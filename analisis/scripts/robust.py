from base import *
from statsmodels.stats.proportion import proportion_confint as ci
from scipy.stats import fisher_exact
def informe(nm, d, cond, hit, mes_col):
    d = d.copy(); d['c'] = cond.loc[d.index]; d['h'] = hit.loc[d.index]
    s, b = d[d.c], d[~d.c]
    base = d.h.mean()
    lo, hi = ci(s.h.sum(), len(s), method='wilson')
    meses = sorted(d[mes_col].unique()); mid = meses[len(meses)//2]
    p1 = s[s[mes_col] < mid].h.mean(); p2 = s[s[mes_col] >= mid].h.mean()
    b1 = d[d[mes_col] < mid].h.mean(); b2 = d[d[mes_col] >= mid].h.mean()
    nov = s[s[mes_col] % 3 == 0]   # sin solapes de ventanas de 3 meses
    # por código: fracción de códigos donde la señal acierta más que el azar
    pc = s.groupby('ean').h.mean()
    odds, p = fisher_exact([[s.h.sum(), len(s)-s.h.sum()], [b.h.sum(), len(b)-b.h.sum()]])
    print(f'\n{nm}\n   cumple {s.h.mean():.0%} [{lo:.0%}-{hi:.0%}] n={len(s)} ({s.ean.nunique()} códigos)   tasa base {base:.0%}   lift {s.h.mean()-base:+.0%}   Fisher p={p:.1e}'
          f'\n   1ª mitad {p1:.0%} (base {b1:.0%})   2ª mitad {p2:.0%} (base {b2:.0%})   sin solapes {nov.h.mean():.0%} n={len(nov)}   códigos con acierto >50%: {(pc>.5).mean():.0%}')
# S1
B = pd.read_pickle(S+'/base_epos.pkl')
informe('S1. EPOS YoY 3M < -30% -> sell-in YoY 3M siguientes baja', B, B.gep < np.log(.7), B.g < 0, 'F')
informe('S1b. EPOS YoY 3M > +10% -> sell-in YoY 3M siguientes NO baja', B, B.gep > np.log(1.1), B.g >= 0, 'F')
# S2
E = pd.read_pickle(S+'/err.pkl')
E = E[(~E.os) & (E.edad>=27) & (E.si12>=300) & (E.y3_ly>=30) & E.gep.notna() & (E.ep3_ly>=30) & (E.c3+E.y3>0)].copy()
E['gap'] = E.gc - E.gep
informe('S2. Consensus asume crecer >50% más que el EPOS -> sobre-forecast SPP3', E, E.gap > np.log(1.5), E.c3 > E.y3, 'F')
informe('S2b. Consensus asume crecer >20% MENOS que el EPOS -> infra-forecast SPP3', E, E.gap < np.log(.8), E.y3 > E.c3, 'F')
# S3
Dp = pd.read_pickle(S+'/err_past.pkl'); Dp = Dp[Dp.ep3_ly >= 30].copy()
informe('S3. SPP3 pasado < -30% y EPOS YoY < -10% -> vuelve a sobre-forecast', Dp, (Dp.pspp < -.3) & (Dp.gep < np.log(.9)), Dp.c3 > Dp.y3, 'F')
# S4 (mensual)
da = pd.read_pickle(S+'/da.pkl'); da = da[~da.os].copy(); da['F'] = da.foto
informe('S4. DA >= 50% de la base (regular) -> sobre-forecast ese mes', da, da.r >= .5, da.cons > da.A, 'F')
da2 = pd.read_pickle(S+'/da.pkl'); da2 = da2[da2.os].copy(); da2['F'] = da2.foto
informe('S4b. DA >= 50% de la base (one shot) -> sobre-forecast ese mes', da2, da2.r >= .5, da2.cons > da2.A, 'F')
# S5
O = pd.read_pickle(S+'/ordenes.pkl'); X = pd.read_pickle(S+'/feats.pkl')
O = O.merge(X[['ean','F','ep3','ep3_ly']].rename(columns={'F':'t'}), on=['ean','t'], how='left'); O = O[O.ep3_ly >= 30].reset_index(drop=True)
O['epg'] = (O.ep3+1)/(O.ep3_ly+1)-1
informe('S5. Sell-through 3M > 1.2 y EPOS YoY < -10% -> el mes siguiente sell-in < 70% de su media 12M', O, (O.st3 > 1.2) & (O.epg < -.1), O.ratio < .7, 't')
