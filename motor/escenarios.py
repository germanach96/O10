"""Escenarios frente al Consensus: probabilidad de que lo vendido se aleje del Consensus de la foto más actual.

Para cada código y foto F se compara el Consensus - Final de F+1…F+3 con lo que se vendió de verdad (sell-in) y se
definen cinco escenarios, cada uno con su propia probabilidad (no suman 100 %):

    bajo       vendido < 0,8 × Consensus           muy_bajo   vendido < 0,5 × Consensus
    alto       vendido > 1,2 × Consensus           muy_alto   vendido > 1,5 × Consensus
    orden      algún mes llega un pedido grande que dobla lo que el Consensus ponía para ese mes

Las probabilidades se aprenden con las fotos pasadas cuyos 3 meses ya cerraron y se aplican a la foto más actual:

1. Panel de la verdad (actuals, cortes y EPOS de la foto más reciente que trae cada código y mes).
2. Armonización de las fotos anteriores a una ruptura de perímetro (factor por código, `ruptura_perimetro`).
3. Indicadores por código y foto con información hasta F−1 (trends de sell-in y sell-out, grupo, pedidos…).
4. Señales binarias legibles (tarjetas) y señales del Consensus frente a la realidad.
5. Por escenario: cribado de señales estables (dos mitades que deben coincidir), logística conjunta, pesos → puntos
   (peso × 10 redondeado) y validación fuera de muestra (por código y de lo antiguo a lo reciente).

La página no calcula: recibe los puntos de cada regla, qué reglas cumple cada código y la recalibración de grupo
(un grupo se mide frente a su Consensus total; ver `calibrar_grupos`).
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from .lector import Foto, int_a_mes, mes_a_int

ESCENARIOS = ("bajo", "muy_bajo", "alto", "muy_alto", "orden")


def _lr(a, b):
    """Variación como log-ratio suavizado: log((a+1)/(b+1))."""
    return np.log((a + 1) / (b + 1))


def _sig(z):
    return 1 / (1 + np.exp(-z))


def _auc(y, p):
    """AUC; None si solo hay una clase."""
    y = np.asarray(y)
    return float(roc_auc_score(y, p)) if 0 < y.mean() < 1 else None


# ------------------------------------------------------------------ 1. panel de la verdad
class Panel:
    """Matrices código × mes (T0…T1, T1 = último mes cerrado de la foto más actual) y forecast de cada foto."""

    def __init__(self, fotos: list[Foto]):
        fotos = sorted(fotos, key=lambda f: f.mes)
        self.fotos = fotos
        reales = [self._reales(f) for f in fotos]
        self.eans = sorted(set().union(*[set(np.asarray(f.eans)[r]) for f, r in zip(fotos, reales)]))
        self.ix = {e: i for i, e in enumerate(self.eans)}
        self.T0 = int(min(f.inicio_historia for f in fotos))
        self.T1 = int(max(f.mes for f in fotos)) - 1
        self.meses = np.arange(self.T0, self.T1 + 1)
        ne, nm = len(self.eans), len(self.meses)
        self.ACT, self.CUT = np.zeros((ne, nm)), np.zeros((ne, nm))
        self.EPOS, self.SRC = np.full((ne, nm), np.nan), np.zeros((ne, nm))
        atr = {}
        # de la foto más antigua a la más reciente: la más reciente que trae el código y el mes gana
        for f, r in zip(fotos, reales):
            filas = np.where(r)[0]
            fi = np.array([self.ix[e] for e in np.asarray(f.eans)[filas]])
            cols = np.where((f.meses >= self.T0) & (f.meses < f.mes))[0]
            tk = (f.meses[cols] - self.T0).astype(int)
            sub = np.ix_(filas, cols)
            dst = np.ix_(fi, tk)
            self.ACT[dst] = np.nan_to_num(f.mat["hist"][sub])
            self.CUT[dst] = np.nan_to_num(f.mat["Supply Cuts"][sub])
            self.SRC[dst] = f.mes
            ep = f.mat["EPOS"][sub]
            cur = self.EPOS[dst]
            self.EPOS[dst] = np.where(np.isnan(ep), cur, ep)
            for e in np.asarray(f.eans)[filas]:
                atr[e] = f.codigos.loc[e]
        self.atr = pd.DataFrame([atr[e] for e in self.eans], index=self.eans)
        vende = self.ACT > 0
        self.primer = np.where(vende.any(1), self.meses[vende.argmax(1)], -1)
        # forecast futuro de cada foto (h = 1…9): Consensus, DA, System FC y flag
        fc = []
        for f, r in zip(fotos, reales):
            cols = np.where((f.meses > f.mes) & (f.meses <= f.mes + 9))[0]
            filas = np.where(r)[0]
            eans = np.asarray(f.eans)[filas]
            d = pd.DataFrame({"foto": f.mes, "ean": np.repeat(eans, len(cols)),
                              "h": np.tile(f.meses[cols] - f.mes, len(filas)).astype(int),
                              "cons": f.mat["Consensus - Final"][np.ix_(filas, cols)].ravel(),
                              "tda": f.mat["Total Demand Assumption"][np.ix_(filas, cols)].ravel()})
            s = f.df[(f.df.t > f.mes) & (f.df.t <= f.mes + 9)]
            s = s.assign(h=(s.t - f.mes).astype(int)).rename(columns={"EAN": "ean"})
            s = s.groupby(["ean", "h"]).agg(sys=("System FC - Final", "sum"),
                                            flag=("Ignore System Forecast Flag", "first")).reset_index()
            fc.append(d.merge(s, on=["ean", "h"], how="left"))
        self.fc = pd.concat(fc, ignore_index=True)
        self.fc[["cons", "tda", "sys"]] = self.fc[["cons", "tda", "sys"]].fillna(0)

    @staticmethod
    def _reales(f: Foto) -> np.ndarray:
        """Filas que vienen en el export (los «fantasmas» de agregar_desaparecidos no cuentan)."""
        if "fantasma" in f.codigos.columns:
            return ~f.codigos["fantasma"].fillna(False).to_numpy(bool)
        return np.ones(len(f.eans), bool)

    def k(self, t):
        return t - self.T0


# ------------------------------------------------------------------ 2. ruptura de perímetro
def perimetro(panel: Panel, ruptura: str | None) -> tuple[dict, dict, set, int]:
    """Factor por código (actuals del perímetro nuevo / viejo en los 24 meses cerrados de la última foto vieja),
    factor por brand de respaldo y códigos que casi solo existen en el perímetro nuevo. Devuelve también el último
    mes de foto del perímetro viejo (las fotos <= ese mes se armonizan). Sin ruptura: factores vacíos."""
    if not ruptura:
        return {}, {}, set(), -1
    b = mes_a_int(ruptura)
    viejas = [f for f in panel.fotos if f.mes < b]
    nuevas = [f for f in panel.fotos if f.mes >= b]
    if not viejas or not nuevas:
        return {}, {}, set(), -1
    ref, nuevo = viejas[-1], nuevas[0]
    ventana = lambda f: (f.meses >= ref.mes - 24) & (f.meses <= ref.mes - 1)  # noqa: E731
    so = dict(zip(ref.eans, np.nansum(ref.mat["Actuals"][:, ventana(ref)], 1)))
    sn = dict(zip(nuevo.eans, np.nansum(nuevo.mat["Actuals"][:, ventana(nuevo)], 1)))
    brand = pd.concat([ref.codigos["Brand"], nuevo.codigos["Brand"]])
    brand = brand[~brand.index.duplicated()]
    kb = {}
    for g in brand.unique():
        es = [e for e in brand.index[brand == g] if e in so and e in sn]
        o, n = sum(so[e] for e in es), sum(sn[e] for e in es)
        kb[g] = n / o if o > 0 else 1.0
    k = {}
    for e in set(so) | set(sn):
        o, n = so.get(e, 0), sn.get(e, np.nan)
        if np.isnan(n):
            k[e] = kb.get(brand.get(e), 1.0)                 # salió del export: factor de su brand
        elif o >= 50:
            k[e] = float(np.clip(n / o, 0.5, 5))
        else:
            k[e] = kb.get(brand.get(e), 1.0)
    solo_nuevo = {e for e in sn if so.get(e, 0) < 0.1 * sn[e] and sn[e] >= 100}
    return k, kb, solo_nuevo, ref.mes


# ------------------------------------------------------------------ 3. indicadores por código y foto
def _gsum(M, keys, mask=None):
    """Suma por grupo (cada código recibe el total de su grupo)."""
    out = np.zeros_like(M)
    M0 = np.nan_to_num(M) if mask is None else np.where(mask[:, None], np.nan_to_num(M), 0)
    for g in pd.unique(keys):
        idx = keys == g
        out[idx] = M0[idx].sum(0)
    return out


def indicadores(panel: Panel, k: dict, kb: dict, vieja: int) -> tuple[pd.DataFrame, np.ndarray]:
    """Una fila por código y foto (solo con información hasta F−1). Devuelve también SI (sell-in armonizado)."""
    A = panel.atr
    brand, pl = A["Brand"].to_numpy(), A["Product Line"].to_numpy()
    os_ = A["Article Type"].ne("Regular Item").to_numpy()
    reg = ~os_
    kk = np.array([k.get(e, kb.get(brand[i], 1.0)) for i, e in enumerate(panel.eans)])[:, None]
    viejo = panel.SRC <= vieja
    SI = np.where(viejo, panel.ACT * kk, panel.ACT)
    CU = np.where(viejo, panel.CUT * kk, panel.CUT)
    EP = panel.EPOS
    ne, nm = SI.shape
    ml = A["tamano"].astype(str).str.extract(r"^([\d.]+)")[0].astype(float).to_numpy()
    disco = A["disco_mes"].to_numpy(float)
    menos = lambda M: np.where(reg[:, None], M, 0)  # noqa: E731  (el propio código no cuenta en su grupo)
    SI_pl, SI_br = _gsum(SI, pl, reg) - menos(SI), _gsum(SI, brand, reg) - menos(SI)
    SI_ho = np.nansum(menos(SI), 0)[None, :] - menos(SI)
    EPz = np.nan_to_num(EP)
    EP_pl, EP_br = _gsum(EPz, pl, reg) - menos(EPz), _gsum(EPz, brand, reg) - menos(EPz)
    EP_ho = EPz[reg].sum(0)[None, :] - menos(EPz)
    OS_br = _gsum(SI, brand, os_)
    REG_pl, REG_br = _gsum(SI, pl, reg), _gsum(SI, brand, reg)
    EP_ok = ~np.isnan(EP).all(0)
    primer = panel.primer
    LAN = np.zeros_like(SI)
    for i in np.where(reg & (primer >= panel.T0 + 1))[0]:
        LAN[i, panel.k(primer[i])] = 1
    LAN_pl, LAN_br = _gsum(LAN, pl), _gsum(LAN, brand)
    kf = panel.k

    def w(M, a, b):   # suma de los meses [a, b]; NaN si la ventana sale del panel
        if kf(a) < 0 or kf(b) >= nm:
            return np.full(M.shape[0], np.nan)
        return M[:, kf(a):kf(b) + 1].sum(1)

    def wn(M, a, b):  # igual, NaN si falta algún mes (EPOS)
        if kf(a) < 0 or kf(b) >= nm:
            return np.full(M.shape[0], np.nan)
        X = M[:, kf(a):kf(b) + 1]
        return np.where(np.isnan(X).any(1), np.nan, np.nansum(X, 1))

    L = _lr
    filas = []
    for F in sorted({f.mes for f in panel.fotos}):
        if F < panel.T0 + 15 or F > panel.T1 + 1:   # el trend interanual de 3 meses necesita 15 meses
            continue
        d = {"F": np.full(ne, F), "ean": np.array(panel.eans)}
        s1, s3, s6, s12 = SI[:, kf(F - 1)], w(SI, F - 3, F - 1), w(SI, F - 6, F - 1), w(SI, F - 12, F - 1)
        s3l, s6l, s12l = w(SI, F - 15, F - 13), w(SI, F - 18, F - 13), w(SI, F - 24, F - 13)
        X12 = SI[:, kf(F - 12):kf(F)]
        mu = X12.mean(1)
        d.update(s_yoy3=L(s3, s3l), s_yoy6=L(s6, s6l), s_yoy12=L(s12, s12l))
        d["s_cv12"] = X12.std(1) / np.maximum(X12.mean(1), 1e-9)
        d["s_zeros12"] = (X12 <= 0).sum(1)
        r3 = np.array([X12[:, j:j + 3].sum(1) for j in range(10)]).T
        d["s_dd"] = s3 / np.maximum(r3.max(1), 1)
        yo = np.array([L(SI[:, kf(F - j)], SI[:, kf(F - 12 - j)]) if kf(F - 12 - j) >= 0 else np.full(ne, np.nan)
                       for j in range(1, 7)]).T
        d["s_up6"] = np.where(np.isnan(yo).any(1), np.nan, (yo > 0).mean(1))
        d["s_last_avg"] = s1 / np.maximum(s12 / 12, 1e-9)
        thr = np.maximum(2 * np.median(X12, 1), 1.5 * mu)
        big = X12 >= thr[:, None]
        ult = np.array([np.where(b)[0].max() if b.any() else -1 for b in big])
        d["s_ms_big"] = np.where(big.any(1), 12 - ult, 13)
        d["n_big12"] = big.sum(1)
        d["s12"] = np.expm1(np.log1p(s12))
        e3, e6, e12 = wn(EP, F - 3, F - 1), wn(EP, F - 6, F - 1), wn(EP, F - 12, F - 1)
        e3l, e6l = wn(EP, F - 15, F - 13), wn(EP, F - 18, F - 13)
        d.update(e_yoy3=L(e3, e3l), e_yoy6=L(e6, e6l))
        d["e_acc"] = d["e_yoy3"] - d["e_yoy6"]
        kap = e12 / np.maximum(s12, 1)
        kap = np.where(kap > 0, kap, np.nan)
        d["st3"] = (e3 / np.maximum(s3, 1)) / kap
        d["stock6"] = (s6 - e6 / kap) / np.maximum(s12 / 12, 1)
        d["div3"] = d["s_yoy3"] - d["e_yoy3"]
        for nom, G, E_ in (("pl", SI_pl, EP_pl), ("br", SI_br, EP_br), ("ho", SI_ho, EP_ho)):
            d[f"{nom}_s_yoy3"] = L(w(G, F - 3, F - 1), w(G, F - 15, F - 13))
            ok3 = (kf(F - 15) >= 0 and EP_ok[kf(F - 15)] and EP_ok[kf(F - 1)]
                   and EP_ok[kf(F - 3)] and EP_ok[kf(F - 13)])
            d[f"{nom}_e_yoy3"] = L(w(E_, F - 3, F - 1), w(E_, F - 15, F - 13)) if ok3 else np.full(ne, np.nan)
            d[f"rs_{nom}"] = d["s_yoy3"] - d[f"{nom}_s_yoy3"]
            d[f"rs_{nom}_e"] = d["e_yoy3"] - d[f"{nom}_e_yoy3"]
        d["pl_share_chg"] = L(s3, w(REG_pl, F - 3, F - 1)) - L(s12, w(REG_pl, F - 12, F - 1))
        nuevo6 = np.where(reg & (primer >= F - 6) & (primer <= F - 1), 1, 0)
        d["lan_pl_6"] = w(LAN_pl, F - 6, F - 1) - nuevo6
        d["lan_br_6"] = w(LAN_br, F - 6, F - 1) - nuevo6
        d["os_br3"] = w(OS_br, F - 3, F - 1) / np.maximum(w(REG_br, F - 3, F - 1), 1)
        d["os_br_yoy3"] = L(w(OS_br, F - 3, F - 1), w(OS_br, F - 15, F - 13))
        d["cut3"] = w(CU, F - 3, F - 1) / np.maximum(s12 / 12, 1)
        d["edad"] = np.where(primer > 0, F - primer, np.nan)
        d["meses_a_disco"] = disco - F
        d["ml"] = ml
        d["os"] = os_.astype(float)
        d["mes_obj"] = (F + 1) % 12 + 1          # mes natural del primer mes objetivo
        d["y3_ly"] = w(SI, F - 11, F - 9)       # lo vendido en esos mismos 3 meses del año pasado
        d["ly_next3"] = d["y3_ly"] / np.maximum(3 * mu, 1e-9)
        d["last3_vs_rate"] = s3 / np.maximum(3 * mu, 1e-9)
        E12 = EP[:, kf(F - 12):kf(F)]
        with warnings.catch_warnings():   # códigos sin ningún mes de EPOS: NaN
            warnings.simplefilter("ignore", RuntimeWarning)
            d["e_last3_vs_rate"] = e3 / np.maximum(3 * np.nanmean(E12, 1), 1e-9)
        d["mu12"], d["thr_big"] = mu, thr
        # pedido grande en estos mismos 3 meses del año pasado (sell-in sin armonizar, como el objetivo)
        ly = np.zeros(ne, bool)
        for h in (1, 2, 3):
            if kf(F + h - 12) >= 0:
                ly |= panel.ACT[:, kf(F + h - 12)] >= thr
        d["ly_big3"] = ly
        filas.append(pd.DataFrame(d))
    Z = pd.concat(filas, ignore_index=True)
    Z["seg"] = Z.ean.map(A["Final Segment"])
    return Z, SI


# ------------------------------------------------------------------ 4. señales (tarjetas)
# (id, familia, texto en la página, usa EPOS, función de la tabla P -> máscara, indicadores que la explican)
FAM = {"si": "Sell-in trend", "so": "Sell-out trend", "x": "Sell-in vs sell-out", "g": "Code vs group",
       "c": "Orders & calendar", "o": "Supply & portfolio", "k": "Consensus vs reality"}


def senales(P: pd.DataFrame) -> list[dict]:
    L = np.log
    si3, si12, ep3 = P.s_yoy3, P.s_yoy12, P.e_yoy3
    ho3, br3, pl3 = P.ho_s_yoy3, P.br_s_yoy3, P.pl_s_yoy3
    up, dn, UP, DN = L(1.1), L(0.9), L(1.3), L(0.7)
    ritmo3 = P.s12 / 4
    cg = L((P.c3 + 1) / (P.y3_ly + 1))         # crecimiento interanual que asume el Consensus
    cm = P[["c1", "c2", "c3m"]]
    vend3 = P.last3_vs_rate * 3 * P.mu12
    S = []

    def add(sid, fam, txt, mask, epos=False, ver=()):
        S.append(dict(id=sid, fam=fam, txt=txt, epos=epos, ver=list(ver),
                      mask=pd.Series(mask, index=P.index).fillna(False).astype(bool)))

    # 1. trend de sell-in del código
    add("SI_up3", "si", "Sell-in last 3 months above +10% vs last year", si3 > up, ver=["s_yoy3"])
    add("SI_UP3", "si", "Sell-in last 3 months above +30% vs last year", si3 > UP, ver=["s_yoy3"])
    add("SI_dn3", "si", "Sell-in last 3 months below −10% vs last year", si3 < dn, ver=["s_yoy3"])
    add("SI_DN3", "si", "Sell-in last 3 months below −30% vs last year", si3 < DN, ver=["s_yoy3"])
    add("SI_dn12", "si", "Sell-in last 12 months below −10% vs the year before", si12 < dn, ver=["s_yoy12"])
    add("SI_up12", "si", "Sell-in last 12 months above +10% vs the year before", si12 > up, ver=["s_yoy12"])
    add("SI_acel", "si", "Speeding up: 3-month trend 20 points better than 12-month", (si3 - si12) > L(1.2), ver=["s_yoy3", "s_yoy12"])
    add("SI_frena", "si", "Slowing down: 3-month trend 20 points worse than 12-month", (si3 - si12) < L(.8), ver=["s_yoy3", "s_yoy12"])
    add("SI_giro_up", "si", "Turning up: 12 months negative but last 3 positive", (si12 < dn) & (si3 > up), ver=["s_yoy12", "s_yoy3"])
    add("SI_giro_dn", "si", "Turning down: 12 months positive but last 3 negative", (si12 > up) & (si3 < dn), ver=["s_yoy12", "s_yoy3"])
    add("SI_racha_up", "si", "Streak: 5 or 6 of the last 6 months above last year", P.s_up6 >= 5 / 6 - 1e-9, ver=["s_up6"])
    add("SI_racha_dn", "si", "Streak: none of the last 6 months above last year", P.s_up6 <= 0, ver=["s_up6"])
    add("SI_last_hi", "si", "Last month above 1.5× its 12-month average", P.s_last_avg > 1.5, ver=["s_last_avg"])
    add("SI_last_lo", "si", "Last month below 0.3× its 12-month average", P.s_last_avg < .3, ver=["s_last_avg"])
    add("SI_3m_hi", "si", "Last 3 months above 1.3× its 12-month pace", P.last3_vs_rate > 1.3, ver=["last3_vs_rate"])
    add("SI_3m_lo", "si", "Last 3 months below 0.6× its 12-month pace", P.last3_vs_rate < .6, ver=["last3_vs_rate"])
    add("SI_max", "si", "At a high: last 3 months at 90% or more of its best quarter of the year", P.s_dd >= .9, ver=["s_dd"])
    add("SI_suelo", "si", "At a low: last 3 months under 25% of its best quarter of the year", P.s_dd < .25, ver=["s_dd"])
    # 2. trend de sell-out (EPOS)
    add("EP_up3", "so", "EPOS last 3 months above +10% vs last year", ep3 > up, True, ["e_yoy3"])
    add("EP_dn3", "so", "EPOS last 3 months below −10% vs last year", ep3 < dn, True, ["e_yoy3"])
    add("EP_DN3", "so", "EPOS last 3 months below −30% vs last year", ep3 < DN, True, ["e_yoy3"])
    add("EP_acel", "so", "EPOS speeding up: 3-month trend 15 points better than 6-month", P.e_acc > L(1.15), True, ["e_yoy3", "e_yoy6"])
    add("EP_frena", "so", "EPOS slowing down: 3-month trend 15 points worse than 6-month", P.e_acc < L(.85), True, ["e_yoy3", "e_yoy6"])
    add("EP_last_hi", "so", "EPOS last 3 months above 1.2× its 12-month average", P.e_last3_vs_rate > 1.2, True, ["e_last3_vs_rate"])
    add("EP_last_lo", "so", "EPOS last 3 months below 0.7× its 12-month average", P.e_last3_vs_rate < .7, True, ["e_last3_vs_rate"])
    # 3. sell-in frente a sell-out
    add("X_si_dn_ep_up", "x", "Sell-in falls (below −10%) while EPOS grows (above +10%): the retailer ran short", (si3 < dn) & (ep3 > up), True, ["s_yoy3", "e_yoy3"])
    add("X_si_up_ep_dn", "x", "Sell-in grows (above +10%) while EPOS falls (below −10%): the retailer is loading up", (si3 > up) & (ep3 < dn), True, ["s_yoy3", "e_yoy3"])
    add("X_ambos_up", "x", "Sell-in and EPOS both grow (above +10%)", (si3 > up) & (ep3 > up), True, ["s_yoy3", "e_yoy3"])
    add("X_ambos_dn", "x", "Sell-in and EPOS both fall (below −10%)", (si3 < dn) & (ep3 < dn), True, ["s_yoy3", "e_yoy3"])
    add("X_ambos_DN", "x", "Sell-in and EPOS both collapse (below −30%)", (si3 < DN) & (ep3 < DN), True, ["s_yoy3", "e_yoy3"])
    add("X_div_pos", "x", "Sell-in runs 30 points above EPOS (3-month trend)", P.div3 > L(1.3), True, ["s_yoy3", "e_yoy3"])
    add("X_div_neg", "x", "Sell-in runs 30 points below EPOS (3-month trend)", P.div3 < L(.7), True, ["s_yoy3", "e_yoy3"])
    add("X_st_alto", "x", "The retailer sells more than it buys: 3-month sell-through above 1.3× normal", P.st3 > 1.3, True, ["st3"])
    add("X_st_bajo", "x", "The retailer buys more than it sells: 3-month sell-through below 0.7× normal", P.st3 < .7, True, ["st3"])
    add("X_stock_alto", "x", "Loaded channel: over 1 month of sales too much came in over 6 months", P.stock6 > 1, True, ["stock6"])
    add("X_stock_bajo", "x", "Empty channel: over 1 month of sales too little came in over 6 months", P.stock6 < -1, True, ["stock6"])
    # 4. código frente a su grupo
    add("G_casa_dn", "g", "The house falls (regular sell-in below −10% over 3 months)", ho3 < dn, ver=["ho_s_yoy3"])
    add("G_casa_up", "g", "The house grows (regular sell-in above +10% over 3 months)", ho3 > up, ver=["ho_s_yoy3"])
    add("G_brand_dn", "g", "Its brand falls (below −10% over 3 months)", br3 < dn, ver=["br_s_yoy3"])
    add("G_brand_DN", "g", "Its brand collapses (below −30% over 3 months)", br3 < DN, ver=["br_s_yoy3"])
    add("G_brand_up", "g", "Its brand grows (above +10% over 3 months)", br3 > up, ver=["br_s_yoy3"])
    add("G_linea_dn", "g", "Its line falls (below −10% over 3 months)", pl3 < dn, ver=["pl_s_yoy3"])
    add("G_linea_DN", "g", "Its line collapses (below −30% over 3 months)", pl3 < DN, ver=["pl_s_yoy3"])
    add("G_linea_up", "g", "Its line grows (above +10% over 3 months)", pl3 > up, ver=["pl_s_yoy3"])
    add("G_contra_casa", "g", "Against the tide: the code grows (above +10%) while the house falls (below −10%)", (si3 > up) & (ho3 < dn), ver=["s_yoy3", "ho_s_yoy3"])
    add("G_contra_brand", "g", "Against the tide: the code grows (above +10%) while its brand falls (below −10%)", (si3 > up) & (br3 < dn), ver=["s_yoy3", "br_s_yoy3"])
    add("G_contra_linea", "g", "Against the tide: the code grows (above +10%) while its line falls (below −10%)", (si3 > up) & (pl3 < dn), ver=["s_yoy3", "pl_s_yoy3"])
    add("G_rezagado", "g", "Lagging: the code falls (below −10%) while its brand grows (above +10%)", (si3 < dn) & (br3 > up), ver=["s_yoy3", "br_s_yoy3"])
    add("G_rs_brand_hi", "g", "Doing much better than its brand (trend 2× better)", P.rs_br > L(2), ver=["s_yoy3", "br_s_yoy3"])
    add("G_rs_brand_lo", "g", "Doing much worse than its brand (half the trend)", P.rs_br < L(.5), ver=["s_yoy3", "br_s_yoy3"])
    add("G_rs_linea_hi", "g", "Doing much better than its line (trend 2× better)", P.rs_pl > L(2), ver=["s_yoy3", "pl_s_yoy3"])
    add("G_rs_linea_lo", "g", "Doing much worse than its line (half the trend)", P.rs_pl < L(.5), ver=["s_yoy3", "pl_s_yoy3"])
    add("G_cuota_up", "g", "Gaining share in its line (3-month share above 1.2× the 12-month share)", P.pl_share_chg > L(1.2), ver=["pl_share_chg"])
    add("G_cuota_dn", "g", "Losing share in its line (3-month share below 0.8× the 12-month share)", P.pl_share_chg < L(.8), ver=["pl_share_chg"])
    add("G_ep_brand_hi", "g", "Its EPOS does better than its brand's EPOS (by 20 points)", P.rs_br_e > L(1.2), True, ["e_yoy3", "br_e_yoy3"])
    add("G_ep_brand_lo", "g", "Its EPOS does worse than its brand's EPOS (by 20 points)", P.rs_br_e < L(.8), True, ["e_yoy3", "br_e_yoy3"])
    add("G_casa_ep_dn", "g", "House EPOS falls (below −10%)", P.ho_e_yoy3 < dn, True, ["ho_e_yoy3"])
    add("G_brand_ep_up", "g", "Its brand's EPOS grows (above +10%)", P.br_e_yoy3 > up, True, ["br_e_yoy3"])
    add("G_brand_ep_dn", "g", "Its brand's EPOS falls (below −10%)", P.br_e_yoy3 < dn, True, ["br_e_yoy3"])
    add("G_brand_destock", "g", "Its brand is destocking: brand sell-in 20 points below its EPOS", (br3 - P.br_e_yoy3) < L(.8), True, ["br_s_yoy3", "br_e_yoy3"])
    # 5. ciclo de pedidos y calendario
    add("C_ly_big3", "c", "Last year it had a large order in these same 3 months", P.ly_big3, ver=[])
    add("C_ly_pico", "c", "Last year these 3 months were its high season (above 1.3× its average)", P.ly_next3 > 1.3, ver=["ly_next3"])
    add("C_ly_valle", "c", "Last year these 3 months were its low season (below 0.7× its average)", P.ly_next3 < .7, ver=["ly_next3"])
    add("C_big_reciente", "c", "Placed a large order in the last 2 months", P.s_ms_big <= 2, ver=["s_ms_big"])
    add("C_big_lejos", "c", "9 months or more without a large order (but it had one)", P.s_ms_big.between(9, 12), ver=["s_ms_big"])
    add("C_sin_big", "c", "No large order in 12 months", P.n_big12 == 0, ver=["n_big12"])
    add("C_muchos_big", "c", "3 or more large orders in 12 months", P.n_big12 >= 3, ver=["n_big12"])
    add("C_errático", "c", "Erratic: months very different from each other (CV 1 or more)", P.s_cv12 >= 1, ver=["s_cv12"])
    add("C_regular", "c", "Steady: months similar to each other (CV under 0.5)", P.s_cv12 < .5, ver=["s_cv12"])
    add("C_ceros", "c", "2 or more months at zero in the last year", P.s_zeros12 >= 2, ver=["s_zeros12"])
    add("C_q4", "c", "The next 3 months include September or October (Q4 load)", P.mes_obj.isin([8, 9, 10]), ver=[])
    add("C_post_navidad", "c", "The next 3 months start in January or February", P.mes_obj.isin([1, 2]), ver=[])
    # 6. supply, lanzamientos, One Shots y ciclo de vida
    add("O_cortes", "o", "Supply cuts in the last 3 months (over 0.5 months of sales)", P.cut3 > .5, ver=["cut3"])
    add("O_cortes_altos", "o", "Heavy cuts in the last 3 months (over 2 months of sales)", P.cut3 > 2, ver=["cut3"])
    add("O_lanz_brand", "o", "Its brand launched 3 or more regulars in the last 6 months", P.lan_br_6 >= 3, ver=["lan_br_6"])
    add("O_lanz_linea", "o", "Its line launched a regular in the last 6 months", P.lan_pl_6 >= 1, ver=["lan_pl_6"])
    add("O_os_campaña", "o", "One Shot campaign in its brand (50% or more of regular sell-in over 3 months)", P.os_br3 >= .5, ver=["os_br3"])
    add("O_os_crece", "o", "One Shots in its brand more than double vs last year", P.os_br_yoy3 > L(2), ver=["os_br_yoy3"])
    add("O_grande_ml", "o", "Large size (150 ml or more)", P.ml >= 150, ver=["ml"])
    add("O_mini", "o", "Mini size (10 ml or less)", P.ml <= 10, ver=["ml"])
    add("O_pequeño", "o", "Small code (under 4,000 units a year)", P.s12 < 4000, ver=["s12"])
    add("O_grande_vol", "o", "Large code (over 30,000 units a year)", P.s12 > 30000, ver=["s12"])
    add("O_joven", "o", "Young: 13 to 24 months since its first sale", P.edad <= 24, ver=["edad"])
    for seg in ("Bulls", "Horses", "Rabbits", "Post NPI", "DISC"):
        add(f"O_seg_{seg.replace(' ', '')}", "o", f"Segment {seg}", P.seg == seg, ver=[])
    add("O_disco", "o", "Discontinuation date within the next 12 months", P.meses_a_disco.between(0, 12), ver=["meses_a_disco"])
    # 7. el Consensus frente a la realidad
    add("K_ritmo_hi", "k", "The 3-month Consensus is over 1.5× its pace of the last 12 months", P.c3 > 1.5 * ritmo3, ver=["k_ritmo"])
    add("K_ritmo_HI", "k", "The 3-month Consensus is over 2.5× its pace of the last 12 months", P.c3 > 2.5 * ritmo3, ver=["k_ritmo"])
    add("K_ritmo_lo", "k", "The 3-month Consensus is under 0.67× its pace of the last 12 months", P.c3 < .67 * ritmo3, ver=["k_ritmo"])
    add("K_ritmo_LO", "k", "The 3-month Consensus is under 0.4× its pace of the last 12 months", P.c3 < .4 * ritmo3, ver=["k_ritmo"])
    add("K_3m_hi", "k", "The 3-month Consensus is over 1.5× what sold in the last 3 months", P.c3 > 1.5 * vend3, ver=["k_3m"])
    add("K_3m_lo", "k", "The 3-month Consensus is under 0.67× what sold in the last 3 months", P.c3 < .67 * vend3, ver=["k_3m"])
    add("K_ly_hi", "k", "The Consensus is over 1.5× what sold in the same months last year", P.c3 > 1.5 * P.y3_ly, ver=["k_ly"])
    add("K_ly_lo", "k", "The Consensus is under 0.67× what sold in the same months last year", P.c3 < .67 * P.y3_ly, ver=["k_ly"])
    add("K_si_hi", "k", "The Consensus assumes growth 50 points above the 3-month sell-in trend", (cg - si3) > L(1.5), ver=["k_cg", "s_yoy3"])
    add("K_si_lo", "k", "The Consensus assumes growth 20 points below the 3-month sell-in trend", (cg - si3) < L(.8), ver=["k_cg", "s_yoy3"])
    add("K_ep_hi", "k", "The Consensus assumes growth 50 points above the EPOS trend", (cg - ep3) > L(1.5), True, ["k_cg", "e_yoy3"])
    add("K_ep_lo", "k", "The Consensus assumes growth 20 points below the EPOS trend", (cg - ep3) < L(.8), True, ["k_cg", "e_yoy3"])
    add("K_da_alto", "k", "DA is over 40% of the next 3 months' Consensus", P.da3 > .4 * P.c3, ver=["k_da"])
    add("K_da_neg", "k", "Negative DA in the next 3 months (over 5% of the Consensus)", P.da3 < -.05 * P.c3, ver=["k_da"])
    add("K_frontal", "k", "Front-loaded Consensus: months 7–9 under 0.5× months 1–3", P.c79 < .5 * P.c3, ver=["k_79"])
    add("K_tardio", "k", "The Consensus expects a late recovery: months 7–9 over 2× months 1–3", P.c79 > 2 * P.c3, ver=["k_79"])
    add("K_rev_up", "k", "The Consensus for these months rose over 30% vs 3 snapshots ago", P.c3 > 1.3 * P.c3_prev3, ver=["k_rev"])
    add("K_rev_dn", "k", "The Consensus for these months fell over 30% vs 3 snapshots ago", P.c3 < .7 * P.c3_prev3, ver=["k_rev"])
    add("K_man_up", "k", "Manual adjustment up: Consensus over 1.2× System FC + DA", P.c3 > 1.2 * (P.sys3 + P.da3.clip(lower=0)), ver=["k_man"])
    add("K_man_dn", "k", "Manual adjustment down: Consensus under 0.8× System FC + DA", P.c3 < .8 * (P.sys3 + P.da3.clip(lower=0)), ver=["k_man"])
    add("K_flag", "k", "System FC does not flow (Ignore System Forecast Flag 1 or 2)", P.flag.isin(["1", "2"]), ver=[])
    add("K_plano", "k", "Flat Consensus: the 3 months nearly equal (under 10% variation)", (cm.std(axis=1) / cm.mean(axis=1).clip(lower=1)) < .1, ver=[])
    add("K_pico_plan", "k", "The Consensus already plans a large-order month (2× its median or more)", cm.max(axis=1) >= P.thr_big, ver=[])
    add("K_ultimo_cero", "k", "Last month came in near zero but the Consensus is over 0.8× its pace", (P.s_last_avg < .15) & (P.c3 > .8 * ritmo3), ver=["s_last_avg", "k_ritmo"])
    return S


# ------------------------------------------------------------------ tabla de casos (código × foto) con objetivos
def casos(panel: Panel, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame, list[dict], dict]:
    ce = cfg["escenarios"]
    k, kb, solo_nuevo, vieja = perimetro(panel, ce.get("ruptura_perimetro"))
    Z, _ = indicadores(panel, k, kb, vieja)
    mn = ce["minimos"]
    P = Z[(Z.os == 0) & (Z.s12 >= mn["vol12"]) & (Z.edad >= mn["edad_meses"])].copy().reset_index(drop=True)
    # Consensus de cada foto (armonizado en las fotos del perímetro viejo)
    fc = panel.fc.copy()
    kc = np.where(fc.foto <= vieja, fc.ean.map(k).fillna(1.0), 1.0)
    for c in ("cons", "tda", "sys"):
        fc[c] = fc[c] * kc
    piv = fc.pivot_table(index=["foto", "ean"], columns="h", values="cons", aggfunc="sum").fillna(0)
    G = pd.DataFrame({"c1": piv[1], "c2": piv[2], "c3m": piv[3]})
    G["c3"] = G.c1 + G.c2 + G.c3m
    G["c46"], G["c79"] = piv[[4, 5, 6]].sum(axis=1), piv[[7, 8, 9]].sum(axis=1)
    a = fc[fc.h.between(1, 3)].groupby(["foto", "ean"])
    G["da3"], G["sys3"], G["flag"] = a.tda.sum(), a.sys.sum(), a.flag.first()
    G = G.reset_index()
    p = fc[["foto", "ean", "h", "cons"]].copy()
    for lag in (1, 3):   # los mismos meses en la foto de hace 1 y 3 meses
        q = p[(p.h > lag) & (p.h <= lag + 3)].assign(F=lambda x: x.foto + lag)
        q = q.groupby(["F", "ean"]).cons.sum().rename(f"c3_prev{lag}").reset_index().rename(columns={"F": "foto"})
        G = G.merge(q, on=["foto", "ean"], how="left")
    G = G.rename(columns={"foto": "F"})
    P = P.merge(G, on=["F", "ean"], how="inner")
    P = P[(P.c3 >= mn["consensus_3m"]) & ~(P.ean.isin(solo_nuevo) & (P.F <= vieja))].reset_index(drop=True)
    # objetivos: lo vendido en F+1…F+3 frente al Consensus de la foto
    i = P.ean.map(panel.ix).to_numpy()
    f = P.F.to_numpy()
    A = np.full((len(P), 3), np.nan)
    for h in (1, 2, 3):
        t = f + h - panel.T0
        ok = t <= panel.T1 - panel.T0
        A[ok, h - 1] = panel.ACT[i[ok], t[ok]]
    u = ce["umbrales"]
    P["A3"] = A.sum(1)
    P["cerrado"] = ~np.isnan(A).any(1)
    r = P.A3 / P.c3
    P["Y_bajo"], P["Y_muy_bajo"] = (r < u["bajo"]).astype(int), (r < u["muy_bajo"]).astype(int)
    P["Y_alto"], P["Y_muy_alto"] = (r > u["alto"]).astype(int), (r > u["muy_alto"]).astype(int)
    Cm = P[["c1", "c2", "c3m"]].to_numpy()
    P["Y_orden"] = ((A >= P.thr_big.to_numpy()[:, None]) & (A > u["orden"] * Cm)).any(1).astype(int)
    P["ratio"] = r
    S = senales(P)
    X = pd.DataFrame({s["id"]: s["mask"].astype(int).to_numpy() for s in S})
    # códigos de la foto más actual que no se puntúan, con el motivo
    ult = panel.fotos[-1]
    zu = Z[Z.F == ult.mes].set_index("ean")
    gu = G[G.F == ult.mes].set_index("ean").c3
    fuera = {}
    for e in np.asarray(ult.eans)[Panel._reales(ult)]:
        if e not in zu.index:
            continue
        z = zu.loc[e]
        c3 = round(float(gu.get(e, 0)), 1)     # Consensus de 3 meses: la página calcula qué parte del grupo se puntúa
        if z.os:
            fuera[e] = ["os", c3]
        elif not z.s12 >= mn["vol12"]:
            fuera[e] = ["vol", c3]
        elif not z.edad >= mn["edad_meses"]:
            fuera[e] = ["edad", c3]
        elif not c3 >= mn["consensus_3m"]:
            fuera[e] = ["cons", c3]
    info = {"k": k, "kb": kb, "solo_nuevo": sorted(solo_nuevo), "vieja": vieja, "fuera": fuera}
    return P, X, S, info


# ------------------------------------------------------------------ 5. pesos por escenario
def _lor(x, y):
    a = ((x == 1) & (y == 1)).sum() + .5
    b = ((x == 1) & (y == 0)).sum() + .5
    c = ((x == 0) & (y == 1)).sum() + .5
    d = ((x == 0) & (y == 0)).sum() + .5
    return np.log(a * d / (b * c)), int((x == 1).sum())


def ajustar(P: pd.DataFrame, X: pd.DataFrame, S: list[dict], cfg: dict) -> dict:
    """Cribado por estabilidad, logística conjunta y validación. P y X: solo casos cerrados."""
    ce = cfg["escenarios"]
    cr_cfg, C = ce["criba"], ce["C"]
    fotos = sorted(P.F.unique())
    corte = fotos[len(fotos) // 2]                      # antiguo -> reciente: mitad de las fotos cerradas
    rng = np.random.default_rng(ce["semilla"])
    cods = np.array(P.ean.unique(), dtype=object)
    rng.shuffle(cods)
    mitad = P.ean.map(dict(zip(cods, np.arange(len(cods)) % 2)))
    fold = P.ean.map(dict(zip(cods, np.arange(len(cods)) % 5)))
    ep_ok = P.e_yoy3.notna() | P.st3.notna() | P.e_last3_vs_rate.notna()
    epos = {s["id"]: s["epos"] for s in S}
    todo = pd.Series(True, index=P.index)
    out = {"corte": int(corte), "fotos": [int(x) for x in fotos]}
    for esc in ESCENARIOS:
        y = P[f"Y_{esc}"]
        filas = []
        for sid in X.columns:
            x = X[sid]
            if epos[sid]:   # las señales de EPOS se prueban en dos mitades de códigos (el EPOS empieza tarde)
                base, partes = ep_ok, [ep_ok & (mitad == 0), ep_ok & (mitad == 1)]
            else:           # el resto, en dos mitades de tiempo
                base, partes = todo, [P.F < corte, P.F >= corte]
            l1, n1 = _lor(x[partes[0]], y[partes[0]])
            l2, n2 = _lor(x[partes[1]], y[partes[1]])
            lt, nt = _lor(x[base], y[base])
            tab = [[int(((x == 1) & (y == 1) & base).sum()), int(((x == 1) & (y == 0) & base).sum())],
                   [int(((x == 0) & (y == 1) & base).sum()), int(((x == 0) & (y == 0) & base).sum())]]
            p = fisher_exact(tab)[1]
            ok = (min(n1, n2) >= cr_cfg["n_min"] and np.sign(l1) == np.sign(l2)
                  and min(abs(l1), abs(l2)) >= cr_cfg["lor_min"] and p < cr_cfg["p_max"])
            filas.append(dict(id=sid, lor=lt, n=nt, p_si=float(y[base & (x == 1)].mean()) if nt else np.nan, ok=ok))
        cr = pd.DataFrame(filas)
        ids = list(cr[cr.ok].sort_values("lor", key=abs, ascending=False).id)
        sel = []
        for s in ids:   # fuera las redundantes
            if all(abs(np.corrcoef(X[s], X[t])[0, 1]) < cr_cfg["corr_max"] for t in sel):
                sel.append(s)
        uni = dict(zip(cr.id, cr.lor))
        for _ in range(6):   # fuera las que cambian de signo en el modelo conjunto o pesan poco
            m = LogisticRegression(C=C, max_iter=5000).fit(X[sel], y)
            co = dict(zip(sel, m.coef_[0]))
            quitar = [s for s in sel if np.sign(co[s]) != np.sign(uni[s]) or abs(co[s]) < cr_cfg["peso_min"]]
            if not quitar:
                break
            sel = [s for s in sel if s not in quitar]
        if not sel:   # ninguna señal estable: solo la tasa base
            b0 = float(np.log((y.mean() + 1e-6) / (1 - y.mean() + 1e-6)))
            coef, pcv, pt = pd.Series(dtype=float), np.full(len(P), y.mean()), np.full(int((P.F >= corte).sum()), y.mean())
        else:
            m = LogisticRegression(C=C, max_iter=5000).fit(X[sel], y)
            coef = pd.Series(m.coef_[0], index=sel)
            b0 = float(m.intercept_[0])
            pcv = np.zeros(len(P))
            for kf in range(5):
                tr, te = fold != kf, fold == kf
                mk = LogisticRegression(C=C, max_iter=5000).fit(X.loc[tr, sel], y[tr])
                pcv[te.to_numpy()] = mk.predict_proba(X.loc[te, sel])[:, 1]
            mt = LogisticRegression(C=C, max_iter=5000).fit(X.loc[P.F < corte, sel], y[P.F < corte])
            pt = mt.predict_proba(X.loc[P.F >= corte, sel])[:, 1]
        pts = (coef * 10).round().astype(int)
        pts = pts[pts != 0]
        tot = X[pts.index] @ pts if len(pts) else pd.Series(0, index=P.index)
        pp = _sig(b0 + tot / 10)
        cal = []
        for lo, hi in ((-99, -15), (-14, -8), (-7, -3), (-2, 2), (3, 7), (8, 14), (15, 99)):
            mk = (tot >= lo) & (tot <= hi)
            if mk.sum() >= 12:
                cal.append(dict(lo=lo, hi=hi, n=int(mk.sum()), pred=float(pp[mk].mean()), obs=float(y[mk].mean())))
        crx = cr.set_index("id")
        out[esc] = dict(base=float(y.mean()), b0=b0, pts={s: int(v) for s, v in pts.items()},
                        auc_cv=_auc(y, pcv), auc_t=_auc(y[P.F >= corte], pt), auc_pts=_auc(y, pp), cal=cal,
                        n_si={s: int(crx.loc[s].n) for s in pts.index},
                        p_si={s: float(crx.loc[s].p_si) for s in pts.index}, pcv=pcv)
    return out


# ------------------------------------------------------------------ 6. de los códigos al grupo entero
def calibrar_grupos(Pm: pd.DataFrame, mod: dict, panel: Panel, cfg: dict) -> dict:
    """Recalibración de grupo: un grupo se mide frente a su Consensus total (Σ vendido / Σ Consensus).

    La media de las probabilidades de los códigos ponderada por su Consensus exagera los escenarios del grupo (un
    código que se hunde lo compensa otro), más cuanto más repartido está el Consensus. Con n = nº efectivo de códigos
    ((ΣC)² / ΣC²) y z = logit de la media ponderada:  P(grupo) = sig(z · (1 + b · ln n) + a · ln n). Con un solo
    código n = 1 y P(grupo) = P(código). Por encima de `grupo_n_max` códigos efectivos ya no se gana más compensación
    (los códigos comparten los golpes de la casa): ln n se topa ahí, y así la casa entera queda bien calibrada.
    a y b se ajustan con los grupos de las fotos cerradas (casa, brand, línea, brand × segmento y selecciones al azar),
    usando las probabilidades de cada código fuera de muestra.
    «Orden no prevista» de un grupo = que al menos un código la tenga: 1 − Π(1 − p) (bien calibrado así)."""
    from scipy.optimize import minimize
    u = cfg["escenarios"]["umbrales"]
    ln_max = float(np.log(cfg["escenarios"].get("grupo_n_max", 8)))
    d0 = Pm.assign(brand=Pm.ean.map(panel.atr["Brand"]), pl=Pm.ean.map(panel.atr["Product Line"]),
                   seg2=Pm.ean.map(panel.atr["Final Segment"]).fillna("-"))
    for esc in ESCENARIOS:
        d0[f"p_{esc}"] = mod[esc]["pcv"]
    rng = np.random.default_rng(cfg["escenarios"]["semilla"])
    grupos = []
    for F, d in d0.groupby("F"):
        for key in (pd.Series("casa", index=d.index), d.brand, d.pl, d.brand + "|" + d.seg2):
            grupos += [g.index.to_numpy() for _, g in d.groupby(key)]
        for _ in range(25):
            n = int(rng.integers(2, 25))
            grupos.append(rng.choice(d.index.to_numpy(), size=min(n, len(d)), replace=False))
    filas = []
    for idx in grupos:
        if len(idx) < 2:
            continue
        d = d0.loc[idx]
        c3 = d.c3.to_numpy()
        r = d.A3.sum() / c3.sum()
        f = dict(F=int(d.F.iloc[0]), ln=min(np.log(c3.sum() ** 2 / (c3 ** 2).sum()), ln_max),
                 bajo=r < u["bajo"], muy_bajo=r < u["muy_bajo"], alto=r > u["alto"], muy_alto=r > u["muy_alto"])
        for esc in ("bajo", "muy_bajo", "alto", "muy_alto"):
            f[f"w_{esc}"] = float((c3 * d[f"p_{esc}"]).sum() / c3.sum())
        filas.append(f)
    D = pd.DataFrame(filas)
    lg = lambda p: np.log(np.clip(p, 1e-4, 1 - 1e-4) / (1 - np.clip(p, 1e-4, 1 - 1e-4)))  # noqa: E731

    def ll(y, p):
        p = np.clip(p, 1e-4, 1 - 1e-4)
        return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))

    def modelo(th, z, ln):
        return _sig(z * (1 + th[1] * ln) + th[0] * ln)

    out = {"n_grupos": int(len(D)), "n_max": float(np.exp(ln_max))}
    for esc in ("bajo", "muy_bajo", "alto", "muy_alto"):
        y, z, ln = D[esc].to_numpy(float), lg(D[f"w_{esc}"].to_numpy()), D.ln.to_numpy()
        th = minimize(lambda t: ll(y, modelo(t, z, ln)), [0.0, 0.0], method="Nelder-Mead").x
        pr = np.zeros(len(D))      # validación dejando fuera una foto entera
        for F in D.F.unique():
            tr = (D.F != F).to_numpy()
            t_ = minimize(lambda t: ll(y[tr], modelo(t, z[tr], ln[tr])), [0.0, 0.0], method="Nelder-Mead").x
            pr[~tr] = modelo(t_, z[~tr], ln[~tr])
        out[esc] = dict(a=round(float(th[0]), 4), b=round(float(th[1]), 4), n_max=out["n_max"], tasa=float(y.mean()),
                        ll_base=ll(y, np.full(len(y), y.mean())), ll_media=ll(y, D[f"w_{esc}"].to_numpy()),
                        ll_recal=ll(y, pr), auc=_auc(y, pr))
    return out


# ------------------------------------------------------------------ 7. salida para la página
# indicadores que explican cada regla: etiqueta y formato en la página
# pct = variación (+12%), x = veces (1.4×), n = número, mes = meses, m = meses de venta, sh = porcentaje (0–1),
# u = unidades, ml = mililitros, cv = coeficiente de variación
VER = {
    "s_yoy3": ("Sell-in, last 3 months vs last year", "pct"),
    "s_yoy12": ("Sell-in, last 12 months vs the year before", "pct"),
    "e_yoy3": ("EPOS, last 3 months vs last year", "pct"),
    "e_yoy6": ("EPOS, last 6 months vs last year", "pct"),
    "s_up6": ("Months above last year (of the last 6)", "n6"),
    "s_last_avg": ("Last month vs its 12-month average", "x"),
    "last3_vs_rate": ("Last 3 months vs its 12-month pace", "x"),
    "s_dd": ("Last 3 months vs its best quarter", "sh"),
    "e_last3_vs_rate": ("EPOS last 3 months vs its 12-month average", "x"),
    "st3": ("Sell-through vs normal", "x"),
    "stock6": ("Channel load over 6 months", "m"),
    "ho_s_yoy3": ("House sell-in, last 3 months", "pct"),
    "br_s_yoy3": ("Brand sell-in, last 3 months", "pct"),
    "pl_s_yoy3": ("Line sell-in, last 3 months", "pct"),
    "pl_share_chg": ("Share in its line, 3 vs 12 months", "x"),
    "br_e_yoy3": ("Brand EPOS, last 3 months", "pct"),
    "ho_e_yoy3": ("House EPOS, last 3 months", "pct"),
    "ly_next3": ("Same 3 months last year vs its average", "x"),
    "s_ms_big": ("Months since its last large order", "mes"),
    "n_big12": ("Large orders in 12 months", "n"),
    "s_cv12": ("Month-to-month variation (CV)", "cv"),
    "s_zeros12": ("Months at zero in the last year", "n"),
    "cut3": ("Cuts, last 3 months", "m"),
    "lan_br_6": ("Brand launches, last 6 months", "n"),
    "lan_pl_6": ("Line launches, last 6 months", "n"),
    "os_br3": ("Brand One Shots vs its regulars, 3 months", "sh"),
    "os_br_yoy3": ("Brand One Shots vs last year", "pct"),
    "ml": ("Size", "ml"),
    "s12": ("Units sold in 12 months", "u"),
    "edad": ("Months since its first sale", "mes"),
    "meses_a_disco": ("Months to discontinuation", "mes"),
    "k_ritmo": ("Consensus vs its 12-month pace", "x"),
    "k_3m": ("Consensus vs the last 3 months sold", "x"),
    "k_ly": ("Consensus vs the same months last year", "x"),
    "k_cg": ("Growth the Consensus assumes vs last year", "pct"),
    "k_da": ("DA share of the Consensus", "sh"),
    "k_79": ("Consensus months 7–9 vs months 1–3", "x"),
    "k_rev": ("Consensus vs 3 snapshots ago", "x"),
    "k_man": ("Consensus vs System FC + DA", "x"),
}


def valores(P: pd.DataFrame) -> pd.DataFrame:
    """Valor de cada indicador de VER, listo para mostrar (variaciones como fracción, ratios como veces)."""
    ex = lambda x: np.exp(x) - 1  # noqa: E731
    div = lambda a, b: np.where(b > 0, a / np.where(b > 0, b, 1), np.nan)  # noqa: E731
    V = pd.DataFrame(index=P.index)
    for c in ("s_yoy3", "s_yoy12", "e_yoy3", "e_yoy6", "ho_s_yoy3", "br_s_yoy3", "pl_s_yoy3", "br_e_yoy3",
              "ho_e_yoy3", "os_br_yoy3"):
        V[c] = ex(P[c])
    V["pl_share_chg"] = np.exp(P.pl_share_chg)
    V["s_up6"] = P.s_up6 * 6
    for c in ("s_last_avg", "last3_vs_rate", "s_dd", "e_last3_vs_rate", "st3", "stock6", "ly_next3", "s_ms_big",
              "n_big12", "s_cv12", "s_zeros12", "cut3", "lan_br_6", "lan_pl_6", "os_br3", "ml", "s12", "edad",
              "meses_a_disco"):
        V[c] = P[c].astype(float)
    V.loc[V.s_ms_big > 12, "s_ms_big"] = np.nan          # 13 = ningún pedido grande en 12 meses
    vend3 = P.last3_vs_rate * 3 * P.mu12
    V["k_ritmo"] = div(P.c3, P.s12 / 4)
    V["k_3m"] = div(P.c3, vend3)
    V["k_ly"] = div(P.c3, P.y3_ly)
    V["k_cg"] = ex(np.log((P.c3 + 1) / (P.y3_ly + 1)))
    V["k_da"] = div(P.da3, P.c3)
    V["k_79"] = div(P.c79, P.c3)
    V["k_rev"] = div(P.c3, P.c3_prev3)
    V["k_man"] = div(P.c3, P.sys3 + P.da3.clip(lower=0))
    return V


def _r(x, nd=3):
    return None if x is None or not np.isfinite(x) else round(float(x), nd)


def calcular(fotos: list[Foto], cfg: dict) -> dict:
    """Probabilidades de la foto más actual por código, reglas y recalibración de grupo, para la página."""
    fotos = sorted(fotos, key=lambda f: f.mes)
    panel = Panel(fotos)
    P, X, S, info = casos(panel, cfg)
    cerr = P.cerrado.to_numpy()
    Pm, Xm = P[cerr].reset_index(drop=True), X[cerr].reset_index(drop=True)
    ult = max(f.mes for f in fotos)
    if len(Pm) < 100 or Pm.F.nunique() < 4:
        return {"foto": int_a_mes(ult), "sin_datos": f"{len(Pm)} closed cases in {Pm.F.nunique()} snapshots"}
    mod = ajustar(Pm, Xm, S, cfg)
    grp = calibrar_grupos(Pm, mod, panel, cfg)
    usadas = [s for s in S if any(s["id"] in mod[e]["pts"] for e in ESCENARIOS)]
    rid = {s["id"]: j for j, s in enumerate(usadas)}
    ver = sorted({v for s in usadas for v in s["ver"]}, key=list(VER).index)
    hoy = (P.F == ult).to_numpy()
    H, XH = P[hoy], X[hoy]
    V = valores(H)
    codigos = {}
    for i in H.index:
        tot = {e: sum(p for s, p in mod[e]["pts"].items() if XH.loc[i, s]) for e in ESCENARIOS}
        codigos[H.ean[i]] = {
            "c": [_r(H.c1[i], 1), _r(H.c2[i], 1), _r(H.c3m[i], 1)],
            "a": [rid[s["id"]] for s in usadas if XH.loc[i, s["id"]]],
            "p": [_r(_sig(mod[e]["b0"] + tot[e] / 10), 4) for e in ESCENARIOS],
            "v": [_r(V.loc[i, v]) for v in ver],
        }
    cats = {}
    for e in ESCENARIOS:
        m = mod[e]
        cats[e] = {"base": _r(m["base"]), "b0": _r(m["b0"], 4), "inicio": _r(_sig(m["b0"])),
                   "auc_cv": _r(m["auc_cv"]), "auc_t": _r(m["auc_t"]), "auc_pts": _r(m["auc_pts"]),
                   "cal": [{**c, "pred": _r(c["pred"]), "obs": _r(c["obs"])} for c in m["cal"]],
                   "pts": [[rid[s], p] for s, p in sorted(m["pts"].items(), key=lambda kv: -abs(kv[1]))],
                   "n_si": {str(rid[s]): n for s, n in m["n_si"].items()},
                   "p_si": {str(rid[s]): _r(p) for s, p in m["p_si"].items()}}
        if e in grp:
            cats[e]["grupo"] = {k: _r(v, 4) for k, v in grp[e].items()}
    return {
        "foto": int_a_mes(ult), "meses": [int_a_mes(ult + h) for h in (1, 2, 3)],
        "umbrales": cfg["escenarios"]["umbrales"],
        "aprendido": {"casos": int(len(Pm)), "codigos": int(Pm.ean.nunique()),
                      "fotos": [int_a_mes(int(f)) for f in sorted(Pm.F.unique())],
                      "corte": int_a_mes(mod["corte"]), "grupos": grp["n_grupos"]},
        "cats": cats,
        "reglas": [{"id": s["id"], "txt": s["txt"], "fam": FAM[s["fam"]], "epos": s["epos"],
                    "ver": [ver.index(v) for v in s["ver"]]} for s in usadas],
        "ver": [[VER[v][0], VER[v][1]] for v in ver],
        "codigos": codigos,
        "fuera": info["fuera"],
    }
