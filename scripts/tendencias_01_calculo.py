"""Relevancia y fiabilidad de los trends: casos (casa × origen × EAN × tramo) con todos los trends y lo que pasó.

Uso: python -m scripts.tendencias_01_calculo   → resultados/cache/tendencias_casos.parquet

Qué se mide: el trend que se veía en un origen F (últimos N meses frente a los mismos N del año anterior) ¿anticipa
el crecimiento real del código frente al año anterior en los meses siguientes?

- **Trends:** sell-in (Actuals) y sell-out (EPOS), del propio código, de su Product Line, de su Brand y de la casa
  (House), con N = 3, 6, 9 y 12 meses. 2 señales × 4 niveles × 4 duraciones = 32 trends por caso.
- **Solo Regular Item:** los One Shot quedan fuera de todo (de los casos y de las sumas de los grupos).
- **Sell-in:** la historia de la foto (Actuals; vacío = 0 ventas, el 0 es 0).
- **EPOS:** vacío **o 0** = sin dato. Emparejado por código: un código suma en un mes solo si tiene EPOS > 0 ese mes
  y hace 12 meses (así un retailer que empieza a reportar no parece crecimiento). Un trend de EPOS necesita al menos
  la mitad de los N meses con datos emparejados.
- **Lo que pasó:** actuals de la foto más reciente que trae el código (0 desde que salió del export), comparados con
  los mismos meses del año anterior de esa misma foto. Así el crecimiento real no se contamina con la ruptura de
  perímetro (2026.M02), porque los dos años salen de la misma foto.
- **Dos modos:**
  - `fotos`: cada foto real es un origen y el trend se calcula con lo que traía ese archivo (sin mirar el futuro).
    Las fotos 2025.M09–M12 no traen EPOS: su EPOS (meses anteriores a la foto) se completa con la primera foto
    posterior que lo trae, como hace el motor (`epos_historico_de_foto_mas_reciente`).
  - `historia`: cada mes de la historia de la última foto hace de origen (desde que hay 24 meses detrás). Más casos,
    para medir la fiabilidad.
- **Tramos:** meses 1–3, 4–6 y 7–9 desde el origen; solo los cerrados (≤ mes anterior a la última foto).
"""
from __future__ import annotations

import json
import math
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from motor.lector import int_a_mes, leer_foto

warnings.filterwarnings("ignore", category=RuntimeWarning)

RAIZ = Path(__file__).resolve().parents[1]
CFG = json.loads((RAIZ / "motor" / "config.json").read_text(encoding="utf-8"))
CASAS = [c.name for c in sorted((RAIZ / "data").iterdir()) if c.is_dir() and any(c.glob("Consensus/*.csv"))]
SALIDA = RAIZ / "resultados" / "cache" / "tendencias_casos.parquet"

NS = [3, 6, 9, 12]
NIVELES = ["cod", "pl", "brand", "house"]
SENALES = ["si", "ep"]
TRAMOS = {1: (1, 3), 2: (4, 6), 3: (7, 9)}
REG = "Regular Item"


# ------------------------------------------------------------------ panel "verdad" (lo que pasó)
class Panel:
    """Series de cada código en una rejilla común de meses, cada código desde la foto más reciente que lo trae."""

    def __init__(self, fotos):
        self.fotos = fotos
        ult = fotos[-1]
        self.t0 = min(int(f.meses[0]) for f in fotos)
        self.t1 = ult.mes - 1                                      # último mes cerrado
        self.eans = sorted(set().union(*[f.eans for f in fotos]))
        self.ix = {e: i for i, e in enumerate(self.eans)}
        n, m = len(self.eans), self.t1 - self.t0 + 1
        self.H = np.full((n, m), np.nan)                           # sell-in (historia de la foto)
        self.E = np.full((n, m), np.nan)                           # EPOS (NaN = sin dato)
        self.atr = pd.DataFrame(index=self.eans, columns=["Brand", "Product Line", "House", "Article Type"])
        visto_h, visto_e = np.zeros(n, bool), np.zeros(n, bool)
        for f in reversed(fotos):                                  # de la más reciente a la más antigua
            fila = np.array([self.ix[e] for e in f.eans])
            nuevo = ~visto_h[fila]
            if nuevo.any():
                r = fila[nuevo]
                H = _rejilla(f, f.mat["hist"][nuevo], self.t0, self.t1)
                # desde que salió del export: 0 (el export trae toda la historia; si vendiera, aparecería)
                H[:, f.mes - self.t0:] = 0.0
                self.H[r] = H
                self.atr.loc[[self.eans[i] for i in r]] = f.codigos.loc[[self.eans[i] for i in r],
                                                                          self.atr.columns].to_numpy()
                visto_h[r] = True
            hay_e = ~np.isnan(f.mat["EPOS"]).all(1)
            nuevo_e = ~visto_e[fila] & hay_e
            if nuevo_e.any():
                r = fila[nuevo_e]
                E = _rejilla(f, f.mat["EPOS"][nuevo_e], self.t0, self.t1)
                E[:, f.mes - self.t0:] = np.nan
                self.E[r] = E
                visto_e[r] = True
        self.E[self.E <= 0] = np.nan                               # EPOS 0 = sin dato
        self.inicio = int(min(f.inicio_historia for f in fotos))


