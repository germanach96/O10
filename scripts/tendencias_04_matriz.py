"""Matriz de resultados de los trends: trend × base × horizonte (después de tendencias_01_calculo).

Uso: python -m scripts.tendencias_04_matriz   → resultados/cache/tendencias_matriz.json y trend_matrix.html (raíz)

- **Filas** (una tabla con los trends de 6M y otra con los de 12M): sell-in puro (EAN, PL, Brand, House), EPOS puro
  (ídem), mezcla 50/50 de cada nivel de EPOS con cada nivel de sell-in, y EPOS en cascada (el del EAN; si no tiene,
  el de su PL, después el de la Brand y por último el de la House), puro y mezclado 50/50 con cada sell-in.
  Trend de la mezcla = 0,5 · sell-in + 0,5 · EPOS, recortado a ±50% (como el motor).
- **Bases** (lo que multiplica (1 + trend)), todas con la historia de la foto verdad:
  - Mean 12M: media de los 12 meses cerrados antes de la foto;
  - LY: los mismos meses del año anterior;
  - Mean 12M + Seas 100%: media × índice estacional de la House (Regular Items, sell-in), media de 2 años;
  - Mean 12M + Seas 50%: media × (1 + índice) / 2.
  Índice de un año: mes del año anterior ÷ media de los 12 meses que acaban antes de la foto; el de hace 2 años,
  con la media de su propio año (como `e` = 2 en el motor). Sin 2 años de historia, solo el de un año.
- **Horizontes** acumulados desde la foto: 3M (meses 1–3), 6M, 9M y 12M. Solo las fotos con todos esos meses
  cerrados. En el mes 12 el año pasado es el propio mes de la foto (ya cerrado en la foto verdad).
- **Medidas** en cada celda, sobre todos los casos en que existe ese trend (EAN × foto, Regular, con ventas en los
  12 meses anteriores):
  - % cumplido: casos en que lo vendido quedó entre 0,8× y 1,2× de lo previsto (base × (1 + trend));
  - mejora de WAPE frente a la misma base sin trend en esos mismos casos (en puntos; negativo = mejor);
  - WAPE con trend; fotos en que mejora; nº de casos y parte del volumen.
- **Perímetro:** lo vendido, la base y el año pasado salen de la última foto que trae el código (perímetro nuevo,
  después del salto de 2026.M02); el trend, de lo que traía cada foto (un cociente dentro del mismo archivo). El
  Consensus de cada foto se lleva al perímetro nuevo con un factor por código: ventas de 12 meses en la foto verdad ÷
  en la foto (si el código vendió menos de 50 uds, el de su casa).
"""
from __future__ import annotations

import json
import warnings

import numpy as np
import pandas as pd

from motor.lector import int_a_mes, leer_foto
from scripts.tendencias_01_calculo import CASAS, CFG, RAIZ, REG, Panel, _claves, _rejilla, trends

warnings.filterwarnings("ignore", category=RuntimeWarning)

SALIDA = RAIZ / "resultados" / "cache" / "tendencias_matriz.json"
NIV = ["cod", "pl", "brand", "house"]
HORIZ = [3, 6, 9, 12]
BASES = ["m", "ly", "s50", "s100"]
TOPE = 0.5
BANDA = (0.8, 1.2)


def filas_trend(N):
    """(clave, señal sell-in o None, señal EPOS o None) de cada fila de la tabla."""
    f = [(f"si_{a}", f"si_{a}_{N}", None) for a in NIV]
    f += [(f"ep_{a}", None, f"ep_{a}_{N}") for a in NIV + ["cas"]]
    f += [(f"mx_{e}_{s}", f"si_{s}_{N}", f"ep_{e}_{N}") for e in NIV + ["cas"] for s in NIV]
    return f


def indice_casa(H, reg, k, n_h):
    """Índice estacional de la casa (Regular Items) para los meses k+1…k+n_h, siendo k el mes de la foto; media
    de 1 o 2 años, cada uno normalizado con la media de los 12 meses que acaban antes de la foto (o un año antes)."""
    G = np.nansum(np.where(reg[:, None], H, 0), 0)
    t = np.arange(k + 1, k + n_h + 1)
    m1 = G[k - 12:k].mean()
    I1 = G[t - 12] / m1 if m1 > 0 else np.ones(n_h)
    if k - 24 >= 0 and not np.isnan(H[:, k - 24]).all():
        m2 = G[k - 24:k - 12].mean()
        if m2 > 0:
            return (I1 + G[t - 24] / m2) / 2
    return I1


