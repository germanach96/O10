from base import *
from statsmodels.stats.proportion import proportion_confint as ci
fc = FC[(FC.t <= T1)].copy()
fc['A'] = ACT[fc.ean.map(IX).to_numpy(), (fc.t - T0).to_numpy()]
fc['DAfin'] = DA[fc.ean.map(IX).to_numpy(), (fc.t - T0).to_numpy()]
fc['os'] = fc.ean.map(dict(zip(EANS, OS)))
fc = fc[fc.ean.isin([e for e in EANS])]
fc['tda_fut'] = fc.tda_fut.fillna(0); fc['cons'] = fc.cons.fillna(0)
fc['base'] = fc.cons - fc.tda_fut
fc = fc[(fc.cons > 0) | (fc.A > 0)]
pd.set_option('display.width', 250)
print('filas código x foto x mes (meses cerrados):', len(fc))
print('\n1) Peso de los DAs en el Consensus por horizonte:')
for h, g in fc[fc.h<=9].groupby('h'):
    print(f'   h={h}: DA/Consensus {g.tda_fut.sum()/g.cons.sum():+.0%}   filas con DA>0 {(g.tda_fut>0).mean():.0%}  DA<0 {(g.tda_fut<0).mean():.0%}')
print('\n2) ¿Se cumplen los DAs? (h=1..3) — por tamaño del DA respecto a la base')
d = fc[fc.h.between(1,3)].copy()
d['r'] = d.tda_fut / d.base.clip(lower=1)
d['cls'] = pd.cut(d.r, [-1e9, -0.05, 0.05, 0.5, 1.5, 1e9], labels=['DA negativo','sin DA (±5%)','DA 5-50% de la base','DA 50-150%','DA >150% (casi todo es DA)'])
for (o, c), g in d.groupby(['os','cls'], observed=True):
    A, C, B, D_ = g.A.sum(), g.cons.sum(), g.base.sum(), g.tda_fut.sum()
    over = (g.cons > g.A).mean(); lo, hi = ci((g.cons>g.A).sum(), len(g), method='wilson')
    print(f'   {"OS " if o else "REG"} {c:28s} n={len(g):5d}  SPP {((A-C)/A):+.0%}  A/base {A/B:.2f}  realizado del DA {(A-B)/D_ if abs(D_)>0 else np.nan:+.0%}  P(sobre-forecast) {over:.0%} [{lo:.0%}-{hi:.0%}]')
# 3) DA planificado vs DA final (cómo crece al acercarse)
print('\n3) DA planificado a h meses vs DA final del mes (agregado, todos los códigos)')
fa = fc.groupby(['h']).agg(plan=('tda_fut','sum'), fin=('DAfin','sum'))
for h, r in fa.iterrows():
    if h <= 9: print(f'   h={h}: DA final / DA planificado = {r.fin/r.plan:.2f}')
d.to_pickle(S+'/da.pkl'); fc.to_pickle(S+'/fc_all.pkl')
