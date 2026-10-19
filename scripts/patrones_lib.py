"""Búsqueda de patrones: casos (EAN × foto), señales visibles en la foto y resultados de los 3 meses siguientes.

Dos tablas de casos por casa:

- **K (frente al Consensus):** las fotos reales cuyos 3 meses ya cerraron. Resultado = lo vendido en F+1…F+3
  frente al Consensus - Final de la foto F (los 4 escenarios: vende menos, mucho menos, más, mucho más).
- **Y (frente al año pasado):** cada mes de la historia hace de "foto" (origen F). Resultado = lo vendido en
  F+1…F+3 frente a esos mismos 3 meses del año anterior, con los mismos 4 umbrales. No usa el Consensus, así que
  aprovecha toda la historia (desde que hay 24 meses detrás).

Toda señal usa solo meses ≤ F−1 (ver `prueba_sin_futuro`). El sell-in vacío es 0; el EPOS vacío es "sin dato".
Los atributos que cambian con el tiempo (segmento, Disco Date) se toman de la foto más cercana anterior a F
(o de la primera foto si F es anterior a todas). El fin de licencia de Gucci (21/06/2027) no cuenta como
discontinuación de producto: afecta a toda la casa a la vez.
"""
from __future__ import annotations

import copy
import json
import warnings
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

from motor import escenarios as es
from motor.lector import int_a_mes, leer_foto, mes_a_int

RAIZ = Path(__file__).resolve().parents[1]
CFG = json.loads((RAIZ / "motor" / "config.json").read_text(encoding="utf-8"))
CASAS = [c.name for c in sorted((RAIZ / "data").iterdir()) if c.is_dir() and any(c.glob("Consensus/*.csv"))]
# fin de licencia: fecha de toda la casa, no de un producto
FECHA_LICENCIA = {"Gucci": "21/06/2027"}
# los 4 escenarios (la orden no prevista queda fuera, a petición del usuario)
UMBRALES = {"bajo": ("<", 0.8), "muy_bajo": ("<", 0.5), "alto": (">", 1.2), "muy_alto": (">", 1.5)}
NOMBRE_Y = {"bajo": "vende menos (< 0,8×)", "muy_bajo": "vende mucho menos (< 0,5×)",
            "alto": "vende más (> 1,2×)", "muy_alto": "vende mucho más (> 1,5×)"}
MIN_REF = 60          # unidades mínimas de la referencia (Consensus o año pasado) en los 3 meses
L = np.log

warnings.filterwarnings("ignore", category=RuntimeWarning)


# ------------------------------------------------------------------ carga
def cargar(casa: str):
    fotos = [leer_foto(r, CFG) for r in sorted((RAIZ / "data" / casa / "Consensus").glob("*.csv"))]
    panel = es.Panel(fotos)
    _atributos_en_el_tiempo(panel, casa)
    return fotos, panel


def _atributos_en_el_tiempo(panel, casa):
    """Segmento y mes de disco por foto (cada código con lo que decía cada foto) y atributos fijos extra."""
    lic = FECHA_LICENCIA.get(casa)
    seg, dis = {}, {}
    for f in panel.fotos:
        c = f.codigos
        seg[f.mes] = c["Final Segment"].to_dict()
        d = c["disco_mes"].where(c["Disco Date"] != lic) if lic else c["disco_mes"]
        dis[f.mes] = d.to_dict()
    panel.seg_foto, panel.disco_foto = seg, dis
    # disco del panel (lo usa escenarios.indicadores) sin la fecha de licencia
    if lic:
        panel.atr["disco_mes"] = panel.atr["disco_mes"].where(panel.atr["Disco Date"] != lic)
    ult = panel.fotos[-1].df.sort_values("t").groupby("EAN").first()
    for col in ("Sub-Category", "Market Category", "Core Category"):
        panel.atr[col] = ult[col].reindex(panel.atr.index) if col in ult else np.nan
    for f in reversed(panel.fotos):   # códigos que ya no salen en la última foto
        g = f.df.sort_values("t").groupby("EAN").first()
        for col in ("Sub-Category", "Market Category", "Core Category"):
            falta = panel.atr[col].isna()
            panel.atr.loc[falta, col] = g[col].reindex(panel.atr.index[falta])
    panel.casa = casa


