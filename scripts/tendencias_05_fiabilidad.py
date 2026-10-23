"""Fiabilidad de cada trend por plazo, en unidades (ponderada por volumen), foto a foto.

Uso: python -m scripts.tendencias_05_fiabilidad   → resultados/cache/tendencias_fiabilidad.json, trend_reliability.html
(raíz) y la tabla en pantalla

Para cada código y foto, lo que el trend anticipaba es el cambio frente al año pasado en unidades: LY × T (T
recortado a ±50%, como el motor). Lo que pasó es A − LY. Sumando en unidades, los códigos grandes pesan más:

- **Fiabilidad (como el WAPE, no compensa):** 1 − Σ|(A − LY) − LY·T| / Σ|A − LY|. 100% = anticipó exactamente lo
  que se movió cada código; 0% = igual que suponer que no cambia; negativo = despista más que no usarlo.
- **Bias (como el SPP, compensa) en el sentido del trend:** Σ signo(T) · ((A − LY) − LY·T) / Σ LY, en puntos de
  crecimiento ponderados por volumen. Positivo = la realidad fue más lejos que el trend en el sentido que marcaba
  (trend −5%, real −7% → +2; trend +15%, real +20% → +5); negativo = se quedó corta (trend −5%, real −4% → −1;
  trend +15%, real +10% → −5). Los casos con trend 0 no marcan sentido y no cuentan.

Se calcula en cada foto y se da la mediana de las fotos (y su rango). Plazos acumulados desde la foto: 3M (meses
1–3), 6M, 9M y 12M, solo con fotos que tienen esos meses cerrados. A 12M solo hay una foto (2025.M09, sin EPOS); para
el sell-in se añade la historia larga: cada mes de la última foto como punto de partida.
"""
from __future__ import annotations

import json
import warnings

import numpy as np
import pandas as pd

from motor.lector import int_a_mes, leer_foto
from scripts.tendencias_01_calculo import CASAS, CFG, RAIZ, REG, Panel, _claves, trends
from scripts.tendencias_04_matriz import NIV, casos_casa

warnings.filterwarnings("ignore", category=RuntimeWarning)

SALIDA = RAIZ / "resultados" / "cache" / "tendencias_fiabilidad.json"
HORIZ = [3, 6, 9, 12]
TOPE = 0.5
MIN_CASOS = 20


def historia_12m(casa):
    """Casos de la historia larga a 12M para el sell-in: cada mes de la última foto como punto de partida."""
    fotos = [leer_foto(r, CFG) for r in sorted((RAIZ / "data" / casa / "Consensus").glob("*.csv"))]
    P = Panel(fotos)
    reg = (P.atr["Article Type"] == REG).to_numpy()
    cl = _claves(P.atr)
    Hv = np.nan_to_num(P.H)
    filas = []
    for F in range(P.inicio + 24, P.t1 - 11):
        k = F - P.t0
        H = P.H.copy()
        H[:, k:] = np.nan
        T = trends(H, np.full_like(H, np.nan), k, cl, reg)
        ks = np.arange(k + 1, k + 13)
        d = {"casa": casa, "F": F, "h": 12, "ean": P.eans, "B12": Hv[:, k - 12:k].sum(1),
             "A": Hv[:, ks].sum(1), "b_ly": Hv[:, ks - 12].sum(1), "reg": reg}
        for N in (6, 12):
            for nv in NIV:
                d[f"si_{nv}_{N}"] = T[f"si_{nv}_{N}"]
        filas.append(pd.DataFrame(d))
    if not filas:                                            # casa sin 3 años de historia (Kylie Frag)
        return pd.DataFrame()
    df = pd.concat(filas, ignore_index=True)
    return df[df.reg & (df.B12 > 0)].drop(columns="reg")


def sesgo(g, col):
    """Bias en el sentido del trend, en puntos de crecimiento ponderados por el volumen del año pasado."""
    T = np.clip(g[col], -TOPE, TOPE)
    z = g[(T != 0) & (g.b_ly > 0)]
    Tz = np.clip(z[col], -TOPE, TOPE)
    den = z.b_ly.sum()
    return float((np.sign(Tz) * ((z.A - z.b_ly) - z.b_ly * Tz)).sum() / den) if den > 0 else np.nan


