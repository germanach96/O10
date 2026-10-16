from base import *
import statsmodels.api as sm
fc = pd.read_pickle(S+'/fva_arm.pkl')
def capt(d, nm):
    d = d.copy(); d['Dp'] = d.tda_fut.clip(lower=0); d['Dn'] = d.tda_fut.clip(upper=0)
    X = d[['base','Dp','Dn']]; w = 1/np.sqrt(d.cons.abs()+d.A+10)
    r = sm.WLS(d.A, X, weights=w).fit(cov_type='cluster', cov_kwds={'groups': d.ean.astype('category').cat.codes})
    ci_ = r.conf_int()
    print(f'  {nm:30s} n={len(d):5d}  A = {r.params.base:.2f}·base + {r.params.Dp:.2f}·DA(+) [{ci_.loc["Dp",0]:.2f}-{ci_.loc["Dp",1]:.2f}] + {r.params.Dn:.2f}·DA(-) [{ci_.loc["Dn",0]:.2f}-{ci_.loc["Dn",1]:.2f}]')
print('Realización de DAs, SOLO fotos limpias (>= 2026.M02):')
c = fc[fc.foto >= 2026*12+1]
for lo, hi in [(1,3),(4,6)]:
    d = c[c.h.between(lo,hi)]
    capt(d[~d.os], f'Regular h={lo}-{hi}'); capt(d[d.os], f'One Shot h={lo}-{hi}')
print('\nAgregado (h=1..3, fotos limpias): DA positivo planificado vs lo que cubre')
d = c[c.h.between(1,3)]
for tipo, g in d.groupby('os'):
    gg = g[g.tda_fut > 0.5*g.base.clip(lower=1)]
    print(f'  {"One Shot" if tipo else "Regular "}: meses con DA dominante n={len(gg)}  Σactual {gg.A.sum():,.0f}  Σbase {gg.base.sum():,.0f}  ΣDA {gg.tda_fut.sum():,.0f}  -> (A−base)/DA = {(gg.A.sum()-gg.base.sum())/gg.tda_fut.sum():.2f}   A/Consensus {gg.A.sum()/gg.cons.sum():.2f}')