def attr_en(panel, F: np.ndarray, eans: np.ndarray, cual: str) -> np.ndarray:
    """Atributo (seg o disco) de cada caso según la foto más cercana ≤ F (o la primera foto)."""
    tabla = panel.seg_foto if cual == "seg" else panel.disco_foto
    meses = np.array(sorted(tabla))
    out = np.empty(len(F), dtype=object)
    pos = np.searchsorted(meses, F, side="right") - 1
    pos = np.clip(pos, 0, len(meses) - 1)
    for j, m in enumerate(meses):
        idx = np.where(pos == j)[0]
        if len(idx):
            d = tabla[m]
            # si el código no salía en esa foto, el de la foto más cercana que lo traiga
            vals = [d.get(e, None) for e in eans[idx]]
            out[idx] = vals
    falta = np.array([v is None for v in out])
    if falta.any():
        for i in np.where(falta)[0]:
            for m in sorted(tabla, key=lambda x: abs(x - F[i])):
                if eans[i] in tabla[m]:
                    out[i] = tabla[m][eans[i]]
                    break
    if cual == "disco":
        return pd.to_numeric(pd.Series(out), errors="coerce").to_numpy(float)
    return np.array(["" if v is None or (isinstance(v, float) and np.isnan(v)) else v for v in out], dtype=object)


# ------------------------------------------------------------------ indicadores extra (todos con meses ≤ F−1)
def _w(M, T0, a, b):
    ka, kb = a - T0, b - T0
    if ka < 0 or kb >= M.shape[1]:
        return np.full(M.shape[0], np.nan)
    return M[:, ka:kb + 1].sum(1)


