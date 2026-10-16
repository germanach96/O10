from base import *
import json
from statsmodels.stats.proportion import proportion_confint as ci
exec(open(S+'/limpio.py').read().split("def informe")[0].split("fv.to_pickle")[0])
src = open(S+'/limpio.py').read()
exec(src[src.index('def consensus_err'):src.index('def informe')])
def fila(nm, d, cond, hit, A, C, extra=''):
    s = d[cond]; lo, hi = ci(hit[cond].sum(), len(s), method='wilson')
    spp = (s[A].sum() - s[C].sum())/s[A].sum()
    print(f'{nm:58s} {hit[cond].mean():.0%} [{lo:.0%}-{hi:.0%}]  base {hit.mean():.0%}  n={len(s)} ({s.ean.nunique()} cód.)  SPP3 del grupo {spp:+.0%}  {extra}')
X = consensus_err(fv, '_arm'); X = X[(X.F+3 <= T1)]
reg = X[~X.os & (X.c3+X.y3>0)]
E = reg[(reg.edad>=27)&(reg.si12>=300)&(reg.y3_ly>=30)&reg.gep.notna()&(reg.ep3_ly>=30)]
print('Muestra regular madura con EPOS (armonizada):', len(E), f' SPP3 global {(E.y3.sum()-E.c3.sum())/E.y3.sum():+.0%}')
for nm, cnd in [('Consensus crece >50% más que el EPOS', E.gap > np.log(1.5)), ('Consensus crece 20-50% más que el EPOS', (E.gap > np.log(1.2)) & (E.gap <= np.log(1.5))),
                ('Consensus ≈ EPOS (±20%)', E.gap.abs() <= np.log(1.2)), ('Consensus crece >20% menos que el EPOS', E.gap < np.log(.8))]:
    fila(nm, E, cnd, E.c3 > E.y3, 'y3', 'c3', '(acierto = sobre-forecast)')
