import numpy as np, pandas as pd
import statsmodels.api as sm
from statsmodels.stats.proportion import proportion_confint
from sklearn.metrics import roc_auc_score
S = '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad'
G = pd.read_pickle(S+'/indfoto.pkl'); corte = 2026*12+1
P = G[(G.F <= 2026*12+5) & (G.c3 >= 60) & ~((G.F < corte) & G.solo_nuevo)].copy()
P['ratio'] = P.c3 / np.maximum(np.expm1(P.log_vol12) / 4, 1)
P['long'] = P.c79 / np.maximum(P.c3, 1)
P['sobre'] = (P.A3 < 0.7*P.c3).astype(int); P['infra'] = (P.A3 > 1.3*P.c3).astype(int)
# indicadores en tramos con nombres de negocio (umbrales redondos)
def tramos(P):
    X = pd.DataFrame(index=P.index)
    r = P.ratio
    X['Cons/ritmo < 0.5x'] = r < .5; X['Cons/ritmo 0.5-0.8x'] = (r >= .5) & (r < .8)
    X['Cons/ritmo 1.25-2x'] = (r >= 1.25) & (r < 2); X['Cons/ritmo > 2x'] = r >= 2
    X['Cons cargado al inicio (m7-9 < 0.5x m1-3)'] = P.long < .5; X['Cons espera recuperación (m7-9 > 2x m1-3)'] = P.long > 2
    X['DA > 40% del Cons'] = P.c_da_share > .4; X['DA negativo'] = P.c_da_share < -.05
    X['Cortes 3M > 0.5 meses de venta'] = P.cut3 > .5; X['Cortes 3M > 2 meses de venta'] = P.cut3 > 2
    X['Cons crece >50% sobre EPOS'] = P.c_gap_e > np.log(1.5); X['Cons crece >20% bajo EPOS'] = P.c_gap_e < np.log(.8)
    X['Último mes ~0'] = P.s_last_avg < .15; X['Último mes > 1.5x media'] = P.s_last_avg > 1.5
    X['One Shots >40% en su PL'] = P.os_pl3 > .4
    X['One Shot'] = P.os == 1
    return X.astype(float)
X = tramos(P)
Dd, Dv = P.F < corte, P.F >= corte
res = {}
for y in ['sobre', 'infra']:
    mdl = sm.Logit(P.loc[Dd, y], sm.add_constant(X[Dd])).fit_regularized(alpha=1.0, disp=0)
    pts = (mdl.params.drop('const') * 10).round().astype(int)
    pts = pts[pts != 0]
    score = X[pts.index] @ pts
    P[f'pts_{y}'] = score
    print(f'\n================ SCORECARD "{y.upper()}-FORECAST > 30%" (puntos calibrados en {len(P[Dd])} casos 2025.M09-2026.M01)')
    for k, v in pts.sort_values(ascending=False).items(): print(f'   {v:+3d}  {k}')
    auc = roc_auc_score(P.loc[Dv, y], score[Dv])
    print(f'   AUC en validación (2026.M02-M06, {Dv.sum()} casos): {auc:.2f}')
    qs = np.unique(np.percentile(score[Dd], [0, 20, 40, 60, 80, 100]))
    cuts = [-1e9] + list(qs[1:-1]) + [1e9]
    P['b'] = pd.cut(score, cuts)
    print('   puntos          | descubrimiento            | VALIDACIÓN')
    for b, g in P.groupby('b', observed=True):
        gd, gv = g[g.F < corte], g[g.F >= corte]
        if len(gv) == 0: continue
        a, c = proportion_confint(int(gv[y].sum()), len(gv), method='wilson')
        print(f'   {str(b):15s} | {gd[y].mean():4.0%} n={len(gd):3d} A/C {gd.A3.sum()/gd.c3.sum():.2f} | {gv[y].mean():4.0%} [{a:.0%}-{c:.0%}] n={len(gv):3d} ({gv.ean.nunique()} cód.) A/C {gv.A3.sum()/gv.c3.sum():.2f}')
    res[y] = pts
P.to_pickle(S+'/scorecard.pkl'); pd.to_pickle(res, S+'/scorecard_pts.pkl')
