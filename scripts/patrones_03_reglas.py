"""Pasos 4-5 de la búsqueda de patrones: barrido de reglas "señal → resultado" por grupo, puntuación y validación.

Uso: python -m scripts.patrones_03_reglas   (después de patrones_02_casos)

Para cada tabla (K = frente al Consensus, Y = frente al año pasado) y cada uno de los 4 escenarios:
1. Reglas = (grupo, señal) y (grupo amplio, pareja de señales). Se cuentan con productos de matrices.
2. Descubrimiento con las fotos antiguas: test binomial frente a la tasa base del grupo con los casos
   independientes (las ventanas de 3 meses de un mismo código se solapan) y Benjamini-Hochberg sobre TODAS las
   reglas probadas de la tabla.
3. Comprobación en las fotos recientes: misma dirección, efecto suficiente y significativo por sí solo.
4. Medidas finales con todos los datos: n, probabilidad, base, lift, probabilidad prudente (Wilson 90 %),
   estabilidad por foto y por casa, puntuación original y propuesta.
5. Explicaciones aburridas: quitar el código con más casos, su línea dominante, la brand dominante, la foto con más
   casos, la casa dominante y, en K, las fotos de la ruptura de perímetro.
Guarda resultados/cache/reglas_{K,Y}.parquet y resultados/cache/resumen_reglas.json.
"""
from __future__ import annotations

import json
from itertools import combinations

import numpy as np
import pandas as pd
from scipy.stats import binom

from scripts import patrones_lib as pl

CACHE = pl.RAIZ / "resultados" / "cache"
Z90 = 1.6449
# separación antiguo / reciente (primer mes de la parte reciente)
CORTE = {"K": pl.mes_a_int("2026.M02"), "Y": pl.mes_a_int("2025.M07"), "Y_epos": pl.mes_a_int("2026.M01")}
RUPTURA_K = {pl.mes_a_int("2026.M01"), pl.mes_a_int("2026.M02")}
COLS_GRUPO = ["casa", "brand", "linea", "tamano", "seg", "tramo_edad", "tramo_vol"]
CRUCES = [("casa", "seg"), ("casa", "tramo_edad"), ("casa", "tramo_vol"), ("brand", "seg"), ("brand", "tramo_edad"),
          ("seg", "tramo_edad"), ("seg", "tramo_vol"), ("tamano", "seg"), ("tramo_edad", "tramo_vol")]
GRUPOS_PAREJAS = {"todo", "casa", "seg", "tramo_edad", "tramo_vol", "brand"}
N_MIN, N_MIN_PARTE, N_MIN_GRUPO = 20, 10, 40
# tabla Y: el trimestre del año pasado (F−11…F−9) debe quedar fuera del primer año de vida (efecto lanzamiento) y no
# se usan las señales que miran justo ese trimestre (son el denominador del resultado: efecto base mecánico)
EDAD_MIN_Y = 24
SENALES_BASE_Y = {"C_ly_valle", "C_ly_pico", "C_ly_big3"}
JACCARD = 0.5
MAX_MEDIR = 400       # reglas por escenario que se miden una a una (las de más ganancia aproximada)


# ------------------------------------------------------------------ utilidades estadísticas
def wilson_lo(p, n):
    n = np.maximum(n, 1e-9)
    c = p + Z90 ** 2 / (2 * n)
    r = Z90 * np.sqrt(p * (1 - p) / n + Z90 ** 2 / (4 * n ** 2))
    return (c - r) / (1 + Z90 ** 2 / n)


def p_binom(k, n, p0, lado=0):
    """p-valor binomial con n y k efectivos (redondeados). lado: +1 cola alta, −1 cola baja, 0 dos colas."""
    n = np.maximum(np.round(n), 1).astype(int)
    k = np.clip(np.round(k), 0, n).astype(int)
    p0 = np.clip(p0, 1e-6, 1 - 1e-6)
    alta = binom.sf(k - 1, n, p0)
    baja = binom.cdf(k, n, p0)
    if lado > 0:
        return alta
    if lado < 0:
        return baja
    return np.minimum(1, 2 * np.minimum(alta, baja))