def extras(panel, SI, F_list) -> pd.DataFrame:
    """Indicadores nuevos que no calcula escenarios.indicadores. SI = sell-in armonizado."""
    T0 = panel.T0
    EP, CU = panel.EPOS, panel.CUT
    A = panel.atr
    reg = A["Article Type"].eq("Regular Item").to_numpy()
    brand, pl = A["Brand"].to_numpy(), A["Product Line"].to_numpy()
    tam = A["tamano"].astype(str).to_numpy()
    primer = panel.primer
    ne = len(panel.eans)
    filas = []
    REGm = np.where(reg[:, None], SI, 0)
    pl_tot = es._gsum(REGm, pl)
    br_tot = es._gsum(REGm, brand)
    for F in F_list:
        k = F - T0
        d = {"F": np.full(ne, F), "ean": np.array(panel.eans)}
        X12 = SI[:, k - 12:k]
        mu = X12.mean(1)
        d["zeros3"] = (SI[:, k - 3:k] <= 0).sum(1)
        tt = np.arange(12)
        lx = np.log1p(X12)
        d["s_slope12"] = ((lx - lx.mean(1, keepdims=True)) * (tt - tt.mean())).sum(1) / ((tt - tt.mean()) ** 2).sum()
        # anomalía robusta del último mes: mediana y MAD de los 12 meses
        med = np.median(X12, 1)
        mad = np.median(np.abs(X12 - med[:, None]), 1) * 1.4826
        d["z_rob1"] = (SI[:, k - 1] - med) / (mad + np.maximum(0.1 * med, 1))
        zz = (X12 - med[:, None]) / (mad + np.maximum(0.1 * med, 1))[:, None]
        d["n_anom12"] = (np.abs(zz) > 3).sum(1)
        # base "lo esperable" del libro: nivel 12M × estacionalidad de la brand el año pasado
        lyw = _w(br_tot, T0, F - 11, F - 9) / 3
        ly12 = _w(br_tot, T0, F - 12, F - 1) / 12
        I = np.clip(lyw / np.maximum(ly12, 1), 0.3, 3)
        d["base_rob"] = X12.sum(1) / 12 * 3 * I
        # EPOS: cobertura, último mes, tendencia del sell-through y stock de 3 meses
        E12 = EP[:, k - 12:k]
        d["e_cov12"] = (~np.isnan(E12)).sum(1) / 12
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            em = np.nanmean(E12, 1)
        d["e_last1"] = EP[:, k - 1] / np.maximum(em, 1e-9)
        s3, s6 = SI[:, k - 3:k].sum(1), SI[:, k - 6:k].sum(1)
        e3 = np.where(np.isnan(EP[:, k - 3:k]).any(1), np.nan, np.nansum(EP[:, k - 3:k], 1))
        e6 = np.where(np.isnan(EP[:, k - 6:k]).any(1), np.nan, np.nansum(EP[:, k - 6:k], 1))
        e12 = np.where(np.isnan(E12).any(1), np.nan, np.nansum(E12, 1))
        kap = e12 / np.maximum(X12.sum(1), 1)
        kap = np.where(kap > 0, kap, np.nan)
        d["st_trend"] = (e3 / np.maximum(s3, 1)) / (e6 / np.maximum(s6, 1))
        d["stock3"] = (s3 - e3 / kap) / np.maximum(mu, 1)
        d["kap"] = kap
        # cartera: cuota del código en su línea, nº de códigos activos y lanzamientos hermanos (misma línea y tamaño)
        pl12 = pl_tot[:, k - 12:k].sum(1)
        d["pl_share12"] = X12.sum(1) / np.maximum(pl12, 1)
        act = (X12.sum(1) > 0) & reg
        npl = pd.Series(act).groupby(pl).transform("sum").to_numpy()
        d["pl_ncod"] = npl
        nuevo = reg & (primer >= F - 6) & (primer <= F - 1)
        clave = pd.Series(pl) + "|" + pd.Series(tam)
        hermanos = pd.Series(nuevo.astype(int)).groupby(clave).transform("sum").to_numpy() - nuevo
        d["lan_hermano6"] = hermanos
        # meses desde el último corte
        cut12 = np.nan_to_num(CU[:, k - 12:k]) > 0
        ult = np.array([np.where(r)[0].max() if r.any() else -1 for r in cut12])
        d["ms_cut"] = np.where(cut12.any(1), 12 - ult, 13)
        filas.append(pd.DataFrame(d))
    return pd.concat(filas, ignore_index=True)


# ------------------------------------------------------------------ tabla Y (frente al año pasado, toda la historia)
def casos_Y(panel, k, kb, vieja) -> tuple[pd.DataFrame, np.ndarray]:
    T0, T1 = panel.T0, panel.T1
    origenes = list(range(T0 + 24, T1 - 2))       # 24 meses detrás y F+1…F+3 cerrados (≤ T1)
    falso = copy.copy(panel)
    falso.fotos = [SimpleNamespace(mes=F) for F in origenes]
    Z, SI = es.indicadores(falso, k, kb, vieja)
    E = extras(panel, SI, origenes)
    Z = Z.merge(E, on=["F", "ean"], how="left")
    Z = _filtrar(Z)
    i = Z.ean.map(panel.ix).to_numpy()
    f = Z.F.to_numpy()
    A = np.stack([SI[i, f + h - T0] for h in (1, 2, 3)], 1)
    Z["A3"] = A.sum(1)
    Z["a1"] = A[:, 0]
    Z["ref"] = Z["y3_ly"]
    # resultados de las tarjetas del libro (muerte = 6 meses)
    ok6 = f + 6 <= T1
    y6 = np.full(len(Z), np.nan)
    y6[ok6] = sum(SI[i[ok6], f[ok6] + h - T0] for h in range(1, 7))
    Z["y6"] = y6
    Z = Z[Z.ref >= MIN_REF].reset_index(drop=True)
    return _resultados(Z), SI


def _filtrar(Z):
    Z = Z[(Z.os == 0) & (Z.s12 >= CFG["escenarios"]["minimos"]["vol12"])
          & (Z.edad >= CFG["escenarios"]["minimos"]["edad_meses"])].copy()
    return Z.reset_index(drop=True)