def _rejilla(f, M, t0, t1):
    """Matriz de una foto llevada a la rejilla de meses t0…t1."""
    out = np.full((M.shape[0], t1 - t0 + 1), np.nan)
    a, b = max(int(f.meses[0]), t0), min(int(f.meses[-1]), t1)
    out[:, a - t0:b - t0 + 1] = M[:, a - int(f.meses[0]):b - int(f.meses[0]) + 1]
    return out


# ------------------------------------------------------------------ trends en un origen
def _claves(atr: pd.DataFrame) -> dict:
    return {"cod": np.arange(len(atr)).astype(str),
            "pl": (atr["Brand"].astype(str) + "|" + atr["Product Line"].astype(str)).to_numpy(),
            "brand": atr["Brand"].astype(str).to_numpy(),
            "house": np.full(len(atr), "casa")}


def trends(H, E, k, claves, reg) -> dict:
    """Todos los trends en el origen de índice k (meses k−N…k−1 frente a k−N−12…k−13). Solo suman los Regular."""
    out = {}
    for N in NS:
        if k - N - 12 < 0:
            for s in SENALES:
                for nv in NIVELES:
                    out[f"{s}_{nv}_{N}"] = np.full(len(reg), np.nan)
            continue
        rec, ant = slice(k - N, k), slice(k - N - 12, k - 12)
        # sell-in: 0 es 0; sin historia en la ventana (fuera del archivo) = no calculable
        hr, ha = H[:, rec], H[:, ant]
        disp = ~np.isnan(hr).all(1) & ~np.isnan(ha).all(1)
        s1, s0 = np.nansum(hr, 1), np.nansum(ha, 1)
        # EPOS emparejado por código: el mes cuenta si hay EPOS > 0 en t y en t−12
        er, ea = E[:, rec], E[:, ant]
        par = ~np.isnan(er) & ~np.isnan(ea)
        e1, e0 = np.where(par, er, 0).sum(1), np.where(par, ea, 0).sum(1)
        minimo = math.ceil(N / 2)
        for nv in NIVELES:
            cl = claves[nv]
            u, inv = np.unique(cl, return_inverse=True)
            w = reg.astype(float)
            g1 = np.bincount(inv, weights=s1 * w, minlength=len(u))
            g0 = np.bincount(inv, weights=s0 * w, minlength=len(u))
            gd = np.bincount(inv, weights=(disp & reg).astype(float), minlength=len(u)) > 0
            T = np.where(gd[inv] & (g0[inv] > 0), g1[inv] / np.where(g0[inv] > 0, g0[inv], 1) - 1, np.nan)
            if nv == "cod":
                T = np.where(disp, T, np.nan)
            out[f"si_{nv}_{N}"] = T
            p1 = np.bincount(inv, weights=e1 * w, minlength=len(u))
            p0 = np.bincount(inv, weights=e0 * w, minlength=len(u))
            # meses con al menos un par en el grupo
            mes_ok = np.zeros((len(u), N))
            np.add.at(mes_ok, inv, par & reg[:, None])
            nmes = (mes_ok > 0).sum(1)
            T = np.where((nmes[inv] >= minimo) & (p0[inv] > 0), p1[inv] / np.where(p0[inv] > 0, p0[inv], 1) - 1, np.nan)
            out[f"ep_{nv}_{N}"] = T
            if nv == "cod":
                out[f"epcov_{N}"] = par.sum(1) / N
    return out