def casos_casa(casa):
    fotos = [leer_foto(r, CFG) for r in sorted((RAIZ / "data" / casa / "Consensus").glob("*.csv"))]
    P = Panel(fotos)
    regP = (P.atr["Article Type"] == REG).to_numpy()
    filas = []
    for f in fotos:
        F = f.mes
        hmax = max([h for h in HORIZ if F + h <= P.t1], default=0)
        if not hmax:
            continue
        reg = (f.codigos["Article Type"] == REG).to_numpy()
        H = f.mat["hist"].copy()
        H[:, f.meses >= F] = np.nan
        E = f.mat["EPOS"].copy()
        E[:, f.meses >= F] = np.nan
        if np.isnan(E).all():                                       # foto sin EPOS: historia de la primera posterior
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
        for N in (6, 12):                                           # EPOS en cascada: EAN → PL → Brand → House
            c = T[f"ep_cod_{N}"].copy()
            for nv in ("pl", "brand", "house"):
                c = np.where(np.isnan(c), T[f"ep_{nv}_{N}"], c)
            T[f"ep_cas_{N}"] = c
        idx = np.array([P.ix[e] for e in f.eans])
        kp = F - P.t0
        Hv = np.nan_to_num(P.H)
        B12 = Hv[idx, kp - 12:kp].sum(1)
        # Consensus al perímetro nuevo: ventas de 12 meses en la foto verdad ÷ en la foto
        v12_f = np.nansum(H[:, k - 12:k], 1)
        fac_casa = B12[reg].sum() / max(v12_f[reg].sum(), 1)
        fac = np.where(v12_f >= 50, B12 / np.maximum(v12_f, 1), fac_casa)
        I = indice_casa(P.H, regP, kp, hmax)                       # meses F+1…F+hmax
        C = f.mat["Consensus - Final"]
        for h in HORIZ:
            if h > hmax:
                continue
            ks = np.arange(kp + 1, kp + h + 1)
            d = {"casa": casa, "F": F, "h": h, "ean": f.eans, "reg": reg, "B12": B12,
                 "A": Hv[idx][:, ks].sum(1),
                 "b_m": B12 / 12 * h, "b_ly": Hv[idx][:, ks - 12].sum(1),
                 "b_s100": B12 / 12 * I[:h].sum(), "b_s50": B12 / 12 * ((1 + I[:h]) / 2).sum(),
                 "C": np.nansum(C[:, np.arange(k + 1, k + h + 1)], 1) * fac}
            for N in (6, 12):
                for nv in NIV + ["cas"]:
                    d[f"ep_{nv}_{N}"] = T[f"ep_{nv}_{N}"]
                for nv in NIV:
                    d[f"si_{nv}_{N}"] = T[f"si_{nv}_{N}"]
            filas.append(pd.DataFrame(d))
    df = pd.concat(filas, ignore_index=True)
    df = df[df.reg & (df.B12 > 0)].drop(columns="reg").reset_index(drop=True)
    print(f"{casa}: {len(df):,} casos")
    return df


def medir(x, Tcol, b):
    """Medidas de una celda: x = casos con el trend, Tcol = trend ya mezclado, b = columna de la base."""
    A = x.A.to_numpy()
    base = x[b].to_numpy()
    Fc = np.maximum(base * (1 + np.clip(Tcol, -TOPE, TOPE)), 0)
    wape = lambda F: float(np.abs(F - A).sum() / A.sum()) if A.sum() > 0 else None
    ok = lambda F: float(((A >= BANDA[0] * F) & (A <= BANDA[1] * F) & (F > 0)).mean())
    w0, w1 = wape(base), wape(Fc)
    gan = []
    for _, g in x.assign(_F=Fc).groupby("F"):
        a = g.A.to_numpy()
        if a.sum() > 0:
            gan.append(np.abs(g._F - a).sum() / a.sum() < np.abs(g[b] - a).sum() / a.sum())
    return {"w0": w0, "w1": w1, "d": None if w0 is None else (w1 - w0), "ok1": ok(Fc), "ok0": ok(base),
            "ayuda": int(sum(gan)), "fotos": len(gan)}


def main():
    d = pd.concat([casos_casa(c) for c in CASAS], ignore_index=True)
    res = {"casas": CASAS, "t": {}, "ref": {}, "fotos": {}}
    for casa in ["all"] + CASAS:
        dc = d if casa == "all" else d[d.casa == casa]
        for h in HORIZ:
            x = dc[dc.h == h]
            res["fotos"][f"{casa}|{h}"] = sorted({int_a_mes(int(F)) for F in x.F})
            # referencias: base sin trend sobre todos los casos, y el Consensus
            ref = {"n": len(x), "vol": float(x.A.sum())}
            for b in BASES:
                ref[b] = medir(x, np.zeros(len(x)), f"b_{b}")
            cx = x[x.C.notna()]
            if len(cx) and cx.A.sum() > 0:
                Cc = cx.C.to_numpy()
                ref["cons"] = {"w1": float(np.abs(Cc - cx.A).sum() / cx.A.sum()),
                               "ok1": float(((cx.A >= .8 * Cc) & (cx.A <= 1.2 * Cc) & (Cc > 0)).mean())}
            res["ref"][f"{casa}|{h}"] = ref
            for N in (6, 12):
                for clave, si, ep in filas_trend(N):
                    cols = [c for c in (si, ep) if c]
                    y = x[x[cols].notna().all(axis=1)]
                    celda = {"n": len(y), "cov": len(y) / max(len(x), 1),
                             "cov_vol": float(y.B12.sum() / max(x.B12.sum(), 1)), "cod": int(y.ean.nunique())}
                    if len(y) >= 30:
                        T = (y[si].to_numpy() if si else 0) * (0.5 if si and ep else 1) + \
                            (y[ep].to_numpy() if ep else 0) * (0.5 if si and ep else 1)
                        for b in BASES:
                            celda[b] = medir(y, T, f"b_{b}")
                    res["t"][f"{casa}|{h}|{N}|{clave}"] = celda
    SALIDA.write_text(json.dumps(res, default=float).replace("NaN", "null"), encoding="utf-8")
    print(f"→ {SALIDA.relative_to(RAIZ)}")
    pagina(res)


def pagina(res):
    """Incrusta la matriz en scripts/plantilla_matriz.html (la página no calcula nada: solo dibuja)."""
    from scripts.tendencias_03_html import redondear
    res = dict(res, version=(RAIZ / "VERSION").read_text(encoding="utf-8").strip())
    html = (RAIZ / "scripts" / "plantilla_matriz.html").read_text(encoding="utf-8").replace(
        "/*__DATOS__*/null", json.dumps(redondear(res), ensure_ascii=False, separators=(",", ":")))
    (RAIZ / "trend_matrix.html").write_text(html, encoding="utf-8")
    print(f"→ trend_matrix.html ({len(html) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