def _resultados(Z):
    r = Z.A3 / Z.ref
    Z["ratio"] = r
    for esc, (op, u) in UMBRALES.items():
        Z[f"Y_{esc}"] = ((r < u) if op == "<" else (r > u)).astype(int)
    return Z


# ------------------------------------------------------------------ tabla K (frente al Consensus, fotos reales)
def casos_K(panel) -> tuple[pd.DataFrame, list[dict], dict]:
    todos, _, S, info = es.casos(panel, CFG)
    P = todos[todos.cerrado].reset_index(drop=True)
    E = extras(panel, _si_armonizado(panel, info), sorted(P.F.unique()))
    P = P.merge(E, on=["F", "ean"], how="left", suffixes=("", "_x"))
    # historial del propio Consensus: lo que pasó en la foto F−4 (sus 3 meses cerraron en F−1)
    r = todos.set_index(["F", "ean"]).eval("A3 / c3")
    prev = r.rename("ratio_F4").reset_index().assign(F=lambda d: d.F + 4)
    P = P.merge(prev, on=["F", "ean"], how="left")
    # media de todos los ratios cerrados antes de F (foto ≤ F−4)
    hist = []
    rr = r.reset_index().rename(columns={0: "r"})
    rr.columns = ["Fp", "ean", "r"]
    for F in sorted(P.F.unique()):
        h = rr[rr.Fp <= F - 4].groupby("ean").r.agg(["mean", "count"])
        hist.append(h.assign(F=F).reset_index())
    H = pd.concat(hist) if hist else pd.DataFrame(columns=["ean", "mean", "count", "F"])
    P = P.merge(H.rename(columns={"mean": "ratio_hist", "count": "n_hist"}), on=["F", "ean"], how="left")
    P["ref"] = P["c3"]
    P = P[P.ref >= MIN_REF].reset_index(drop=True)
    return _resultados(P), S, info


def _si_armonizado(panel, info):
    k, kb, vieja = info["k"], info["kb"], info["vieja"]
    brand = panel.atr["Brand"].to_numpy()
    kk = np.array([k.get(e, kb.get(brand[i], 1.0)) for i, e in enumerate(panel.eans)])[:, None]
    return np.where(panel.SRC <= vieja, panel.ACT * kk, panel.ACT)


# ------------------------------------------------------------------ grupos de cada caso
def grupos(Z: pd.DataFrame, panel) -> pd.DataFrame:
    A = panel.atr
    Z = Z.copy()
    Z["casa"] = panel.casa
    Z["brand"] = Z.ean.map(A["Brand"]).str.replace(r"\s*\(\d+\)$", "", regex=True)
    Z["linea"] = Z.ean.map(A["Product Line"]).str.replace(r"\s*\(\d+\)$", "", regex=True)
    tam = Z.ean.map(A["tamano"]).astype(str)
    sub = Z.ean.map(A["Sub-Category"]).astype(str).str.replace(r"\s*\(\d+\)$", "", regex=True)
    Z["tamano"] = np.where(tam.eq("Make up"), sub, tam)    # maquillaje: subcategoría en lugar de tamaño
    F, e = Z.F.to_numpy(), Z.ean.to_numpy()
    Z["seg"] = attr_en(panel, F, e, "seg")
    disco = attr_en(panel, F, e, "disco")
    Z["meses_a_disco"] = disco - F
    Z["tramo_edad"] = np.select([Z.meses_a_disco.between(0, 12), Z.edad <= 24, Z.edad <= 36],
                                ["Pre-disco", "13-24 meses", "25-36 meses"], "37+ meses")
    # volumen (terciles dentro de la casa)
    Z["tramo_vol"] = pd.qcut(Z.s12.rank(method="first"), 3, labels=["vol bajo", "vol medio", "vol alto"]).astype(str)
    return Z


def listas(Z: pd.DataFrame) -> pd.DataFrame:
    """Pertenencia a las listas de data/filters.csv (una columna booleana por lista)."""
    ruta = RAIZ / "data" / "filters.csv"
    if not ruta.exists():
        return Z
    d = pd.read_csv(ruta, sep=";", dtype=str, encoding="utf-8-sig")
    for c in d.columns:
        eans = set(d[c].dropna().str.strip())
        Z[f"lista_{c.strip()}"] = Z.ean.isin(eans)
    return Z