# ------------------------------------------------------------------ casos
def casos_casa(casa: str) -> pd.DataFrame:
    rutas = sorted((RAIZ / "data" / casa / "Consensus").glob("*.csv"))
    fotos = [leer_foto(r, CFG) for r in rutas]
    P = Panel(fotos)
    filas = []

    def objetivo(idx, F):
        """A y LY de cada tramo cerrado, desde el panel verdad."""
        res = {}
        for tr, (a, b) in TRAMOS.items():
            if F + b > P.t1:
                continue
            ks = np.arange(F + a, F + b + 1) - P.t0
            A = np.nansum(P.H[idx][:, ks], 1)
            LY = np.nansum(P.H[idx][:, ks - 12], 1)
            res[tr] = (A, LY, ks)
        return res

    # --- modo fotos: el trend con lo que traía cada archivo
    for f in fotos:
        F = f.mes
        reg = (f.codigos["Article Type"] == REG).to_numpy()
        H = f.mat["hist"].copy()
        H[:, f.meses >= F] = np.nan
        E = f.mat["EPOS"].copy()
        E[:, f.meses >= F] = np.nan
        epos_completado = np.isnan(E).all()
        if epos_completado:                                        # foto sin EPOS: historia de la primera posterior
            for g in fotos:
                if g.mes > F and not np.isnan(g.mat["EPOS"]).all():
                    pos = {e: i for i, e in enumerate(g.eans)}
                    for i, e in enumerate(f.eans):
                        if e in pos:
                            fila = _rejilla(g, g.mat["EPOS"][[pos[e]]], int(f.meses[0]), int(f.meses[-1]))[0]
                            E[i] = np.where(f.meses < F, fila, np.nan)
                    break
        E[E <= 0] = np.nan
        k = F - int(f.meses[0])
        T = trends(H, E, k, _claves(f.codigos), reg)
        idx = np.array([P.ix[e] for e in f.eans])
        # base de 12 meses desde la foto verdad (mismo perímetro que lo que pasó)
        B12 = np.nansum(P.H[idx][:, F - 12 - P.t0:F - P.t0], 1)
        C = f.mat["Consensus - Final"]
        for tr, (A, LY, ks) in objetivo(idx, F).items():
            a, b = TRAMOS[tr]
            kf = np.arange(F + a, F + b + 1) - int(f.meses[0])
            d = {"casa": casa, "modo": "fotos", "F": F, "ean": f.eans, "tramo": tr, "A": A, "LY": LY,
                 "C": np.nansum(C[:, kf], 1), "LY_F": np.nansum(H[:, kf - 12], 1), "B12": B12,
                 "reg": reg, "epos_completado": epos_completado, "seg": f.codigos["Final Segment"].to_numpy(),
                 "brand": f.codigos["Brand"].to_numpy(), "pl": f.codigos["Product Line"].to_numpy()}
            d.update(T)
            filas.append(pd.DataFrame(d))

    # --- modo historia: cada mes de la última foto hace de origen (24 meses detrás)
    reg = (P.atr["Article Type"] == REG).to_numpy()
    cl = _claves(P.atr)
    todos = np.arange(len(P.eans))
    for F in range(P.inicio + 24, P.t1 - 2):
        k = F - P.t0
        H = P.H.copy()
        H[:, k:] = np.nan
        E = P.E.copy()
        E[:, k:] = np.nan
        T = trends(H, E, k, cl, reg)
        B12 = np.nansum(H[:, k - 12:k], 1)
        for tr, (A, LY, ks) in objetivo(todos, F).items():
            d = {"casa": casa, "modo": "historia", "F": F, "ean": P.eans, "tramo": tr, "A": A, "LY": LY,
                 "C": np.nan, "LY_F": np.nan, "B12": B12, "reg": reg, "epos_completado": False, "seg": "",
                 "brand": P.atr["Brand"].to_numpy(), "pl": P.atr["Product Line"].to_numpy()}
            d.update(T)
            filas.append(pd.DataFrame(d))
    df = pd.concat(filas, ignore_index=True)
    # universo: Regular, con ventas el año anterior en esos meses (sin LY no hay crecimiento que anticipar)
    df = df[df.reg & (df.LY > 0)].drop(columns="reg").reset_index(drop=True)
    print(f"{casa}: {len(fotos)} fotos ({fotos[0].etiqueta}–{fotos[-1].etiqueta}), "
          f"historia hasta {int_a_mes(P.t1)}, {len(df):,} casos")
    return df


def main():
    df = pd.concat([casos_casa(c) for c in CASAS], ignore_index=True)
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(SALIDA, index=False)
    print(f"→ {SALIDA.relative_to(RAIZ)} ({len(df):,} filas)")


if __name__ == "__main__":
    main()
