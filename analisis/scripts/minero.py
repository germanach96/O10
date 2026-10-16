"""Minería de reglas: descubrir en un conjunto, confirmar en otro (BH-FDR)."""
import numpy as np, pandas as pd
from statsmodels.stats.proportion import proportion_confint
from scipy.stats import binomtest
from statsmodels.stats.multitest import multipletests
CAT = ['seg', 'brand', 'mes_obj']
BIN = ['os', 'local', 'cut_any6']
EXCL = {'F','ean','i','y3','y3_ly','Y_yoy3','Y_vs_last3','Y_big1','Y_ratio1','s12','log_vol12_raw'}
QS = [10, 20, 30, 70, 80, 90]
def wilson_lb(h, n):
    p = h / np.maximum(n, 1); z = 1.96
    return (p + z*z/(2*n) - z*np.sqrt(p*(1-p)/n + z*z/(4*n*n))) / (1 + z*z/n)
def condiciones(D, feats):
    """Lista de (nombre, feature, función) con umbrales de cuantiles del conjunto de descubrimiento."""
    conds = []
    for f in feats:
        if f in CAT:
            for v in D[f].dropna().unique():
                conds.append((f'{f} = {v}', f, ('eq', v)))
        elif f in BIN:
            conds.append((f'{f} = 1', f, ('eq', 1.0))); conds.append((f'{f} = 0', f, ('eq', 0.0)))
        else:
            x = D[f].dropna()
            if x.nunique() < 4: continue
            for q in QS:
                t = float(np.percentile(x, q))
                conds.append((f'{f} {"<=" if q < 50 else ">="} {t:.3g}', f, ('le' if q < 50 else 'ge', t)))
    seen = set(); out = []
    for c in conds:
        if c[0] not in seen: seen.add(c[0]); out.append(c)
    return out
def evaluar(D, conds):
    M = np.zeros((len(D), len(conds)), bool)
    for j, (_, f, (op, t)) in enumerate(conds):
        x = D[f].to_numpy()
        if op == 'eq': M[:, j] = (x == t)
        elif op == 'le': M[:, j] = (x <= t)
        else: M[:, j] = (x >= t)
    return M
def minar(Dd, Dv, y, feats, min_n=40, min_cod=12, top=400, nombre=''):
    conds = condiciones(Dd, feats)
    Md, Mv = evaluar(Dd, conds), evaluar(Dv, conds)
    yd, yv = Dd[y].to_numpy().astype(bool), Dv[y].to_numpy().astype(bool)
    bd, bv = yd.mean(), yv.mean()
    fe = np.array([c[1] for c in conds])
    Cf = Md.astype(np.float32); Cy = (Md & yd[:, None]).astype(np.float32)
    n2 = Cf.T @ Cf; h2 = Cf.T @ Cy             # pares (incluye diagonal = condiciones sueltas)
    lb = wilson_lb(h2, n2); lb[n2 < min_n] = 0; lb[(fe[:, None] == fe[None, :]) & ~np.eye(len(conds), dtype=bool)] = 0
    iu = np.triu_indices(len(conds))
    cand = sorted(zip(lb[iu], iu[0], iu[1]), reverse=True)[:top]
    reglas = []
    for _, a, b in cand:
        reglas.append(tuple(sorted({a, b})))
    # tríos: ampliar los 150 mejores pares
    for _, a, b in cand[:150]:
        base = Md[:, a] & Md[:, b]
        n3 = (base[:, None] & Md).sum(0); h3 = (base[:, None] & Md & yd[:, None]).sum(0)
        l3 = wilson_lb(h3, n3); l3[n3 < min_n] = 0; l3[np.isin(fe, [fe[a], fe[b]])] = 0
        for c in np.argsort(-l3)[:3]:
            if l3[c] > lb[a, b] + 0.02: reglas.append(tuple(sorted({a, b, c})))
    reglas = list(dict.fromkeys(reglas))
    out = []
    for r in reglas:
        md = Md[:, r].all(1); mv = Mv[:, r].all(1)
        nd, hd, nv, hv = md.sum(), (md & yd).sum(), mv.sum(), (mv & yv).sum()
        cd = Dd.ean[md].nunique(); cv = Dv.ean[mv].nunique()
        if nd < min_n or cd < min_cod: continue
        p = binomtest(int(hv), int(nv), bv, alternative='greater').pvalue if nv >= 10 else 1.0
        out.append(dict(regla=' Y '.join(conds[j][0] for j in r), k=len(r), mask_d=md, mask_v=mv, n_desc=int(nd), cod_desc=int(cd), p_desc=hd/nd,
                        n_val=int(nv), cod_val=int(cv), p_val=hv/nv if nv else np.nan, p=p, idx=r))
    R = pd.DataFrame(out)
    if R.empty: return R, bd, bv, conds
    R['q'] = multipletests(R.p, method='fdr_bh')[1]
    R['base_desc'] = bd; R['base_val'] = bv
    R['lb_val'] = [proportion_confint(int(round(p*n)), n, method='wilson')[0] if n else 0 for p, n in zip(R.p_val.fillna(0), R.n_val)]
    R['confirmada'] = (R.q < 0.05) & (R.p_val >= bv + 0.10) & (R.cod_val >= 8)
    return R.sort_values(['confirmada', 'p_val'], ascending=False), bd, bv, conds

def diversas(R, n=10, max_jac=0.5):
    """Elige reglas confirmadas variadas: descarta las que cubren casi las mismas filas que una ya elegida."""
    sel = []
    for _, r in R[R.confirmada].sort_values('lb_val', ascending=False).iterrows():
        md = r.mask_d
        if all((md & s.mask_d).sum() / max((md | s.mask_d).sum(), 1) < max_jac for s in sel):
            sel.append(r)
        if len(sel) >= n: break
    return pd.DataFrame(sel)