def medir(x, col):
    """Fiabilidad y bias en unidades, foto a foto (mediana y rango) y con todas las fotos juntas."""
    y = x[x[col].notna()]
    por_foto = []
    for F, g in y.groupby("F"):
        if len(g) < MIN_CASOS:
            continue
        mov = g.A - g.b_ly                                   # lo que se movió cada código, en unidades
        prev = g.b_ly * np.clip(g[col], -TOPE, TOPE)         # lo que anticipaba el trend
        den = np.abs(mov).sum()
        if den > 0:
            por_foto.append((int_a_mes(int(F)), 1 - np.abs(mov - prev).sum() / den, sesgo(g, col), len(g)))
    if not por_foto:
        return {"n": int(len(y)), "fotos": 0}
    fi = np.array([p[1] for p in por_foto])
    bi = np.array([p[2] for p in por_foto])
    mov = y.A - y.b_ly
    prev = y.b_ly * np.clip(y[col], -TOPE, TOPE)
    den = np.abs(mov).sum()
    return {"n": int(len(y)), "codigos": int(y.ean.nunique()), "fotos": len(por_foto),
            "fiab": float(np.median(fi)), "fiab_min": float(fi.min()), "fiab_max": float(fi.max()),
            "bias": float(np.median(bi)), "bias_min": float(bi.min()), "bias_max": float(bi.max()),
            "fiab_total": float(1 - np.abs(mov - prev).sum() / den), "bias_total": sesgo(y, col),
            "detalle": [[p[0], round(p[1], 4), round(p[2], 4), p[3]] for p in por_foto]}


def main():
    d = pd.concat([casos_casa(c) for c in CASAS], ignore_index=True)
    hist = pd.concat([historia_12m(c) for c in CASAS], ignore_index=True)
    filas = [(f"si_{a}", "Sell-in · " + {"cod": "EAN", "pl": "PL", "brand": "Brand", "house": "House"}[a]) for a in NIV]
    filas += [(f"ep_{a}", "EPOS · " + {"cod": "EAN", "pl": "PL", "brand": "Brand", "house": "House", "cas": "cascade"}[a])
              for a in NIV + ["cas"]]
    res = {"casas": CASAS, "r": {}}
    for casa in ["all"] + CASAS:
        dc = d if casa == "all" else d[d.casa == casa]
        hc = hist if casa == "all" else hist[hist.casa == casa] if casa in set(hist.casa) else hist.iloc[:0]
        for N in (6, 12):
            for clave, _ in filas:
                col = f"{clave}_{N}"
                for h in HORIZ:
                    res["r"][f"{casa}|{N}|{clave}|{h}"] = medir(dc[dc.h == h], col)
                if clave.startswith("si"):
                    res["r"][f"{casa}|{N}|{clave}|12h"] = medir(hc, col)
    SALIDA.write_text(json.dumps(res).replace("NaN", "null"), encoding="utf-8")
    # tabla en pantalla: todas las casas
    for N in (6, 12):
        print(f"\nTrends de {N}M · fiabilidad / bias (mediana de las fotos, en unidades)")
        for clave, nombre in filas:
            celdas = []
            for h in HORIZ + (["12h"] if clave.startswith("si") else []):
                m = res["r"][f"all|{N}|{clave}|{h}"]
                celdas.append(f"{m['fiab']*100:5.0f}% {m['bias']*100:+5.1f}pt ({m['fotos']})" if m.get("fotos") else " " * 18)
            print(f"{nombre:18}", " | ".join(celdas))
    print(f"→ {SALIDA.relative_to(RAIZ)}")
    pagina(res)


def pagina(res):
    """Incrusta los resultados en scripts/plantilla_fiabilidad.html (la página no calcula nada: solo dibuja)."""
    from scripts.tendencias_04_matriz import hasta, redondear
    html = (RAIZ / "scripts" / "plantilla_fiabilidad.html").read_text(encoding="utf-8").replace(
        "/*__DATOS__*/null", json.dumps(redondear(dict(res, hasta=hasta())), ensure_ascii=False, separators=(",", ":")))
    (RAIZ / "trend_reliability.html").write_text(html, encoding="utf-8")
    print(f"→ trend_reliability.html ({len(html) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
