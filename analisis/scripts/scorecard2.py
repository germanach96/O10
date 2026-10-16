import numpy as np, pandas as pd
import statsmodels.api as sm
from sklearn.metrics import roc_auc_score
exec(open(S+'/scorecard.py').read().split("X = tramos(P)")[0]) if False else None
src = open('/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad/scorecard.py').read()
exec(src.split("X = tramos(P)")[0])
X = tramos(P); corte = 2026*12+1
A, B = P.F < corte, P.F >= corte
print('1) Robustez: calibrar en un periodo, medir AUC en el otro')
for y in ['sobre','infra']:
    for nm, tr, te in [('2025→2026', A, B), ('2026→2025', B, A)]:
        mdl = sm.Logit(P.loc[tr, y], sm.add_constant(X[tr])).fit_regularized(alpha=1.0, disp=0)
        pts = (mdl.params.drop('const')*10).round()
        print(f'   {y:6s} {nm}: AUC {roc_auc_score(P.loc[te, y], X[te] @ pts):.2f}')
pts = pd.read_pickle(S+'/scorecard_pts.pkl')
P['ps'] = X[pts['sobre'].index] @ pts['sobre']; P['pi'] = X[pts['infra'].index] @ pts['infra']
print('\n2) Por tipo de artículo (validación)')
for t, g in P[B].groupby('os'):
    print(f'   {"One Shot" if t else "Regular "}: n={len(g)}  AUC sobre {roc_auc_score(g.sobre, g.ps):.2f}  AUC infra {roc_auc_score(g.infra, g.pi):.2f}')
print('\n3) ¿Cuánto mejora el KPI si corrijo el Consensus según la puntuación? (factores aprendidos en 2025, aplicados en 2026)')
P['neto'] = P.ps - P.pi
cuts = np.unique(np.percentile(P.loc[A, 'neto'], [0, 20, 40, 60, 80, 100])); cuts[0], cuts[-1] = -1e9, 1e9
P['b'] = pd.cut(P.neto, cuts)
fac = P[A].groupby('b', observed=True).apply(lambda g: g.A3.sum()/g.c3.sum())
fac_med = P[A].groupby('b', observed=True).apply(lambda g: np.median(g.A3/g.c3))
print('   factor por tramo de (puntos sobre − puntos infra):', {str(k): round(v, 2) for k, v in fac.items()})
v = P[B].copy(); v['adj'] = v.c3 * v.b.map(fac).astype(float)
# objetivo relativo al Consensus: mensualizar no es posible aquí; WAPE de la ventana de 3M por código
for nm, f in [('Consensus', v.c3), ('Consensus corregido (factor agregado)', v.adj), ('Consensus corregido a medias', (v.c3 + v.adj)/2)]:
    print(f'   {nm:40s} WAPE3 {(f - v.A3).abs().sum()/v.A3.sum():.1%}  SPP3 {(v.A3.sum()-f.sum())/v.A3.sum():+.1%}')
for t, g in v.groupby('os'):
    print(f'   {"One Shot" if t else "Regular "}: Consensus WAPE3 {(g.c3-g.A3).abs().sum()/g.A3.sum():.1%} SPP {(g.A3.sum()-g.c3.sum())/g.A3.sum():+.0%}  ->  corregido WAPE3 {(g.adj-g.A3).abs().sum()/g.A3.sum():.1%} SPP {(g.A3.sum()-g.adj.sum())/g.A3.sum():+.0%}')
print('\n   validación por tramo: n, A/C real, factor aplicado')
for b, g in v.groupby('b', observed=True):
    print(f'     {str(b):18s} n={len(g):3d}  A/C real {g.A3.sum()/g.c3.sum():.2f}  mediana {np.median(g.A3/g.c3):.2f}   factor aprendido {fac[b]:.2f}')