# ------------------------------------------------------------------ señales
FAMILIAS = dict(es.FAM, libro="Libro de señales", n="Nuevas")


def senales(Z: pd.DataFrame, con_consensus: bool) -> list[dict]:
    """Señales binarias: las 113 del motor (las del Consensus solo en K), las del libro y las nuevas."""
    P = Z.copy()
    if not con_consensus:   # columnas del Consensus vacías: sus señales salen siempre falsas y se descartan
        for c in ("c1", "c2", "c3m", "c3", "c46", "c79", "da3", "sys3", "flag", "c3_prev1", "c3_prev3"):
            P[c] = np.nan
    S = es.senales(P)
    for s in S:
        s["origen"] = "motor"
    if not con_consensus:
        S = [s for s in S if s["fam"] != "k"]
    S = [s for s in S if s["id"] != "O_disco"]   # se rehace abajo con el disco de cada foto (sin licencia)
    S += [dict(s, origen="libro") for s in senales_libro(P)]
    S += [dict(s, origen="nueva") for s in senales_nuevas(P, con_consensus)]
    for s in S:
        s["mask"] = pd.Series(s["mask"], index=P.index).fillna(False).astype(bool).to_numpy()
    # fuera las que casi no se dan o casi siempre se dan
    return [s for s in S if 20 <= s["mask"].sum() <= 0.9 * len(P)]


def _add(S, sid, fam, txt, mask, epos=False):
    S.append(dict(id=sid, fam=fam, txt=txt, epos=epos, mask=mask))


def senales_libro(P) -> list[dict]:
    S = []
    a = lambda *x: _add(S, *x)  # noqa: E731
    a("C1", "libro", "Errático (CV ≥ 0,9), pequeño (< 4.000 uds/año) y último mes < 30 % de su media",
      (P.s_cv12 >= .9) & (P.s12 < 4000) & (P.s_last_avg < .3))
    a("C2", "libro", "Crece ≥ 4× más que su brand y es errático (CV ≥ 0,9)", (P.rs_br >= L(4)) & (P.s_cv12 >= .9))
    a("C3", "libro", "Crece ≥ 6× más que su línea mientras la línea cae ≥ 40 %", (P.rs_pl >= L(6)) & (P.pl_s_yoy3 <= L(.6)))
    a("C4", "libro", "Brand en campaña de One Shots (≥ 70 % del regular en 3M) y tamaño ≥ 150 ml",
      (P.os_br3 >= .7) & (P.ml >= 150))
    a("C5", "libro", "Muy errático (CV ≥ 1,25) y pequeño (< 4.000 uds/año)", (P.s_cv12 >= 1.25) & (P.s12 < 4000))
    a("M1", "libro", "Pequeño, errático (CV ≥ 1) y su línea cae ≥ 30 %",
      (P.s12 < 4000) & (P.s_cv12 >= 1) & (P.pl_s_yoy3 <= L(.7)))
    a("M2", "libro", "Rabbit con EPOS ≥ 25 % peor que el EPOS de su brand", (P.seg == "Rabbits") & (P.rs_br_e <= L(.75)), True)
    a("M3", "libro", "Muy errático (CV ≥ 1,25) y pedido grande en los últimos 3 meses", (P.s_cv12 >= 1.25) & (P.s_ms_big <= 3))
    a("M4", "libro", "Tamaño ≥ 150 ml con pedido grande en los últimos 2 meses", (P.ml >= 150) & (P.s_ms_big <= 2))
    a("M5", "libro", "Pequeño (< 4.000 uds/año) y su línea cae ≥ 30 %", (P.s12 < 4000) & (P.pl_s_yoy3 <= L(.7)))
    a("U1", "libro", "≥ 3 pedidos grandes en 12M y últimos 3M ≥ 1,5× su ritmo", (P.n_big12 >= 3) & (P.last3_vs_rate >= 1.5))
    a("U2", "libro", "Irregular (algún mes a cero) que se reactiva: 3M ≥ 1,2× ritmo y brand sin campaña OS",
      (P.s_zeros12 >= 1) & (P.last3_vs_rate >= 1.2) & (P.os_br3 < .05))
    a("U3", "libro", "Llenado de canal: sell-through ≤ 0,69 de lo normal y pedido grande en 3 meses",
      (P.st3 <= .69) & (P.s_ms_big <= 3), True)
    a("U4", "libro", "Cortes ≥ 0,6 meses de venta y EPOS de la brand cae ≥ 20 %", (P.cut3 >= .6) & (P.br_e_yoy3 <= L(.8)), True)
    a("V1", "libro", "Último mes < 10 % de la media y sin cortes", (P.s_last_avg < .1) & (P.cut3 <= 0))
    a("V2", "libro", "Último mes < 10 % de la media y tendencia de 12M negativa", (P.s_last_avg < .1) & (P.s_slope12 < -.1))
    a("V3", "libro", "Último mes < 10 % de la media con cortes > 1 mes de venta", (P.s_last_avg < .1) & (P.cut3 > 1))
    return S


