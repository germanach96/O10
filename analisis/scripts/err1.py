from base import *
import statsmodels.formula.api as smf
from statsmodels.stats.proportion import proportion_confint as ci
X = pd.read_pickle(S+'/feats.pkl')
# Consensus de cada foto para F+1..F+3 y F+4..F+6, DA futuro
add = []
for F in FOTOS:
    if F+3 > T1: continue
    d = pd.DataFrame({'ean': EANS, 'F': F, 'c3': cons(F,1,3), 'c6': cons(F,4,6) if F+6<=T1 else np.nan,
                      'da3': dafut(F,1,3), 'c_prev3': cons(F-1,2,4) if F-1 in FOTOS else np.nan, 'en': EN_FOTO[F]})
    add.append(d)
CC = pd.concat(add)
E = X.merge(CC, on=['ean','F'])
E = E[E.en]
L = lambda a, b: np.log((a+1)/(b+1))
E['spp3'] = (E.y3 - E.c3) / E.y3.where(E.y3>0)
E['gep'] = L(E.ep3, E.ep3_ly); E['gs'] = L(E.si3, E.si3_ly); E['gc'] = L(E.c3, E.y3_ly)   # crecimiento implícito del consensus
E['err'] = L(E.y3, E.c3)   # log(actual/consensus): <0 = sobre-forecast
E.to_pickle(S+'/err.pkl')
def tab(d, by, nm):
    print(f'\n{nm}')
    for b, g in d.groupby(by, observed=True):
        A, Cc = g.y3.sum(), g.c3.sum(); spp = (A-Cc)/A; wape = (g.y3-g.c3).abs().sum()/A
        over = (g.c3 > g.y3); lo, hi = ci(over.sum(), len(g), method='wilson')
        print(f'  {str(b):22s} n={len(g):4d}  SPP3 {spp:+.0%}  WAPE3 {wape:.0%}  P(sobre-forecast)={over.mean():.0%} [{lo:.0%}-{hi:.0%}]')
reg = E[(~E.os) & (E.c3+E.y3 > 0)]
tab(reg, pd.Series('todos', index=reg.index), 'Regular, todas las fotos 25.M09-26.M06 (base)')
m1 = reg[(reg.edad>=27)&(reg.si12>=300)&(reg.y3_ly>=30)&reg.gep.notna()&(reg.ep3_ly>=30)].copy()
tab(m1, pd.Series('maduros con EPOS', index=m1.index), 'Muestra con EPOS YoY')
m1['b'] = pd.cut(np.expm1(m1.gep), [-1,-.3,-.1,.1,10], labels=['EPOS < -30%','EPOS -30..-10%','EPOS ±10%','EPOS > +10%'])
tab(m1, 'b', 'EPOS YoY 3M pasados -> error del Consensus en los 3 meses siguientes')
# brecha de ambición: crecimiento implícito del consensus menos crecimiento EPOS
m1['gap'] = m1.gc - m1.gep
m1['gb'] = pd.cut(np.expm1(m1.gap), [-1,-.2,0,.2,.5,100], labels=['Cons < EPOS -20%','Cons ≈ EPOS (-20..0)','Cons > EPOS 0..20%','Cons > EPOS 20..50%','Cons > EPOS > +50%'])
tab(m1, 'gb', 'Brecha: crecimiento YoY que asume el Consensus vs crecimiento YoY del EPOS')
for f in ['err ~ gep', 'err ~ gc', 'err ~ gc + gep', 'err ~ gc + gep + gs', 'err ~ gc + gep + gs + C(F)']:
    r = smf.wls(f, m1, weights=np.sqrt(m1.si12)).fit(cov_type='cluster', cov_kwds={'groups': m1.ean.astype('category').cat.codes})
    print(f'{f:30s} R2={r.rsquared:.3f} ', '  '.join(f'{k}={v:+.2f}(p={r.pvalues[k]:.3f})' for k, v in r.params.items() if not k.startswith('C(')))
