from base import *
from scipy import stats
# --- 1. Agregado: correlación cruzada sell-in vs EPOS a nivel brand (regular y todo), log, sin estacionalidad por diferencia YoY
ok = ~np.isnan(EPOS).all(0)
km = np.where(ok)[0]
print('meses con EPOS', m(MESES[km[0]]), '..', m(MESES[km[-1]]), len(km))
def serie(mask):
    a = ACT[mask][:, km].sum(0); e = np.nansum(EPOS[mask][:, km], 0)
    return a, e
print('\nRatio sell-in / EPOS por año fiscal-ish (cobertura EPOS):')
for nombre, mask in [('Regular', ~OS), ('One Shot', OS), ('Todo', np.ones(len(OS),bool))]:
    a, e = serie(mask)
    print(f'  {nombre:9s} sell-in {a.sum():>10,.0f}  EPOS {e.sum():>10,.0f}  ratio {a.sum()/e.sum():.2f}')
# correlación cruzada de crecimiento mes a mes (log-diff) — confundido por estacionalidad, así que usamos variación vs media móvil
print('\nCorrelación cruzada (Regular, por código, two-way demeaned log1p): corr(EPOS_t, SellIn_{t+k})')
mask = (~OS) & (np.nansum(EPOS[:, km] > 0, 1) >= 12)
Ae = np.log1p(ACT[mask][:, km]); Ee = np.log1p(EPOS[mask][:, km])
def dm(X):
    X = X - np.nanmean(X, 1, keepdims=True); X = X - np.nanmean(X, 0, keepdims=True); return X
Ae, Ee = dm(Ae), dm(Ee)
for lag in range(-4, 5):
    if lag >= 0: x, y = Ee[:, :Ee.shape[1]-lag], Ae[:, lag:]
    else: x, y = Ee[:, -lag:], Ae[:, :lag]
    v = ~np.isnan(x) & ~np.isnan(y)
    r = np.corrcoef(x[v], y[v])[0,1]
    print(f'  k={lag:+d}  r={r:+.3f}  n={v.sum()}')
print('  códigos usados', mask.sum())
# autocorrelación sell-in y EPOS (persistencia)
for nm, X in [('sell-in', Ae), ('EPOS', Ee)]:
    x, y = X[:, :-1], X[:, 1:]; v = ~np.isnan(x)&~np.isnan(y)
    print(f'  autocorr lag1 {nm}: {np.corrcoef(x[v], y[v])[0,1]:+.3f}')
