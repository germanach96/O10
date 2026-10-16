import numpy as np, pandas as pd
import statsmodels.api as sm
from sklearn.metrics import roc_auc_score
from statsmodels.stats.proportion import proportion_confint
src = open('/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad/scorecard.py').read()
exec(src.split("X = tramos(P)")[0])
P = P[P.os == 0].copy()
X = tramos(P).drop(columns=['One Shot']); corte = 2026*12+1
A, B = P.F < corte, P.F >= corte
P['tam'] = np.where(P.c3 >= 1500, 'grande (Cons3M ≥1500)', np.where(P.c3 >= 300, 'medio (300-1500)', 'pequeño (<300)'))
out = {}
for y in ['sobre', 'infra']:
    mdl = sm.Logit(P.loc[A, y], sm.add_constant(X[A])).fit_regularized(alpha=1.0, disp=0)
    pts = (mdl.params.drop('const')*10).round().astype(int); pts = pts[pts != 0]
    P['p_'+y] = X[pts.index] @ pts; out[y] = pts
    mdl2 = sm.Logit(P.loc[B, y], sm.add_constant(X[B])).fit_regularized(alpha=1.0, disp=0)
    pts2 = (mdl2.params.drop('const')*10).round()
    print(f'\nSCORECARD REGULAR "{y.upper()}-FORECAST >30%"  AUC 2025→2026 {roc_auc_score(P.loc[B,y], P.loc[B,"p_"+y]):.2f} | 2026→2025 {roc_auc_score(P.loc[A,y], X[A] @ pts2):.2f}')
    for k, v in pts.sort_values(ascending=False).items(): print(f'   {v:+3d}  {k}   (calibrado en 2026: {int(pts2.get(k, 0)):+d})')
    cuts = [-1e9, -10, 0, 10, 20, 1e9] if y == 'sobre' else [-1e9, -10, 0, 8, 15, 1e9]
    P['b'] = pd.cut(P['p_'+y], cuts)
    for b, g in P.groupby('b', observed=True):
        gd, gv = g[g.F < corte], g[g.F >= corte]
        a, c = proportion_confint(int(gv[y].sum()), max(len(gv),1), method='wilson')
        print(f'   {str(b):16s} 2025: {gd[y].mean():4.0%} (n={len(gd):3d}) | 2026: {gv[y].mean():4.0%} [{a:.0%}-{c:.0%}] (n={len(gv):3d}, {gv.ean.nunique()} cód.)  mediana A/C 2026 {np.median(gv.A3/gv.c3) if len(gv) else np.nan:.2f}')
pd.to_pickle(out, S+'/scorecard_reg_pts.pkl')
# corrección por (puntos sobre − puntos infra) x tamaño
P['neto'] = P.p_sobre - P.p_infra
P['nb'] = pd.cut(P.neto, [-1e9, -15, 0, 15, 30, 1e9])
def aplicar(tr, te):
    fac = tr.groupby(['nb','tam'], observed=True).apply(lambda g: (g.A3.sum()/g.c3.sum()) if len(g) >= 15 else np.nan)
    f = pd.Series([fac.get((b, t), np.nan) for b, t in zip(te.nb, te.tam)], index=te.index).fillna(tr.A3.sum()/tr.c3.sum())
    return te.c3 * f, fac
print('\nCORRECCIÓN DEL CONSENSUS (regular), factor por tramo de puntos x tamaño, aprendido en un periodo y aplicado al otro:')
for nm, tr, te in [('2025→2026', P[A], P[B]), ('2026→2025', P[B], P[A])]:
    adj, fac = aplicar(tr, te)
    for lab, f in [('Consensus', te.c3), ('corregido', adj), ('corregido a medias', (te.c3 + adj)/2)]:
        print(f'   {nm} {lab:20s} WAPE3 {(f-te.A3).abs().sum()/te.A3.sum():.1%}  SPP3 {(te.A3.sum()-f.sum())/te.A3.sum():+.1%}')
adj, fac = aplicar(P[A], P[B])
print('\n   factores aprendidos en 2025 (A/C):'); print(fac.unstack().round(2).to_string())
P.to_pickle(S+'/scorecard_reg.pkl')
