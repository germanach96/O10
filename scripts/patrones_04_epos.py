"""Qué hacer con el EPOS: relación entre sell-in y sell-out (parte de la búsqueda de patrones).

Uso: python -m scripts.patrones_04_epos   (después de patrones_02_casos)

Tres preguntas, todas con información hasta F−1 para predecir F+1…F+3:
1. Trend: para predecir el sell-in de los 3 meses siguientes como "mismos meses del año pasado × (1 + w · trend)",
   ¿qué trend funciona mejor: el de sell-in, el de EPOS o una mezcla m? ¿Y de quién: del código, su línea, su
   brand o la casa? (Es la Brújula 2 del motor, medida solo con lo que pasó.)
2. Canal: cuando el retailer compra más (o menos) de lo que vende, ¿cuánto de ese desfase se corrige el trimestre
   siguiente, y se corrige por el sell-in o por el EPOS?
3. Frente al Consensus: en las fotos reales, ¿una receta tan simple con EPOS le gana al Consensus?
Guarda resultados/cache/epos.json.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from motor import escenarios as es
from scripts import patrones_lib as pl

CACHE = pl.RAIZ / "resultados" / "cache"
MS = [0, .25, .5, .75, 1]
WS = [0, .25, .5, .75, 1]
NIVELES = {"código": ("s_yoy3", "e_yoy3"), "línea": ("pl_s_yoy3", "pl_e_yoy3"),
           "brand": ("br_s_yoy3", "br_e_yoy3"), "casa": ("ho_s_yoy3", "ho_e_yoy3")}
TOPE = np.log(1.5)   # el mismo tope del trend que el motor (±50 %)


def wape(a, f):
    return float(np.abs(f - a).sum() / max(a.sum(), 1e-9))


def boot_dif(Z, f1, f2, n=400, semilla=3):
    """Intervalo 90 % de WAPE(f1) − WAPE(f2) remuestreando códigos enteros."""
    rng = np.random.default_rng(semilla)
    cods = Z.ean.unique()
    idx = {c: np.where(Z.ean.to_numpy() == c)[0] for c in cods}
    a = Z.A3.to_numpy()
    out = []
    for _ in range(n):
        s = np.concatenate([idx[c] for c in rng.choice(cods, len(cods))])
        out.append(wape(a[s], f1[s]) - wape(a[s], f2[s]))
    return [float(np.percentile(out, 5)), float(np.percentile(out, 95))]


def rejilla(Z):
    """WAPE de cada (nivel, m, w) con la base = mismos 3 meses del año pasado."""
    filas = []
    a, base = Z.A3.to_numpy(), Z.y3_ly.to_numpy()
    for niv, (cs, ce) in NIVELES.items():
        ok = Z[cs].notna() & Z[ce].notna()
        for m in MS:
            T = np.clip((1 - m) * Z[cs].fillna(0) + m * Z[ce].fillna(0), -TOPE, TOPE)
            for w in WS:
                f = base * np.exp(w * T)
                filas.append(dict(nivel=niv, m=m, w=w, wape=wape(a[ok], f[ok]), n=int(ok.sum())))
    return pd.DataFrame(filas)


def pregunta_trend(Y):
    """Solo los casos con todos los trends de EPOS (desde ~2025.M10) para comparar en igualdad."""
    cols = [c for par in NIVELES.values() for c in par]
    Z = Y.dropna(subset=cols).reset_index(drop=True)
    res = {"casos": len(Z), "codigos": int(Z.ean.nunique()), "fotos": [pl.int_a_mes(int(Z.F.min())), pl.int_a_mes(int(Z.F.max()))]}
    for casa, g in [("Todas", Z)] + list(Z.groupby("casa")):
        if len(g) < 60:
            continue
        R = rejilla(g.reset_index(drop=True))
        mejor = R.loc[R.wape.idxmin()]
        sin = R[(R.w == 0)].wape.iloc[0]          # solo el año pasado, sin trend
        por_nivel = {}
        for niv, r in R.groupby("nivel"):
            si = r[r.m == 0].wape.min()
            ep = r[r.m == 1].wape.min()
            b = r.loc[r.wape.idxmin()]
            por_nivel[niv] = dict(solo_sellin=si, solo_epos=ep, mejor=float(b.wape), m=float(b.m), w=float(b.w))
        g = g.reset_index(drop=True)
        cs, ce = NIVELES[mejor.nivel]
        Tm = np.clip((1 - mejor.m) * g[cs] + mejor.m * g[ce], -TOPE, TOPE)
        Ts = np.clip(g[NIVELES[mejor.nivel][0]], -TOPE, TOPE)
        ws = R[(R.nivel == mejor.nivel) & (R.m == 0)].sort_values("wape").iloc[0].w
        f_mej = g.y3_ly.to_numpy() * np.exp(mejor.w * Tm.to_numpy())
        f_si = g.y3_ly.to_numpy() * np.exp(ws * Ts.to_numpy())
        res[casa] = dict(casos=len(g), sin_trend=float(sin), mejor=dict(nivel=mejor.nivel, m=float(mejor.m), w=float(mejor.w), wape=float(mejor.wape)),
                         por_nivel=por_nivel, ic90_mejor_menos_solo_sellin=boot_dif(g, f_mej, f_si),
                         rejilla=R.to_dict("records"))
    return res


def pregunta_canal():
    """Desfase del canal: g0 = log((s3/e3) / (s12/e12)) en F; g1 = lo mismo en F+1…F+3. Pendiente de g1 sobre g0 y
    descomposición: cuánto del ajuste viene del sell-in (A3 frente a s3) y cuánto del EPOS (E3 futuro frente a e3)."""
    filas = []
    for casa in pl.CASAS:
        fotos, panel = pl.cargar(casa)
        reg = panel.atr["Article Type"].eq("Regular Item").to_numpy()
        SI, EP, T0, T1 = panel.ACT, panel.EPOS, panel.T0, panel.T1
        for F in range(T0 + 12, T1 - 2):
            k = F - T0
            E12, E3, Ef = EP[:, k - 12:k], EP[:, k - 3:k], EP[:, k:k + 3]
            ok = reg & ~np.isnan(E12).any(1) & ~np.isnan(Ef).any(1)
            s12, s3, a3 = SI[:, k - 12:k].sum(1), SI[:, k - 3:k].sum(1), SI[:, k:k + 3].sum(1)
            e12, e3, ef = E12.sum(1), E3.sum(1), Ef.sum(1)
            ok &= (s12 >= 150) & (e12 >= 100) & (s3 > 0) & (e3 > 0) & (a3 > 0) & (ef > 0)
            for i in np.where(ok)[0]:
                filas.append(dict(casa=casa, F=F, ean=panel.eans[i], g0=np.log((s3[i] / e3[i]) / (s12[i] / e12[i])),
                                  g1=np.log((a3[i] / ef[i]) / (s12[i] / e12[i])),
                                  dsi=np.log(a3[i] / s3[i]), dep=np.log(ef[i] / e3[i]), vol=s12[i]))
    D = pd.DataFrame(filas)
    D = D[np.isfinite(D[["g0", "g1", "dsi", "dep"]]).all(1)]
    D = D[(D.g0.abs() < 3) & (D.g1.abs() < 3)]
    out = {"casos": len(D), "codigos": int(D.ean.nunique()), "fotos": [pl.int_a_mes(int(D.F.min())), pl.int_a_mes(int(D.F.max()))]}
    for casa, g in [("Todas", D)] + list(D.groupby("casa")):
        if len(g) < 60:
            continue
        b = np.polyfit(g.g0, g.g1, 1)[0]
        # g1 − g0 = (dsi − dep): de lo que se corrige, qué parte hace el sell-in y qué parte el EPOS
        bs = np.polyfit(g.g0, g.dsi, 1)[0]
        be = np.polyfit(g.g0, g.dep, 1)[0]
        tram = []
        for lo, hi, nom in ((-3, -.3, "compró ≥ 26 % menos de lo que vendió"), (-.3, -.1, "algo menos"),
                            (-.1, .1, "a la par (±10 %)"), (.1, .3, "algo más"), (.3, 3, "compró ≥ 35 % más de lo que vendió")):
            q = g[(g.g0 >= lo) & (g.g0 < hi)]
            if len(q) >= 15:
                tram.append(dict(tramo=nom, n=len(q), desfase_antes=float(np.expm1(q.g0.median())),
                                 desfase_despues=float(np.expm1(q.g1.median())),
                                 sellin_siguiente_vs_ultimo=float(np.expm1(q.dsi.median())),
                                 epos_siguiente_vs_ultimo=float(np.expm1(q.dep.median()))))
        out[casa] = dict(casos=len(g), persistencia=float(b), ajuste_por_sellin=float(-bs), ajuste_por_epos=float(be),
                         tramos=tram)
    return out


def pregunta_consensus(K):
    """En las fotos reales: Consensus frente a la mejor receta simple (aprendida con la tabla Y de antes de la foto)."""
    Z = K.dropna(subset=["s_yoy3", "e_yoy3", "br_s_yoy3", "br_e_yoy3"]).reset_index(drop=True)
    Z = Z[Z.y3_ly > 0].reset_index(drop=True)
    a = Z.A3.to_numpy()
    out = {"casos": len(Z), "codigos": int(Z.ean.nunique())}
    for casa, g in [("Todas", Z)] + list(Z.groupby("casa")):
        if len(g) < 60:
            continue
        g = g.reset_index(drop=True)
        a = g.A3.to_numpy()
        r = dict(casos=len(g), consensus=wape(a, g.c3.to_numpy()), ano_pasado=wape(a, g.y3_ly.to_numpy()))
        for niv in ("código", "brand"):
            cs, ce = NIVELES[niv]
            for m in (0, .5, 1):
                T = np.clip((1 - m) * g[cs] + m * g[ce], -TOPE, TOPE)
                for w in (.5, 1):
                    r[f"{niv} m={m:g} w={w:g}"] = wape(a, g.y3_ly.to_numpy() * np.exp(w * T.to_numpy()))
        # mezcla receta + Consensus (¿aporta información que el Consensus no tiene?)
        T = np.clip(.5 * g.br_s_yoy3 + .5 * g.br_e_yoy3, -TOPE, TOPE)
        rec = g.y3_ly.to_numpy() * np.exp(.5 * T.to_numpy())
        r["media Consensus y receta brand m=0.5 w=0.5"] = wape(a, .5 * g.c3.to_numpy() + .5 * rec)
        out[casa] = r
    return out


def main():
    Y = pd.read_parquet(CACHE / "casos_Y.parquet")
    K = pd.read_parquet(CACHE / "casos_K.parquet")
    res = {"trend": pregunta_trend(Y), "canal": pregunta_canal(), "consensus": pregunta_consensus(K)}
    (CACHE / "epos.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    t = res["trend"]
    print("TREND", {k: (v["mejor"], round(v["sin_trend"], 3), {n: {kk: round(vv, 3) for kk, vv in d.items()} for n, d in v["por_nivel"].items()}, v["ic90_mejor_menos_solo_sellin"])
                    for k, v in t.items() if isinstance(v, dict) and "mejor" in v})
    print("CANAL", json.dumps({k: v for k, v in res["canal"].items()}, ensure_ascii=False, default=float)[:3000])
    print("CONSENSUS", json.dumps(res["consensus"], ensure_ascii=False, default=float)[:3000])


if __name__ == "__main__":
    _ = es
    main()