def bh(p):
    p = np.asarray(p)
    n = len(p)
    o = np.argsort(p)
    q = p[o] * n / np.arange(1, n + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    out = np.empty(n)
    out[o] = np.minimum(q, 1)
    return out


# ------------------------------------------------------------------ grupos
def subconjuntos(Z: pd.DataFrame) -> list[tuple[str, str, np.ndarray]]:
    S = [("todo", "Todas las casas", np.ones(len(Z), bool))]
    for c in COLS_GRUPO:
        for v, idx in Z.groupby(c).groups.items():
            if v in ("", "nan", "N/D", "None") or len(idx) < N_MIN_GRUPO:
                continue
            m = np.zeros(len(Z), bool)
            m[np.asarray([Z.index.get_loc(i) for i in idx])] = True
            S.append((c, str(v), m))
    for c in [c for c in Z.columns if c.startswith("lista_")]:
        m = Z[c].astype(str).eq("True").to_numpy()
        if m.sum() >= N_MIN_GRUPO:
            S.append(("lista", c[6:], m))
    for a, b in CRUCES:
        for (va, vb), idx in Z.groupby([a, b]).groups.items():
            if "" in (va, vb) or "nan" in (va, vb) or len(idx) < N_MIN_GRUPO:
                continue
            m = np.zeros(len(Z), bool)
            m[np.asarray([Z.index.get_loc(i) for i in idx])] = True
            S.append((f"{a}×{b}", f"{va} × {vb}", m))
    return S


# ------------------------------------------------------------------ barrido
def barrer(Z, X, meta, tabla):
    sids = list(X.columns)
    Xm = X.to_numpy(np.float32)
    epos = np.array([m["epos"] for m in meta])
    F = Z.F.to_numpy()
    rec = {False: F >= CORTE[tabla], True: F >= CORTE["Y_epos" if tabla == "Y" else tabla]}
    # proporción de casos independientes de cada señal (ventanas de 3 meses que no se pisan)
    eans = Z.ean.to_numpy()
    r_ind = np.array([pl.independientes(F[Xm[:, j] > 0], eans[Xm[:, j] > 0]) / max(Xm[:, j].sum(), 1)
                      for j in range(len(sids))])
    subs = subconjuntos(Z)
    G = np.stack([s[2] for s in subs], 1).astype(np.float32)
    trozos = []
    ns = len(sids)
    sids_a = np.array(sids, dtype=object)
    for esc in pl.UMBRALES:
        y = Z[f"Y_{esc}"].to_numpy(np.float32)
        # una fila por (grupo, señal suelta): matrices grupo × señal
        cols = {}
        for nom in ("D", "T", "A"):
            N = np.zeros((len(subs), ns), np.float32)
            K = np.zeros_like(N)
            n0 = np.zeros((len(subs), ns), np.float32)
            k0 = np.zeros_like(n0)
            for ep in (False, True):
                m = {"D": ~rec[ep], "T": rec[ep], "A": np.ones(len(Z), bool)}[nom].astype(np.float32)
                Gm = G * m[:, None]
                cj = epos == ep
                N[:, cj] = (Gm.T @ Xm)[:, cj]
                K[:, cj] = ((Gm * y[:, None]).T @ Xm)[:, cj]
                n0[:, cj] = Gm.sum(0)[:, None]
                k0[:, cj] = (Gm * y[:, None]).sum(0)[:, None]
            cols[nom] = (N.ravel(), K.ravel(), n0.ravel(), k0.ravel())
        gi = np.repeat(np.arange(len(subs)), ns)
        jj = np.tile(np.arange(ns), len(subs))
        d = pd.DataFrame({"esc": esc, "gi": gi, "s1": sids_a[jj], "s2": "", "r": r_ind[jj], "epos": epos[jj]})
        for nom in ("D", "T", "A"):
            d[f"n{nom}"], d[f"k{nom}"], d[f"n0{nom}"], d[f"k0{nom}"] = cols[nom]
        trozos.append(d[d.nA >= N_MIN])
        # parejas en los grupos amplios
        iu, ju = np.triu_indices(ns, 1)
        epp = epos[iu] | epos[ju]
        for g, (tipo, val, gm) in enumerate(subs):
            if tipo not in GRUPOS_PAREJAS:
                continue
            d = {}
            for nom in ("D", "T", "A"):
                vals = []
                for ep in (False, True):
                    m = {"D": ~rec[ep], "T": rec[ep], "A": np.ones(len(Z), bool)}[nom]
                    sel = gm & m
                    Xs, ys = Xm[sel], y[sel]
                    vals.append(((Xs.T @ Xs)[iu, ju], ((Xs * ys[:, None]).T @ Xs)[iu, ju], float(sel.sum()), float(ys.sum())))
                pick = lambda t: np.where(epp, vals[1][t], vals[0][t])  # noqa: E731
                d[f"n{nom}"], d[f"k{nom}"], d[f"n0{nom}"], d[f"k0{nom}"] = pick(0), pick(1), pick(2), pick(3)
            keep = d["nA"] >= N_MIN
            if not keep.any():
                continue
            t = pd.DataFrame({k: v[keep] for k, v in d.items()})
            t.insert(0, "esc", esc)
            t.insert(1, "gi", g)
            t.insert(2, "s1", sids_a[iu[keep]])
            t.insert(3, "s2", sids_a[ju[keep]])
            t.insert(4, "r", np.minimum(r_ind[iu[keep]], r_ind[ju[keep]]))
            t.insert(5, "epos", epp[keep])
            trozos.append(t)
    R = pd.concat(trozos, ignore_index=True)
    R["tabla"] = tabla
    R["tipo"] = [subs[g][0] for g in R.gi]
    R["grupo"] = [subs[g][1] for g in R.gi]
    R = R[(R.nA >= N_MIN) & (R.nD >= N_MIN_PARTE) & (R.nT >= N_MIN_PARTE)].reset_index(drop=True)
    for nom in ("D", "T", "A"):
        R[f"p{nom}"] = R[f"k{nom}"] / R[f"n{nom}"]
        R[f"b{nom}"] = R[f"k0{nom}"] / R[f"n0{nom}"]
    R["pval_D"] = p_binom(R.kD * R.r, R.nD * R.r, R.bD)
    R["q_D"] = bh(R.pval_D.to_numpy())
    return R, subs


def efecto(p, b):
    lift = p / np.maximum(b, 1e-9)
    return (lift >= 1.5) | (lift <= 0.67) | ((p - b).abs() >= 0.15)


def filtrar(R):
    """Descubrimiento (BH) y comprobación en las fotos recientes."""
    dirD = np.sign(R.pD - R.bD)
    ok_D = (R.q_D < 0.10) & efecto(R.pD, R.bD)
    dirT = np.sign(R.pT - R.bT)
    lado = np.where(dirD > 0, 1, -1)
    pT = np.where(lado > 0, p_binom(R.kT * R.r, R.nT * R.r, R.bT, 1), p_binom(R.kT * R.r, R.nT * R.r, R.bT, -1))
    R["pval_T"] = pT
    liftT = R.pT / R.bT.clip(lower=1e-9)
    ok_T = (dirT == dirD) & ((R.pT - R.bT).abs() >= 0.07) & ((liftT >= 1.2) | (liftT <= 0.83)) & (pT < 0.10)
    R["pasa_D"], R["pasa_T"] = ok_D, ok_D & ok_T
    R["valor_anadido"] = valor_anadido(R)
    R["pasa"] = R.pasa_T & R.valor_anadido
    return R


def valor_anadido(R):
    """Una pareja debe mejorar a sus dos señales sueltas en el mismo grupo, y una regla de un grupo a la misma señal
    en todas las casas: +5 puntos sobre la base con todos los datos y sin empeorar en las fotos recientes."""
    gapA, gapT = (R.pA - R.bA).abs(), np.sign(R.pD - R.bD) * (R.pT - R.bT)
    suelta = R[R.s2 == ""].set_index(["esc", "gi", "s1"])
    gA = (suelta.pA - suelta.bA).abs().to_dict()
    gT = (np.sign(suelta.pD - suelta.bD) * (suelta.pT - suelta.bT)).to_dict()
    ok = np.ones(len(R), bool)
    for i, (esc, gi, s1, s2) in enumerate(zip(R.esc, R.gi, R.s1, R.s2)):
        if s2:
            comp = [(esc, gi, s1), (esc, gi, s2)]
        elif gi != 0:
            comp = [(esc, 0, s1)]
        else:
            continue
        refA = max(gA.get(c, 0) for c in comp)
        refT = max(gT.get(c, -1) for c in comp)
        ok[i] = (gapA.iat[i] >= refA + 0.05) and (gapT.iat[i] >= refT - 0.02)
    return ok


# ------------------------------------------------------------------ medidas finales de una regla
def medir(mask, y, Z, base_mask, dir_=None):
    """Medidas de la tarjeta en la dirección que predice (dir = +1: pasa el escenario; −1: no pasa)."""
    n = int(mask.sum())
    p = y[mask].mean()
    b = y[base_mask].mean()
    if dir_ is None:
        dir_ = 1 if p >= b else -1
    pc, bc = (p, b) if dir_ > 0 else (1 - p, 1 - b)
    F, e = Z.F.to_numpy(), Z.ean.to_numpy()
    n_ind = pl.independientes(F[mask], e[mask])
    lo = float(wilson_lo(pc, n_ind))
    # estabilidad por foto (≥ 3 casos con la señal) y por casa (≥ 10)
    fotos_ok = fotos_tot = 0
    for f in np.unique(F[mask]):
        mf = mask & (F == f)
        if mf.sum() >= 3:
            fotos_tot += 1
            bf = y[base_mask & (F == f)].mean()
            fotos_ok += int(np.sign(y[mf].mean() - bf) == dir_)
    casas = Z.casa.to_numpy()
    casa_ok = casa_tot = 0
    por_casa = {}
    for c in np.unique(casas[mask]):
        mc = mask & (casas == c)
        bcasa = y[base_mask & (casas == c)].mean()
        por_casa[c] = (int(mc.sum()), float(y[mc].mean()), float(bcasa))
        if mc.sum() >= 10:
            casa_tot += 1
            casa_ok += int(np.sign(y[mc].mean() - bcasa) == dir_)
    est_f = fotos_ok / fotos_tot if fotos_tot else np.nan
    est_c = casa_ok / casa_tot if casa_tot else np.nan
    est = np.nanmin([est_f, est_c]) if casa_tot >= 2 else est_f
    pen = 1.0 if (np.isnan(est) or est >= 0.6) else est / 0.6
    s0 = 100 * lo * pen
    gan = 100 * (lo - bc) * pen
    return dict(n=n, n_indep=n_ind, codigos=int(len(np.unique(e[mask]))), fotos=int(len(np.unique(F[mask]))),
                prob=float(p), base=float(b), lift=float(p / max(b, 1e-9)), dir=int(dir_),
                prob_tarjeta=float(pc), base_tarjeta=float(bc), prob_prudente=lo,
                estab_fotos=est_f, estab_casas=est_c, estabilidad=est,
                puntuacion=s0, clase=("A" if s0 >= 70 and pen == 1 else "B" if s0 >= 55 else "C"),
                ganancia=gan, clase_ganancia=("A" if gan >= 20 and pen == 1 else "B" if gan >= 10 else "C"),
                por_casa=por_casa)


def aburridas(mask, y, Z, base_mask, dir_, tabla):
    """Quita, por turnos, la explicación aburrida y mira si la tarjeta sigue en pie (misma dirección y al menos la
    mitad de su ventaja sobre la base)."""
    p, b = y[mask].mean(), y[base_mask].mean()
    gap = dir_ * (p - b)
    pruebas = {}
    e = Z.ean.to_numpy()
    top_ean = pd.Series(e[mask]).value_counts().index[0]
    pruebas["sin su código con más casos"] = e != top_ean
    br = Z.brand.to_numpy()
    vc = pd.Series(br[mask]).value_counts(normalize=True)
    if vc.iloc[0] >= 0.5:
        pruebas[f"sin la brand dominante ({vc.index[0]}, {vc.iloc[0]:.0%} de los casos)"] = br != vc.index[0]
    li = Z.linea.to_numpy()
    vl = pd.Series(li[mask]).value_counts(normalize=True)
    pruebas[f"sin su línea dominante ({vl.index[0]}, {vl.iloc[0]:.0%} de los casos)"] = li != vl.index[0]
    F = Z.F.to_numpy()
    top_f = pd.Series(F[mask]).value_counts().index[0]
    pruebas[f"sin la foto con más casos ({pl.int_a_mes(int(top_f))})"] = F != top_f
    if tabla == "K":
        pruebas["sin las fotos de la ruptura de perímetro"] = ~np.isin(F, list(RUPTURA_K))
    ca = Z.casa.to_numpy()
    vc = pd.Series(ca[mask]).value_counts(normalize=True)
    if vc.iloc[0] >= 0.5 and len(vc) > 1:
        pruebas[f"sin la casa dominante ({vc.index[0]})"] = ca != vc.index[0]
    caidas = []
    for nom, keep in pruebas.items():
        m, bm = mask & keep, base_mask & keep
        if m.sum() < 10:
            caidas.append(f"{nom}: quedan < 10 casos")
            continue
        g2 = dir_ * (y[m].mean() - y[bm].mean())
        if g2 < 0.5 * gap:
            caidas.append(f"{nom}: {y[m].mean():.0%} frente a base {y[bm].mean():.0%}")
    return caidas


def tarjetas(R, Z, X, subs, meta, tabla):
    """Medidas finales de las reglas que pasan, quitando duplicados (Jaccard ≥ 0,7 con otra mejor)."""
    txt = {m["id"]: m["txt"] for m in meta}
    origen = {m["id"]: m.get("origen", "motor") for m in meta}
    ok = R[R.pasa].copy()
    # medida aproximada (vectorizada) para quedarse con las mejores antes de medir una a una
    d = np.where(ok.pA >= ok.bA, 1, -1)
    pc = np.where(d > 0, ok.pA, 1 - ok.pA)
    bc = np.where(d > 0, ok.bA, 1 - ok.bA)
    ok["gan_aprox"] = wilson_lo(pc, ok.nA * ok.r) - bc
    ok = ok.sort_values("gan_aprox", ascending=False).groupby("esc").head(MAX_MEDIR)
    out = []
    for esc, g in ok.groupby("esc"):
        y = Z[f"Y_{esc}"].to_numpy()
        cand = []
        for _, r in g.iterrows():
            gm = subs[int(r.gi)][2]
            m = gm & X[r.s1].to_numpy()
            if r.s2:
                m = m & X[r.s2].to_numpy()
            med = medir(m, y, Z, gm)
            cand.append((med["ganancia"], r, m, gm, med))
        cand.sort(key=lambda c: -c[0])
        elegidas = []
        for gan, r, m, gm, med in cand:
            if any((med["dir"] == e[4]["dir"]) and (m & e[2]).sum() / (m | e[2]).sum() >= JACCARD for e in elegidas):
                continue
            elegidas.append((gan, r, m, gm, med))
        for gan, r, m, gm, med in elegidas:
            caidas = aburridas(m, y, Z, gm, med["dir"], tabla)
            ejemplos = _ejemplos(Z, m, y, med["dir"])
            out.append(dict(tabla=tabla, escenario=esc, tipo_grupo=r.tipo, grupo=r.grupo, s1=r.s1, s2=r.s2,
                            senal=txt[r.s1] + (f" Y {txt[r.s2][0].lower()}{txt[r.s2][1:]}" if r.s2 else ""),
                            origen="+".join(sorted({origen[r.s1]} | ({origen[r.s2]} if r.s2 else set()))),
                            epos=bool(r.epos), q_descubrimiento=float(r.q_D),
                            antiguo=f"{r.pD:.0%} vs {r.bD:.0%} (n={int(r.nD)})",
                            reciente=f"{r.pT:.0%} vs {r.bT:.0%} (n={int(r.nT)})",
                            p_reciente=float(r.pval_T), explicaciones_que_la_tumban="; ".join(caidas),
                            ejemplos=ejemplos, **med))
    return pd.DataFrame(out)


def _ejemplos(Z, m, y, dir_, k=3):
    d = Z[m & ((y == 1) if dir_ > 0 else (y == 0))]
    if not len(d):
        return ""
    t = d.groupby("ean").agg(n=("F", "size"), desc=("ean", "first"), F=("F", "max"), r=("ratio", "median")).sort_values("n", ascending=False)
    return " | ".join(f"{e} ({int(r.n)} fotos, vendido/ref. {r.r:.2f})" for e, r in t.head(k).iterrows())


def cargar_tabla(tabla):
    Z = pd.read_parquet(CACHE / f"casos_{tabla}.parquet")
    X = pd.read_parquet(CACHE / f"senales_{tabla}.parquet").astype(bool)
    meta = json.loads((CACHE / f"senales_{tabla}.json").read_text(encoding="utf-8"))
    if tabla == "Y":
        keep = (Z.edad >= EDAD_MIN_Y).to_numpy()
        Z, X = Z[keep].reset_index(drop=True), X[keep].reset_index(drop=True)
        meta = [m for m in meta if m["id"] not in SENALES_BASE_Y]
        X = X[[m["id"] for m in meta]]
    return Z, X, meta


def anidados(T):
    """El mismo grupo y señales en «más» y «mucho más» (o «menos» y «mucho menos»): queda el extremo si gana casi lo
    mismo (≤ 5 puntos menos), si no, el moderado."""
    pares = {"alto": "muy_alto", "bajo": "muy_bajo"}
    quitar = set()
    clave = lambda r: (r.tipo_grupo, r.grupo, r.s1, r.s2, r.dir)  # noqa: E731
    idx = {(clave(r), r.escenario): i for i, r in T.iterrows()}
    for (k, esc), i in idx.items():
        if esc in pares and (k, pares[esc]) in idx:
            j = idx[(k, pares[esc])]
            if T.at[j, "ganancia"] >= T.at[i, "ganancia"] - 5:
                quitar.add(i)
            else:
                quitar.add(j)
    return T.drop(index=list(quitar)).reset_index(drop=True)


def main():
    resumen = {}
    for tabla in ("K", "Y"):
        Z, X, meta = cargar_tabla(tabla)
        R, subs = barrer(Z, X, meta, tabla)
        R = filtrar(R)
        T = anidados(tarjetas(R, Z, X, subs, meta, tabla))
        R.to_parquet(CACHE / f"barrido_{tabla}.parquet")
        T.drop(columns=["por_casa"]).assign(por_casa=T.por_casa.astype(str)).to_parquet(CACHE / f"reglas_{tabla}.parquet")
        resumen[tabla] = dict(casos=len(Z), senales=X.shape[1], grupos=len(subs), reglas_probadas=int(len(R)),
                              sueltas=int((R.s2 == "").sum()), parejas=int((R.s2 != "").sum()),
                              pasan_descubrimiento=int(R.pasa_D.sum()), pasan_reciente=int(R.pasa_T.sum()),
                              con_valor_anadido=int(R.pasa.sum()),
                              tarjetas_tras_quitar_duplicados=int(len(T)),
                              por_escenario={e: int((R.pasa & (R.esc == e)).sum()) for e in pl.UMBRALES})
        print(tabla, json.dumps(resumen[tabla], ensure_ascii=False))
    (CACHE / "resumen_reglas.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
