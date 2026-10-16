from base import *
from statsmodels.stats.proportion import proportion_confint as ci
import statsmodels.formula.api as smf
fc = pd.read_pickle(S+'/fva.pkl')
fc = fc.sort_values(['ean','t','foto'])
g = fc.groupby(['ean','t'])
fc['cons_prev'] = g.cons.shift(1); fc['foto_prev'] = g.foto.shift(1)
fc['base_prev'] = g.base.shift(1)
d = fc[(fc.foto_prev == fc.foto - 1) & fc.h.between(1,3) & ~fc.os].copy()
d = d[(d.cons_prev > 20) | (d.cons > 20)]
d['rev'] = np.log((d.base + 1)/(d.base_prev + 1))     # revisión de la base (sin DA) de una foto a la siguiente
d['err'] = np.log((d.A + 1)/(d.cons + 1))
d['rb'] = pd.cut(d.rev, [-10, np.log(.7), np.log(.9), np.log(1/.9*0+1.1)-0.0001-np.log(1.1)+np.log(0.99999), np.log(1.1), np.log(1/.7), 10], labels=['recorte >30%','recorte 10-30%','±','x','sube 10-43%','sube >43%'])
d['rb'] = pd.cut(np.expm1(d.rev), [-1, -.3, -.1, .1, .3, 100], labels=['base recortada >30%','recortada 10-30%','estable ±10%','subida 10-30%','subida >30%'])
print('Revisión de la base (Consensus sin DA) respecto a la foto anterior -> error final del Consensus (regular, h=1..3)')
for b, gg in d.groupby('rb', observed=True):
    A, C = gg.A.sum(), gg.cons.sum(); lo, hi = ci((gg.cons>gg.A).sum(), len(gg), method='wilson')
    print(f'   {b:22s} n={len(gg):5d}  SPP {((A-C)/A):+.0%}  P(sobre-forecast) {(gg.cons>gg.A).mean():.0%} [{lo:.0%}-{hi:.0%}]  mediana log(A/C) {gg.err.median():+.2f}')
r = smf.wls('err ~ rev', d, weights=np.sqrt(d.cons+d.A+1)).fit(cov_type='cluster', cov_kwds={'groups': d.ean.astype('category').cat.codes})
print(f'   pendiente err ~ rev = {r.params.rev:+.2f} (p={r.pvalues.rev:.3f})  -> >0 = el consensus se queda corto en la dirección de la revisión (infra-reacción)')
