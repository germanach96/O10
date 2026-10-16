import pandas as pd, numpy as np, statsmodels.formula.api as smf
from statsmodels.stats.proportion import proportion_confint as ci
X = pd.read_pickle('/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad/feats.pkl')
L = lambda a, b: np.log((a+1)/(b+1))
X['g'] = L(X.y3, X.y3_ly); X['gs'] = L(X.si3, X.si3_ly); X['gep'] = L(X.ep3, X.ep3_ly)
X['gs12'] = L(X.si12, X.si12_ly)
X['cs'] = np.log(((X.si3+1)/(X.ep3+1)) / ((X.si12+1)/(X.ep12+1)))
base = X[(~X.os) & (X.edad >= 27) & (X.si12 >= 300) & (X.y3_ly >= 30) & X.gep.notna() & (X.ep3_ly>=30) & X.ep12.notna()].copy()
print('obs', len(base), 'códigos', base.ean.nunique(), 'meses F', base.F.nunique())
for f in ['g ~ gs', 'g ~ gep', 'g ~ gs + gep', 'g ~ gs + gep + cs', 'g ~ gs + gep + cs + C(F)']:
    r = smf.wls(f, base, weights=np.sqrt(base.si12)).fit(cov_type='cluster', cov_kwds={'groups': base.ean.astype('category').cat.codes})
    print(f'{f:28s} R2={r.rsquared:.3f} ', '  '.join(f'{k}={v:+.2f}(p={r.pvalues[k]:.3f})' for k, v in r.params.items() if not k.startswith('C(') and k!='Intercept'))
# señal: EPOS YoY 3M vs sell-in YoY futuro
print('\nBins de EPOS YoY (3M pasados) -> sell-in YoY 3M futuros (ponderado por volumen):')
base['ge_bin'] = pd.cut(np.expm1(base.gep), [-1, -.3, -.1, .1, .3, 10], labels=['< -30%','-30..-10%','±10%','+10..30%','> +30%'])
for b, d in base.groupby('ge_bin', observed=True):
    agg = d.y3.sum()/d.y3_ly.sum()-1; down = (d.g<0).mean(); lo, hi = ci((d.g<0).sum(), len(d), method='wilson')
    print(f'  EPOS {b:10s} n={len(d):4d}  sell-in futuro agregado {agg:+.0%}  P(baja)={down:.0%} [{lo:.0%}-{hi:.0%}]')
print('\nBins de sell-in YoY (3M pasados) -> sell-in YoY 3M futuros:')
base['gs_bin'] = pd.cut(np.expm1(base.gs), [-1, -.3, -.1, .1, .3, 100], labels=['< -30%','-30..-10%','±10%','+10..30%','> +30%'])
for b, d in base.groupby('gs_bin', observed=True):
    agg = d.y3.sum()/d.y3_ly.sum()-1; down = (d.g<0).mean(); lo, hi = ci((d.g<0).sum(), len(d), method='wilson')
    print(f'  SI   {b:10s} n={len(d):4d}  sell-in futuro agregado {agg:+.0%}  P(baja)={down:.0%} [{lo:.0%}-{hi:.0%}]')
print('\nCombinado: EPOS y sell-in pasados ambos < -10% vs ambos > +10%:')
for nm, q in [('ambos bajan', (base.gep<np.log(.9))&(base.gs<np.log(.9))), ('EPOS baja, SI sube', (base.gep<np.log(.9))&(base.gs>np.log(1.1))), ('EPOS sube, SI baja', (base.gep>np.log(1.1))&(base.gs<np.log(.9))), ('ambos suben', (base.gep>np.log(1.1))&(base.gs>np.log(1.1)))]:
    d = base[q]; lo, hi = ci((d.g<0).sum(), len(d), method='wilson')
    print(f'  {nm:20s} n={len(d):4d}  futuro agregado {d.y3.sum()/d.y3_ly.sum()-1:+.0%}  P(baja)={(d.g<0).mean():.0%} [{lo:.0%}-{hi:.0%}]')
base.to_pickle('/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad/base_epos.pkl')