def senales_nuevas(P, con_consensus) -> list[dict]:
    S = []
    a = lambda *x: _add(S, *x)  # noqa: E731
    ex = lambda x: np.exp(x) - 1  # noqa: E731
    # sell-in: anomalías robustas (mediana y MAD) y forma de la serie
    a("N_anom_hi", "n", "El último mes es una anomalía al alza (más de 3 MAD sobre su mediana de 12 meses)", P.z_rob1 > 3)
    a("N_anom_lo", "n", "El último mes es una anomalía a la baja (más de 3 MAD bajo su mediana de 12 meses)", P.z_rob1 < -3)
    a("N_anom_muchas", "n", "3 o más meses anómalos (más de 3 MAD) en el último año", P.n_anom12 >= 3)
    a("N_sin_anom", "n", "Ningún mes anómalo en el último año (serie limpia)", P.n_anom12 == 0)
    a("N_pend_up", "n", "Pendiente de 12 meses claramente al alza (+3 % al mes o más)", P.s_slope12 > .03)
    a("N_pend_dn", "n", "Pendiente de 12 meses claramente a la baja (−3 % al mes o menos)", P.s_slope12 < -.03)
    a("N_ceros3", "n", "Algún mes a cero en los últimos 3", P.zeros3 >= 1)
    # sell-in frente a sell-out
    a("N_st_mejora", "n", "El sell-through mejora: el retailer vende en 3M un 20 % más de lo que compra que en 6M", P.st_trend > 1.2, True)
    a("N_st_empeora", "n", "El sell-through empeora: en 3M vende un 20 % menos de lo que compra que en 6M", P.st_trend < .8, True)
    a("N_stock3_alto", "n", "Canal cargado en 3 meses: entró más de 1 mes de venta de más", P.stock3 > 1, True)
    a("N_stock3_bajo", "n", "Canal vacío en 3 meses: entró más de 1 mes de venta de menos", P.stock3 < -1, True)
    a("N_ep_ult_lo", "n", "El EPOS del último mes cae por debajo de 0,6× su media", P.e_last1 < .6, True)
    a("N_ep_ult_hi", "n", "El EPOS del último mes sube por encima de 1,4× su media", P.e_last1 > 1.4, True)
    a("N_ep_parcial", "n", "EPOS incompleto: solo 1 a 9 de los últimos 12 meses con dato", P.e_cov12.between(1 / 12, .75), True)
    a("N_kap_bajo", "n", "Pocos retailers reportan: el EPOS cubre menos del 30 % del sell-in", P.kap < .3, True)
    a("N_kap_alto", "n", "El EPOS cubre casi todo: más del 80 % del sell-in", P.kap > .8, True)
    a("N_si_up_ep_plano", "n", "Sell-in sube (> +15 %) con el EPOS plano (±5 %)", (P.s_yoy3 > L(1.15)) & (P.e_yoy3.abs() < L(1.05)), True)
    a("N_si_dn_ep_plano", "n", "Sell-in baja (< −15 %) con el EPOS plano (±5 %)", (P.s_yoy3 < L(.85)) & (P.e_yoy3.abs() < L(1.05)), True)
    # cartera
    a("N_lider_linea", "n", "Es el líder de su línea (≥ 50 % de su sell-in en 12M)", P.pl_share12 >= .5)
    a("N_cola_linea", "n", "Es cola de su línea (< 5 % de su sell-in en 12M)", P.pl_share12 < .05)
    a("N_linea_larga", "n", "Su línea tiene 8 o más códigos activos", P.pl_ncod >= 8)
    a("N_solo_linea", "n", "Es el único código activo de su línea", P.pl_ncod <= 1)
    a("N_hermano_nuevo", "n", "Se lanzó un hermano (misma línea y tamaño) en los últimos 6 meses", P.lan_hermano6 >= 1)
    a("N_corte_reciente", "n", "Tuvo un corte el último mes", P.ms_cut <= 1)
    a("N_corte_viejo", "n", "Tuvo cortes hace 4 a 12 meses, pero ninguno en los últimos 3", P.ms_cut.between(4, 12))
    a("N_disco12", "n", "Fecha de discontinuación de producto en los próximos 12 meses (sin contar el fin de licencia)",
      P.meses_a_disco.between(0, 12))
    if con_consensus:
        ritmo3 = P.s12 / 4
        a("N_k_vs_esp_hi", "n", "El Consensus de 3 meses supera en 1,3× lo esperable (nivel 12M × estacionalidad de su brand)",
          P.c3 > 1.3 * P.base_rob)
        a("N_k_vs_esp_lo", "n", "El Consensus de 3 meses es menos de 0,77× lo esperable", P.c3 < .77 * P.base_rob)
        a("N_k_rev1_up", "n", "El Consensus de estos meses subió más del 15 % frente a la foto anterior", P.c3 > 1.15 * P.c3_prev1)
        a("N_k_rev1_dn", "n", "El Consensus de estos meses bajó más del 15 % frente a la foto anterior", P.c3 < .85 * P.c3_prev1)
        quieto = ((P.c3 / P.c3_prev1 - 1).abs() < .03) & ((P.c3 / P.c3_prev3 - 1).abs() < .03)
        a("N_k_quieto", "n", "Consensus congelado: casi igual (±3 %) que hace 1 y 3 fotos", quieto)
        quieto_mueve = quieto & ((P.last3_vs_rate > 1.3) | (P.last3_vs_rate < .7))
        a("N_k_quieto_mueve", "n", "Consensus congelado aunque las ventas de 3 meses se alejan más de un 30 % de su ritmo", quieto_mueve)
        a("N_k_paso_bajo", "n", "La última vez que se midió (foto F−4) vendió menos de 0,8× su Consensus", P.ratio_F4 < .8)
        a("N_k_paso_alto", "n", "La última vez que se midió (foto F−4) vendió más de 1,2× su Consensus", P.ratio_F4 > 1.2)
        a("N_k_hist_bajo", "n", "De media, en sus fotos ya medidas vendió menos de 0,8× su Consensus", P.ratio_hist < .8)
        a("N_k_hist_alto", "n", "De media, en sus fotos ya medidas vendió más de 1,2× su Consensus", P.ratio_hist > 1.2)
        a("N_k_sobre_rev_dn", "n", "Se recortó el Consensus (−15 % frente a la foto anterior) aunque las ventas de 3M van por encima de su ritmo",
          (P.c3 < .85 * P.c3_prev1) & (P.last3_vs_rate > 1))
        a("N_k_sube_ventas_dn", "n", "Se subió el Consensus (+15 %) aunque las ventas de 3M van por debajo de su ritmo",
          (P.c3 > 1.15 * P.c3_prev1) & (P.last3_vs_rate < 1))
        a("N_k_ep_vs", "n", "El Consensus supera 1,3× su ritmo mientras el EPOS cae (< −10 %)",
          (P.c3 > 1.3 * ritmo3) & (P.e_yoy3 < L(.9)), True)
        a("N_k_sys_bajo", "n", "El System FC está por debajo de 0,6× su ritmo (el estadístico ve caída)", P.sys3 < .6 * ritmo3)
        a("N_k_sys_alto", "n", "El System FC está por encima de 1,5× su ritmo", P.sys3 > 1.5 * ritmo3)
        a("N_k_cerca_sys", "n", "Consensus casi igual al System FC + DA (±5 %): no se tocó a mano",
          ((P.c3 / (P.sys3 + P.da3.clip(lower=0)).clip(lower=1)) - 1).abs() < .05)
    _ = ex
    return S


