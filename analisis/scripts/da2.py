from base import *
import statsmodels.api as sm
fc = pd.read_pickle(S+'/fc_all.pkl')
def capt(d, nm):
    d = d.copy(); d['Dp'] = d.tda_fut.clip(lower=0); d['Dn'] = d.tda_fut.clip(upper=0)
    X = d[['base','Dp','Dn']]; w = 1/np.sqrt(d.cons.abs()+d.A+10)
    r = sm.WLS(d.A, X, weights=w).fit(cov_type='cluster', cov_kwds={'groups': d.ean.astype('category').cat.codes})
    print(f'  {nm:34s} n={len(d):5d}  A = {r.params.base:.2f}·base + {r.params.Dp:.2f}·DA(+) + {r.params.Dn:.2f}·DA(-)   [IC DA+ {r.conf_int().loc["Dp",0]:.2f}-{r.conf_int().loc["Dp",1]:.2f}]')
print('Tasa de realización de los DAs (cuánto de cada unidad de DA aparece en los actuals):')
for (lo, hi) in [(1,1),(2,3),(4,6),(7,9)]:
    d = fc[fc.h.between(lo,hi)]
    capt(d[~d.os], f'REGULAR h={lo}-{hi}'); capt(d[d.os], f'ONE SHOT h={lo}-{hi}')
# DA final del mes (foto t+1) vs actual: ¿se reescribe el DA con lo que pasó?
d = fc[(fc.h==1)].drop_duplicates(['ean','t'])
d = d[d.DAfin.abs() > 0]
print(f'\nCorrelación DA final (foto t+1) con actual del mes: {np.corrcoef(d.DAfin, d.A)[0,1]:.2f}; con DA planificado a h=1: {np.corrcoef(d.DAfin, d.tda_fut)[0,1]:.2f}')
# Pull-forward: actual en t+1, t+2 tras un mes con DA grande, frente al consensus de la misma foto
print('\nEfecto resaca: error del consensus en los meses DESPUÉS de un mes con DA grande (misma foto)')
fc = fc.sort_values(['foto','ean','t'])
g = fc.groupby(['foto','ean'])
for lag in [1, 2]:
    fc[f'da_prev{lag}'] = g.tda_fut.shift(lag); fc[f'base_prev{lag}'] = g.base.shift(lag)
for lag in [1,2]:
    d = fc[fc.h.between(1+lag, 6) & ~fc.os & fc[f'da_prev{lag}'].notna()].copy()
    d['tras'] = np.where(d[f'da_prev{lag}'] > 0.5*d[f'base_prev{lag}'].clip(lower=1), 'tras DA grande', 'normal')
    d = d[d.tda_fut.abs() <= 0.05*d.base.clip(lower=1)]   # mes evaluado sin DA propio
    for c, gg in d.groupby('tras'):
        print(f'   {lag} mes(es) después, {c:15s} n={len(gg):5d}  SPP {(gg.A.sum()-gg.cons.sum())/gg.A.sum():+.0%}  A/Consensus {gg.A.sum()/gg.cons.sum():.2f}  P(sobre) {(gg.cons>gg.A).mean():.0%}')
