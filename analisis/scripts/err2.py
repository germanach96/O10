from base import *
from statsmodels.stats.proportion import proportion_confint as ci
E = pd.read_pickle(S+'/err.pkl')
# SPP3 pasado: de la foto F-4 (ventana F-3..F-1), ya conocido en F
past = E[['ean','F','y3','c3']].copy(); past['F'] = past.F + 4; past = past.rename(columns={'y3':'py3','c3':'pc3'})
D = E.merge(past, on=['ean','F'])
D = D[(~D.os) & (D.py3+D.pc3>0) & (D.y3+D.c3>0)]
D['pspp'] = (D.py3-D.pc3)/D.py3.where(D.py3>0, np.nan)
D['pspp'] = D.pspp.fillna(-9)   # actual 0 con consensus>0 => sobre-forecast extremo
print('fotos F', sorted(set(m(f) for f in D.F)), 'obs', len(D))
def tab(d, by, nm):
    print(f'\n{nm}')
    for b, g in d.groupby(by, observed=True):
        A, Cc = g.y3.sum(), g.c3.sum(); spp = (A-Cc)/A
        over = (g.c3 > g.y3); lo, hi = ci(over.sum(), len(g), method='wilson')
        grow = g.y3.sum()/g.y3_ly.sum()-1
        print(f'  {str(b):34s} n={len(g):4d}  SPP3 siguiente {spp:+.0%}  P(sobre-forecast otra vez)={over.mean():.0%} [{lo:.0%}-{hi:.0%}]  sell-in YoY {grow:+.0%}')
D['pb'] = pd.cut(D.pspp, [-1e9,-.3,-.05,.05,.3,1e9], labels=['SPP3 pasado < -30%','-30..-5%','±5% (en meta)','+5..30%','> +30%'])
tab(D, 'pb', 'Persistencia del bias: SPP3 de la foto F-4 (ya medido en F) -> SPP3 de la foto F')
D['gep'] = np.log((D.ep3+1)/(D.ep3_ly+1))
d2 = D[D.ep3_ly>=30].copy()
d2['combo'] = np.select([(d2.pspp<-.3)&(d2.gep<np.log(.9)), (d2.pspp<-.3)&(d2.gep>=np.log(.9)), (d2.pspp>.05)&(d2.gep<np.log(.9)), (d2.pspp>.05)&(d2.gep>=np.log(.9))],
                        ['SPP3<-30% y EPOS baja >10%','SPP3<-30% y EPOS no baja','SPP3>+5% y EPOS baja','SPP3>+5% y EPOS no baja'], 'otros')
tab(d2, 'combo', 'Pregunta del usuario: SPP3 muy negativo + EPOS bajando')
D.to_pickle(S+'/err_past.pkl')
