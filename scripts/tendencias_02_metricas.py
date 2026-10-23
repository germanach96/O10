"""Métricas de relevancia y fiabilidad de cada trend (después de tendencias_01_calculo).

Uso: python -m scripts.tendencias_02_metricas   → resultados/cache/tendencias.json

Para cada modo (fotos / historia), casa (y todas juntas), tramo (1–3, 4–6, 7–9), señal (sell-in / EPOS),
nivel (código, PL, brand, house) y duración N (3, 6, 9, 12):

- **Cobertura:** % de casos (y de volumen) en que el trend se puede calcular.
- **Relevancia (¿anticipa?):**
  - acierto de dirección: entre los casos en que el código se movió más de ±10% frente al año anterior, % en que el
    trend tenía el mismo signo (ponderado por volumen del año anterior);
  - correlación de rangos (Spearman) entre el trend y el crecimiento real;
  - persistencia β: de cada 10 puntos de trend, cuántos aparecen en el crecimiento real (pendiente ponderada).
- **Mejora del forecast:** WAPE de la base sin trend frente a la base × (1 + T), con el trend recortado a ±50%
  como en el motor. Dos bases: media de 12 meses (s = 0) y mismos meses del año anterior (s = 1). Peso w óptimo.
- **Fiabilidad:** en cuántos orígenes mejora, cuántos valores distintos tiene (un trend de casa es uno por origen),
  qué parte se sale del tope, y la mejora por tamaño del código.
- **Frente al Consensus (solo modo fotos):** si el trend anticipa dónde se equivoca el Consensus.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from motor.lector import int_a_mes

warnings.filterwarnings("ignore", category=RuntimeWarning)

RAIZ = Path(__file__).resolve().parents[1]
CASOS = RAIZ / "resultados" / "cache" / "tendencias_casos.parquet"
SALIDA = RAIZ / "resultados" / "cache" / "tendencias.json"

NS = [3, 6, 9, 12]
NIVELES = ["cod", "pl", "brand", "house"]
SENALES = ["si", "ep"]
TOPE = 0.5
PESOS = [0, 0.25, 0.5, 0.75, 1, 1.25, 1.5]
MOV = 0.10            # movimiento mínimo para medir el acierto de dirección
MIN_CASOS = 60        # por debajo, la métrica no se muestra
TAMANOS = {"small": (0, 1000), "medium": (1000, 10000), "large": (10000, np.inf)}   # uds en 12 meses


def wape(F, A):
    s = A.sum()
    return float(np.abs(F - A).sum() / s) if s > 0 else np.nan


def spearman(x, y):
    if len(x) < 10:
        return np.nan
    return float(pd.Series(x).rank().corr(pd.Series(y).rank()))


def medir(x: pd.DataFrame, col: str, todos: pd.DataFrame) -> dict | None:
    """Métricas de un trend sobre los casos x (ya filtrados por modo, casa y tramo)."""
    ok = x[col].notna()
    y = x[ok]
    out = {"n": int(ok.sum()), "codigos": int(x.ean[ok].nunique()), "cov": float(ok.mean()) if len(x) else 0.0,
           "cov_vol": float(y.LY.sum() / x.LY.sum()) if x.LY.sum() > 0 else 0.0}
    if len(y) < MIN_CASOS:
        return out
    T = y[col].to_numpy()
    Tc = np.clip(T, -TOPE, TOPE)
    A, LY = y.A.to_numpy(), y.LY.to_numpy()
    G = A / LY - 1
    base_m = y.B12.to_numpy() / 12 * 3
    # relevancia
    mov = np.abs(G) > MOV
    acierto = (np.sign(T) == np.sign(G)) & mov
    out["hit"] = float((LY * acierto).sum() / (LY * mov).sum()) if mov.any() else np.nan
    out["hit_n"] = int(mov.sum())
    out["rho"] = spearman(T, G)
    Gc = np.clip(G, -1, 2)
    out["beta"] = float((LY * Tc * Gc).sum() / (LY * Tc * Tc).sum()) if (Tc != 0).any() else np.nan
    out["cap"] = float((np.abs(T) > TOPE).mean())
    out["t_med"] = float(np.median(np.abs(T)))
    # mejora del forecast
    for nb, base in (("m", base_m), ("ly", LY)):
        w0 = wape(base, A)
        curva = [wape(np.maximum(base * (1 + w * Tc), 0), A) for w in PESOS]
        out[f"w0_{nb}"] = w0
        out[f"w1_{nb}"] = curva[PESOS.index(1)]
        out[f"curva_{nb}"] = curva
        i = int(np.nanargmin(curva[:5]))       # mejor w dentro de la rejilla del motor (0…100%)
        out[f"wbest_{nb}"] = PESOS[i]
        out[f"wbest_{nb}_wape"] = curva[i]
        out[f"w1_{nb}_sin_tope"] = wape(np.maximum(base * (1 + T), 0), A)
    # fiabilidad: orígenes en que mejora (w = 100%), con cada base
    for nb in ("m", "ly"):
        gan = []
        for F, g in y.groupby("F"):
            if len(g) < 5:
                continue
            b = g.B12.to_numpy() / 12 * 3 if nb == "m" else g.LY.to_numpy()
            t = np.clip(g[col].to_numpy(), -TOPE, TOPE)
            gan.append((int(F), wape(b, g.A.to_numpy()) - wape(np.maximum(b * (1 + t), 0), g.A.to_numpy())))
        out[f"origenes_{nb}"] = [[int_a_mes(F), round(v, 4)] for F, v in gan]
        out[f"helps_{nb}"] = float(np.mean([v > 0 for _, v in gan])) if gan else np.nan
        out["n_origenes"] = len(gan)
    out["n_valores"] = int(pd.Series(np.round(T, 6)).nunique())
    # por tamaño del código
    tam = {}
    for nt, (a, b) in TAMANOS.items():
        s = (y.B12 >= a) & (y.B12 < b)
        if s.sum() >= MIN_CASOS:
            bb = base_m[s.to_numpy()]
            bl = LY[s.to_numpy()]
            tam[nt] = {"n": int(s.sum()), "w0_m": wape(bb, A[s.to_numpy()]),
                       "w1_m": wape(np.maximum(bb * (1 + Tc[s.to_numpy()]), 0), A[s.to_numpy()]),
                       "w0_ly": wape(bl, A[s.to_numpy()]),
                       "w1_ly": wape(np.maximum(bl * (1 + Tc[s.to_numpy()]), 0), A[s.to_numpy()])}
    out["tam"] = tam
    # frente al Consensus: ¿el trend anticipa dónde se equivoca?
    if y.C.notna().all() and (y.C > 0).sum() >= MIN_CASOS:
        z = y[y.C > 0]
        tz = z[col].to_numpy()
        r = z.A.to_numpy() / z.C.to_numpy()
        out["rho_cons"] = spearman(tz, r)
        sube, baja = tz > MOV, tz < -MOV
        out["cons_sube"] = float(z.A[sube].sum() / z.C[sube].sum()) if sube.sum() >= 20 else np.nan
        out["cons_baja"] = float(z.A[baja].sum() / z.C[baja].sum()) if baja.sum() >= 20 else np.nan
        out["cons_n"] = [int(sube.sum()), int(baja.sum())]
        out["w_cons"] = wape(z.C.to_numpy(), z.A.to_numpy())
        # el Consensus corregido con el trend que no recogió: C × (1 + T)/(1 + crecimiento del Consensus)
        gc = z.C.to_numpy() / np.maximum(z.LY_F.to_numpy(), 1) - 1
        tc = np.clip(tz, -TOPE, TOPE)
        ajuste = np.clip((1 + tc) / np.maximum(1 + gc, 0.2), 0.5, 1.5)
        out["w_cons_mix"] = wape(z.C.to_numpy() * (0.5 + 0.5 * ajuste), z.A.to_numpy())
    return out


def comun(x: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    return x[x[cols].notna().all(axis=1)]


def main():
    d = pd.read_parquet(CASOS)
    casas = sorted(d.casa.unique())
    res = {"meta": {}, "m": {}, "duelo": {}}
    for modo in ("fotos", "historia"):
        dm = d[d.modo == modo]
        for casa in ["all"] + casas:
            dc = dm if casa == "all" else dm[dm.casa == casa]
            for tr in (1, 2, 3):
                x = dc[dc.tramo == tr]
                clave = f"{modo}|{casa}|{tr}"
                res["m"][clave] = {}
                for s in SENALES:
                    for nv in NIVELES:
                        for N in NS:
                            col = f"{s}_{nv}_{N}"
                            res["m"][clave][col] = medir(x, col, dc)
                # duelo en un conjunto común: códigos con EPOS (sell-in vs EPOS, mismos casos), N = 3 y 6
                cols = [f"{s}_{nv}_{N}" for s in SENALES for nv in NIVELES for N in (3, 6)]
                z = comun(x, cols)
                if len(z) >= MIN_CASOS:
                    duelo = {"n": len(z), "codigos": int(z.ean.nunique())}
                    for nb, b in (("m", z.B12.to_numpy() / 12 * 3), ("ly", z.LY.to_numpy())):
                        duelo[f"w0_{nb}"] = wape(b, z.A.to_numpy())
                        for c in cols:
                            t = np.clip(z[c].to_numpy(), -TOPE, TOPE)
                            duelo[f"{c}_{nb}"] = wape(np.maximum(b * (1 + t), 0), z.A.to_numpy())
                    if z.C.notna().all():
                        duelo["cons"] = wape(z.C.to_numpy(), z.A.to_numpy())
                    res["duelo"][clave] = duelo
                res["meta"][clave] = {"n": len(x), "codigos": int(x.ean.nunique()),
                                      "origenes": sorted({int_a_mes(int(F)) for F in x.F})}
    # robustez: fotos sin EPOS propio (completado con una foto posterior) frente a fotos con EPOS propio
    df_f = d[d.modo == "fotos"]
    res["periodo"] = {}
    for tr in (1, 2, 3):
        for back, nom in ((True, "completado"), (False, "propio")):
            x = df_f[(df_f.tramo == tr) & (df_f.epos_completado == back)]
            res["periodo"][f"{tr}|{nom}"] = {
                "fotos": sorted({int_a_mes(int(F)) for F in x.F}),
                "m": {c: medir(x, c, x) for c in ("ep_cod_3", "ep_pl_3", "si_cod_6", "ep_house_3", "si_house_9")}}
    res["meta"]["casas"] = casas
    res["meta"]["fotos"] = sorted({int_a_mes(int(F)) for F in d[d.modo == "fotos"].F})
    res["meta"]["origenes_historia"] = [int_a_mes(int(d[d.modo == "historia"].F.min())),
                                        int_a_mes(int(d[d.modo == "historia"].F.max()))]
    res["meta"]["codigos"] = {c: int(d[d.casa == c].ean.nunique()) for c in casas}
    SALIDA.write_text(json.dumps(res, allow_nan=True, default=float).replace("NaN", "null"), encoding="utf-8")
    print(f"→ {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