# ------------------------------------------------------------------ casos independientes (ventanas que no se solapan)
def independientes(F: np.ndarray, eans: np.ndarray, sep: int = 3) -> int:
    """Nº de casos cuyas ventanas de 3 meses no se pisan: por código, orígenes con al menos `sep` meses entre sí."""
    tot = 0
    df = pd.DataFrame({"F": F, "e": eans}).sort_values(["e", "F"])
    for _, g in df.groupby("e"):
        last = -10 ** 9
        for f in g.F:
            if f - last >= sep:
                tot += 1
                last = f
    return tot


# ------------------------------------------------------------------ prueba de que ninguna señal usa el futuro
def prueba_sin_futuro(casa: str, n_origenes: int = 3, semilla: int = 1) -> list[str]:
    """Borra (pone a basura) todos los meses ≥ F del panel y recalcula las señales del origen F: deben salir iguales."""
    fotos, panel = cargar(casa)
    k, kb, sn, vieja = es.perimetro(panel, CFG["escenarios"]["ruptura_perimetro"].get(casa))
    rng = np.random.default_rng(semilla)
    T0, T1 = panel.T0, panel.T1
    candidatos = list(range(T0 + 24, T1 - 2))
    fallos = []
    for F in rng.choice(candidatos, size=min(n_origenes, len(candidatos)), replace=False):
        F = int(F)
        base = _senales_origen(panel, k, kb, vieja, F)      # el panel de producción, con todo el futuro
        sucio = copy.copy(panel)
        kk = F - T0
        for nom in ("ACT", "CUT", "EPOS"):
            M = getattr(panel, nom).copy()
            M[:, kk:] = rng.uniform(0, 1e5, size=M[:, kk:].shape)
            setattr(sucio, nom, M)
        # SRC del futuro no cambia el pasado; los primeros meses de venta se recalculan con el panel sucio
        prim = np.where((panel.ACT[:, :kk] > 0).any(1), panel.meses[(panel.ACT[:, :kk] > 0).argmax(1)], -1)
        sucio.primer = prim
        otra = _senales_origen(sucio, k, kb, vieja, F)
        comunes = base.index.intersection(otra.index)
        dif = (base.loc[comunes] != otra.loc[comunes]).sum()
        dif = dif[dif > 0]
        if len(dif) or len(base) != len(otra):
            fallos.append(f"{casa} {int_a_mes(F)}: {dict(dif)} filas {len(base)} vs {len(otra)}")
    return fallos


def _senales_origen(panel, k, kb, vieja, F) -> pd.DataFrame:
    falso = copy.copy(panel)
    falso.fotos = [SimpleNamespace(mes=F)]
    Z, SI = es.indicadores(falso, k, kb, vieja)
    Z = Z.merge(extras(panel, SI, [F]), on=["F", "ean"], how="left")
    Z = grupos(_filtrar(Z), panel)
    S = senales(Z.assign(c3=np.nan), con_consensus=False)
    return pd.DataFrame({s["id"]: s["mask"] for s in S}, index=Z.ean)


__all__ = ["CASAS", "cargar", "casos_K", "casos_Y", "grupos", "listas", "senales", "UMBRALES", "NOMBRE_Y",
           "independientes", "prueba_sin_futuro", "mes_a_int", "int_a_mes", "FAMILIAS"]
