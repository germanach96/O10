"""Motor de recetas: forecast de cada receta de la rejilla para cada código de una foto.

Una receta = (s, w, m, N, c, p, grupo). Ver CLAUDE.md §4 y §5.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .lector import Foto

AMPLITUDES = ["Propio", "Product Line", "Brand", "House", "Todo"]
CRITERIOS = ["Jerarquía", "Segmento", "Tamaño", "Edad"]
# 17 celdas: "Propio" solo en la fila "Jerarquía"
CELDAS = [(a, c) for c in CRITERIOS for a in AMPLITUDES if not (a == "Propio" and c != "Jerarquía")]
EJES = ["s", "e", "w", "m", "N", "c", "p", "g"]   # e = años de estacionalidad (1 o 2)


class Rejilla:
    """Enumera las recetas de la rejilla gruesa. Índice plano en orden (s, e, w, m, N, c, p, g)."""

    def __init__(self, cfg: dict):
        r = cfg["rejilla_gruesa"]
        self.valores = {k: list(r[k]) for k in ["s", "w", "m", "N", "c", "p"]}
        self.valores["e"] = list(r.get("e", [1]))
        self.valores["g"] = list(range(len(CELDAS)))
        self.forma = tuple(len(self.valores[k]) for k in EJES)
        self.n = int(np.prod(self.forma))
        idx = np.indices(self.forma).reshape(len(EJES), -1)
        self.idx = {k: idx[i] for i, k in enumerate(EJES)}  # índice de valor por eje y receta

    def receta(self, r: int) -> dict:
        d = {k: self.valores[k][self.idx[k][r]] for k in EJES}
        d["grupo"] = "{} · {}".format(*CELDAS[d["g"]])
        return d


def _clave_grupo(cod: pd.DataFrame, amp: str, crit: str) -> np.ndarray:
    n = len(cod)
    if amp == "Propio":
        return np.arange(n).astype(str)
    a = {"Product Line": cod["Product Line"], "Brand": cod["Brand"], "House": cod["House"],
         "Todo": pd.Series([""] * n, index=cod.index)}[amp].astype(str)
    c = {"Jerarquía": pd.Series([""] * n, index=cod.index), "Segmento": cod["Final Segment"],
         "Tamaño": cod["tamano"], "Edad": cod["tramo_edad"]}[crit].astype(str)
    return (a + "|" + c).to_numpy()


class MotorFoto:
    """Precalcula historia limpia, bases y trends de una foto; produce forecasts por receta."""

    def __init__(self, foto: Foto, cfg: dict, rejilla: Rejilla, epos_externo: np.ndarray | None = None,
                 cuenta: np.ndarray | None = None):
        self.foto, self.cfg, self.R = foto, cfg, rejilla
        # códigos que suman en los trends de grupo (filtro general de tipos); None = todos
        self.cuenta = np.ones(len(foto.eans), bool) if cuenta is None else np.asarray(cuenta, bool)
        F = foto.mes
        self.F = F
        hz = cfg["horizonte"]
        self.hz = hz
        meses = foto.meses
        col = lambda t: t - int(meses[0])
        # Ampliar matrices si la foto no cubre el rango necesario
        self.t_hist = np.arange(F - 24 - 12, F)          # suficiente para N=12 + año anterior
        self.t_fut = np.arange(F + 1, F + hz + 1)

        def tomar(M, ts):
            out = np.full((M.shape[0], len(ts)), np.nan)
            for j, t in enumerate(ts):
                k = col(t)
                if 0 <= k < M.shape[1]:
                    out[:, j] = M[:, k]
            return out

        hist = tomar(foto.mat["hist"], self.t_hist)                       # NaN = fuera de la historia
        cuts = np.nan_to_num(tomar(foto.mat["Supply Cuts"], self.t_hist))
        tda_h = np.nan_to_num(tomar(foto.mat["Total Demand Assumption"], self.t_hist))
        self.tda_fut = np.nan_to_num(tomar(foto.mat["Total Demand Assumption"], self.t_fut))
        self.cons_fut = np.nan_to_num(tomar(foto.mat["Consensus - Final"], self.t_fut))
        epos = tomar(foto.mat["EPOS"], self.t_hist)
        if epos_externo is not None:
            epos = np.where(np.isnan(epos), epos_externo, epos)
        self.epos = epos
        self.hist_raw, self.cuts, self.tda_h = hist, cuts, tda_h
        self.disponible = ~np.isnan(hist)                                # mes dentro de la historia útil

        cv, pv = rejilla.valores["c"], rejilla.valores["p"]
        # Historia limpia por (c, p): H = A + c·Cortes − p·TDA      forma (c, p, códigos, meses)
        A = np.nan_to_num(hist)
        self.H = (A[None, None] + np.array(cv)[:, None, None, None] * cuts[None, None]
                  - np.array(pv)[None, :, None, None] * tda_h[None, None])

        self._bases()
        self._trends()

    # ---------- base ----------
    def _bases(self):
        F, nm = self.F, self.cfg["meses_media_base"]
        cod = self.foto.codigos
        th = self.t_hist
        primer = cod["primer_mes_venta"].to_numpy()
        ult = (th >= F - nm) & (th <= F - 1)
        # meses válidos para la media: dentro de la ventana y desde el primer mes de venta
        valido = ult[None, :] & (th[None, :] >= primer[:, None]) & self.disponible
        nval = valido.sum(axis=1)
        self.historia_corta = (primer < 0) | (primer > F - nm)
        Hm = np.where(valido[None, None], self.H, 0.0)
        with np.errstate(invalid="ignore", divide="ignore"):
            self.media = np.where(nval > 0, Hm.sum(-1) / np.maximum(nval, 1), 0.0)   # (c, p, códigos)
        # mismo mes del año anterior (t − 12) para t = F+1..F+hz
        lag_t = self.t_fut - 12
        k = np.searchsorted(th, lag_t)
        lag = self.H[..., k]                                             # (c, p, códigos, hz)
        lag_ok = (lag_t[None, :] >= primer[:, None]) & (primer[:, None] >= 0) & self.disponible[:, k]
        lag1 = np.where(lag_ok[None, None], lag, self.media[..., None])
        # estacionalidad de 2 años: media de t−12 y t−24 en los códigos que tienen los dos; si no, la de 1 año
        lag2_t = self.t_fut - 24
        k2 = np.searchsorted(th, lag2_t)
        ok2 = lag_ok & (lag2_t[None, :] >= primer[:, None]) & self.disponible[:, k2]
        lag2 = np.where(ok2[None, None], (lag + self.H[..., k2]) / 2, lag1)
        # parte estacional por valor del eje e: (e, c, p, códigos, hz)
        self.lag = np.stack([lag2 if e == 2 else lag1 for e in self.R.valores["e"]])
        self.lag_ok, self.lag_2a = lag_ok, ok2

    def base(self, i: int) -> np.ndarray:
        """Base(s, e, c, p, h) del código i."""
        sv = np.array(self.R.valores["s"])[:, None, None, None, None]
        med = self.media[:, :, i][None, None, :, :, None]
        lag = self.lag[:, :, :, i, :][None]
        return (1 - sv) * med + sv * lag

    # ---------- trends ----------
    def _trends(self):
        F = self.F
        cod = self.foto.codigos
        th = self.t_hist
        Nv = self.R.valores["N"]
        n = len(cod)
        nc, npp = self.H.shape[:2]
        tope = self.cfg["tope_trend"]
        # T_sellin / T_sellout por celda, N, (c, p) y código
        self.T_si = np.full((len(CELDAS), len(Nv), nc, npp, n), np.nan)
        self.T_so = np.full((len(CELDAS), len(Nv), n), np.nan)
        self.tam_grupo = np.zeros((len(CELDAS), n), dtype=int)
        self.claves = []
        ep = self.epos
        ep_ok = ~np.isnan(ep)
        fantasma = cod["fantasma"].to_numpy(bool) if "fantasma" in cod else np.zeros(n, bool)
        for gi, (amp, crit) in enumerate(CELDAS):
            clave = _clave_grupo(cod, amp, crit)
            self.claves.append(clave)
            u, inv = np.unique(clave, return_inverse=True)
            # los códigos ignorados por el filtro de tipos no suman en el grupo; los que salieron del export
            # suman en el trend pero no en el nº de códigos
            self.tam_grupo[gi] = np.bincount(inv, weights=self.cuenta & ~fantasma).astype(int)[inv]
            onehot = np.zeros((len(u), n))
            onehot[inv, np.arange(n)] = self.cuenta.astype(float)
            HG = np.einsum("gk,cpkt->cpgt", onehot, self.H)                 # (c, p, grupos, meses)
            dispG = (onehot @ (~self.disponible).astype(float)) == 0       # todos los miembros con historia
            epG = onehot @ np.nan_to_num(ep)                                # EPOS del grupo por mes
            hayG = (onehot @ ep_ok.astype(float)) > 0                       # algún miembro con EPOS ese mes
            for ni, N in enumerate(Nv):
                rec = (th >= F - N) & (th <= F - 1)
                ant = (th >= F - N - 12) & (th <= F - 13)
                num = HG[..., rec].sum(-1)
                den = HG[..., ant].sum(-1)
                ok = dispG[:, ant].all(-1) & dispG[:, rec].all(-1)
                with np.errstate(invalid="ignore", divide="ignore"):
                    T = np.where(ok[None, None] & (den > 0), num / den - 1, np.nan)
                self.T_si[gi, ni] = T[:, :, inv]
                # sell-out: totales del grupo, solo meses con EPOS del grupo en t y en t−12 (sin EPOS hace un año
                # = no se reportaba; sin EPOS en el mes −1 = aún no cargado). Sin emparejar código a código.
                idx_rec = np.where(rec)[0]
                mes_ok = hayG[:, idx_rec] & hayG[:, idx_rec - 12]
                e_num = np.where(mes_ok, epG[:, idx_rec], 0).sum(-1)
                e_den = np.where(mes_ok, epG[:, idx_rec - 12], 0).sum(-1)
                with np.errstate(invalid="ignore", divide="ignore"):
                    To = np.where(e_den > 0, e_num / e_den - 1, np.nan)
                self.T_so[gi, ni] = To[inv]
        self.tope = tope

    def trend(self, i: int):
        """T(m, N, c, p, g) recortado, y máscara de validez."""
        mv = np.array(self.R.valores["m"])
        Tsi = np.moveaxis(self.T_si[:, :, :, :, i], 0, -1)              # (N, c, p, g)
        Tso = np.moveaxis(self.T_so[:, :, i], 0, -1)[:, None, None, :]  # (N, 1, 1, g)
        m = mv[:, None, None, None, None]
        si_ok = ~np.isnan(Tsi)[None] | (m == 1)
        so_ok = ~np.isnan(Tso)[None] | (m == 0)
        T = (1 - m) * np.nan_to_num(Tsi)[None] + m * np.nan_to_num(Tso)[None]
        T = np.clip(T, -self.tope, self.tope)
        ok = si_ok & so_ok
        return T, np.broadcast_to(ok, T.shape)                          # (m, N, c, p, g)

    # ---------- forecast ----------
    def forecasts(self, i: int):
        """Forecast (recetas, hz) y validez (recetas,) del código i."""
        B = self.base(i)                                               # (s, e, c, p, h)
        T, ok = self.trend(i)                                          # (m, N, c, p, g)
        wv = np.array(self.R.valores["w"])
        # forma (s, e, w, m, N, c, p, g, h)
        Fc = (B[:, :, None, None, None, :, :, None, :]
              * (1 + wv[None, None, :, None, None, None, None, None, None] * T[None, None, None, ..., None])
              + self.tda_fut[i])
        Fc = np.maximum(Fc, 0.0)
        valido = ok[None, None, None] | (wv[None, None, :, None, None, None, None, None] == 0)
        valido = np.broadcast_to(valido, self.R.forma)
        return Fc.reshape(self.R.n, self.hz), valido.reshape(-1).copy()

    def desglose(self, i: int, r: int) -> dict:
        """Componentes del forecast de la receta r para el código i (para mostrar en la página)."""
        R = self.R
        ix = {k: R.idx[k][r] for k in EJES}
        s, w, m = R.valores["s"][ix["s"]], R.valores["w"][ix["w"]], R.valores["m"][ix["m"]]
        ci, pi, ni, gi = ix["c"], ix["p"], ix["N"], ix["g"]
        tsi = self.T_si[gi, ni, ci, pi, i]
        tso = self.T_so[gi, ni, i]
        T, ok = self.trend(i)
        Tr = T[ix["m"], ni, ci, pi, gi]
        return {
            "media": float(self.media[ci, pi, i]),
            "lag": [float(x) for x in self.lag[ix["e"], ci, pi, i]],
            "lag_real": [bool(x) for x in self.lag_ok[i]],
            "t_sellin": None if np.isnan(tsi) else float(tsi),
            "t_sellout": None if np.isnan(tso) else float(tso),
            "t_final": float(Tr), "trend_valido": bool(ok[ix["m"], ni, ci, pi, gi]),
            "da": [float(x) for x in self.tda_fut[i]],
            "tam_grupo": int(self.tam_grupo[gi, i]),
        }

    def motivos_invalidez(self, i: int) -> list[str]:
        out = []
        if self.historia_corta[i]:
            out.append("historia corta (<12M): s>0 usa la media")
        for gi, celda in enumerate(CELDAS):
            for ni, N in enumerate(self.R.valores["N"]):
                if np.isnan(self.T_si[gi, ni, 0, 0, i]):
                    out.append(f"trend sell-in no calculable: {celda[0]}·{celda[1]} N={N}")
                if np.isnan(self.T_so[gi, ni, i]):
                    out.append(f"sin EPOS comparable: {celda[0]}·{celda[1]} N={N}")
        return out
