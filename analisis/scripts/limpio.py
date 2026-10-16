"""Repite las señales que usan el Consensus: (a) solo fotos >= 2026.M02, (b) fotos viejas armonizadas con el factor de perímetro."""
from base import *
import json
from statsmodels.stats.proportion import proportion_confint as ci
from scipy.stats import fisher_exact
per = json.load(open(S+'/perimetro.json')); K = per['k']; SOLO = set(per['solo_nuevo'])
CORTE = 2026*12+1
fv = pd.read_pickle(S+'/fva.pkl')
viejo = fv.foto < CORTE
kk = fv.ean.map(K).fillna(1.0)
for c in ['cons','tda_fut','base','sys','sysda','ajuste']:
    fv[c+'_arm'] = np.where(viejo, fv[c]*kk, fv[c])
fv = fv[~(viejo & fv.ean.isin(SOLO))]
fv.to_pickle(S+'/fva_arm.pkl')
def consensus_err(fv, sufijo):
    c3 = fv[fv.h.between(1,3)].groupby(['foto','ean']).agg(c3=('cons'+sufijo,'sum'), da3=('tda_fut'+sufijo,'sum')).reset_index().rename(columns={'foto':'F'})
    X = pd.read_pickle(S+'/feats.pkl').merge(c3, on=['F','ean'])
    L = lambda a, b: np.log((a+1)/(b+1))
    X['gep'] = L(X.ep3, X.ep3_ly); X['gc'] = L(X.c3, X.y3_ly); X['gap'] = X.gc - X.gep
    return X
def informe(nm, d, cond, hit):
    s, b = d[cond], d[~cond]
    if len(s) < 10: print(f'   {nm}: n={len(s)} insuficiente'); return
    lo, hi = ci(hit[cond].sum(), len(s), method='wilson'); base = hit.mean()
    p = fisher_exact([[hit[cond].sum(), len(s)-hit[cond].sum()], [hit[~cond].sum(), len(b)-hit[~cond].sum()]])[1]
    print(f'   {nm:62s} {hit[cond].mean():.0%} [{lo:.0%}-{hi:.0%}] n={len(s):4d} ({s.ean.nunique()} cód.)  base {base:.0%}  lift {hit[cond].mean()-base:+.0%}  p={p:.0e}')
for titulo, filtro, suf in [('(a) SOLO FOTOS LIMPIAS 2026.M02-M06', lambda X: X.F >= CORTE, ''), ('(b) TODAS LAS FOTOS ARMONIZADAS', lambda X: X.F >= 0, '_arm')]:
    print(f'\n===== {titulo} =====')
    X = consensus_err(fv, suf); X = X[filtro(X) & (X.F + 3 <= T1)]
    reg = X[~X.os & (X.c3 + X.y3 > 0)]
    print(f'   SPP3 Consensus regular: {(reg.y3.sum()-reg.c3.sum())/reg.y3.sum():+.0%}   P(sobre-forecast) {(reg.c3>reg.y3).mean():.0%}   fotos {sorted(set(m(f) for f in reg.F))}')
    E = reg[(reg.edad>=27)&(reg.si12>=300)&(reg.y3_ly>=30)&reg.gep.notna()&(reg.ep3_ly>=30)]
    informe('S2  Consensus crece >50% más que el EPOS -> sobre-forecast', E, E.gap > np.log(1.5), E.c3 > E.y3)
    informe('S2b Consensus crece >20% menos que el EPOS -> infra-forecast', E, E.gap < np.log(.8), E.y3 > E.c3)
    informe('S2c Consensus ≈ EPOS (±20%) -> SPP3 dentro de ±20%', E, E.gap.abs() < np.log(1.2), ((E.y3-E.c3)/E.y3).abs() < .2)
    # S3: SPP3 pasado
    past = X[['ean','F','y3','c3']].copy(); past['F'] += 4; past = past.rename(columns={'y3':'py3','c3':'pc3'})
    D = reg.merge(past, on=['ean','F']); D = D[(D.py3+D.pc3>0) & (D.ep3_ly>=30)]
    D['pspp'] = ((D.py3-D.pc3)/D.py3.where(D.py3>0)).fillna(-9)
    informe('S3  SPP3 pasado < -30% y EPOS < -10% -> repite sobre-forecast', D, (D.pspp < -.3) & (D.gep < np.log(.9)), D.c3 > D.y3)
    informe('S3b SPP3 pasado < -30% (sin mirar EPOS) -> repite sobre-forecast', D, (D.pspp < -.3), D.c3 > D.y3)
    # S4 DAs mensual
    dd = fv if suf == '' else fv
    dm = dd[dd.h.between(1,3) & filtro(dd.rename(columns={'foto':'F'}))].copy()
    dm['c_'] = dm['cons'+suf]; dm['b_'] = dm['base'+suf]; dm['d_'] = dm['tda_fut'+suf]
    dm['r'] = dm.d_ / dm.b_.clip(lower=1)
    for tipo, g in dm.groupby('os'):
        informe(f'S4  DA >= 50% de la base ({"One Shot" if tipo else "Regular"}) -> sobre-forecast ese mes', g, g.r >= .5, g.c_ > g.A)
    # FVA por edad (regular)
    r = dm[~dm.os]
    print('   FVA (WAPE Sys+DA − WAPE Consensus), regular h=1..3:')
    for nm, g in r.groupby('edad_b', observed=True):
        A = g.A.sum(); wc = (g.c_-g.A).abs().sum()/A; ws = (g['sysda'+suf]-g.A).abs().sum()/A
        print(f'      {str(nm):10s} Consensus {wc:.0%}  Sys+DA {ws:.0%}  FVA {ws-wc:+.0%}  SPP Cons {(A-g.c_.sum())/A:+.0%}')
