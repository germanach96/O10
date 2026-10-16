from base import *
from statsmodels.stats.proportion import proportion_confint as ci
fc = pd.read_pickle(S+'/fc_all.pkl'); sy = pd.read_pickle(S+'/sysfc.pkl')
D = fc.merge(sy[['ean','t','foto','sys','flag','seg_foto','init','prom']], on=['ean','t','foto'], how='left')
D[['sys','init','prom']] = D[['sys','init','prom']].fillna(0); D['flag'] = D.flag.fillna('vacío')
D['sysda'] = (D.sys + D.tda_fut).clip(lower=0)
D['ajuste'] = D.cons - D.sysda
D['edad'] = D.foto - D.ean.map(dict(zip(EANS, PRIMER)))
D['edad_b'] = pd.cut(D.edad, [-100, 6, 12, 24, 1000], labels=['A1 1-6','A1 7-12','Año 2','Año 3+'])
D['brand'] = D.ean.map(dict(zip(EANS, BRAND)))
D['tipo'] = np.where(D.os, 'One Shot', 'Regular')
D.to_pickle(S+'/fva.pkl')
def tab(d, by, nm):
    print(f'\n{nm}  (h=1..3, fotos 25.M09-26.M06)')
    print(f'   {"":24s} {"n":>5s} {"vol":>8s}  {"WAPE Cons":>9s} {"WAPE Sys+DA":>11s} {"FVA":>6s}  {"SPP Cons":>8s} {"SPP Sys+DA":>10s}  ajuste manual/Cons')
    for b, g in d.groupby(by, observed=True):
        A = g.A.sum()
        if A < 1000: continue
        wc, ws = (g.cons-g.A).abs().sum()/A, (g.sysda-g.A).abs().sum()/A
        sc, ss = (A-g.cons.sum())/A, (A-g.sysda.sum())/A
        print(f'   {str(b):24s} {len(g):5d} {A:8,.0f}  {wc:9.0%} {ws:11.0%} {ws-wc:+6.0%}  {sc:+8.0%} {ss:+10.0%}  {g.ajuste.sum()/g.cons.sum():+.0%}')
d = D[D.h.between(1,3)]
tab(d, 'tipo', 'Por tipo de artículo')
r = d[~d.os]
tab(r, 'flag', 'REGULAR por Ignore System Forecast Flag')
tab(r, 'seg_foto', 'REGULAR por segmento')
tab(r, 'edad_b', 'REGULAR por edad')
tab(r, 'brand', 'REGULAR por brand')
tab(D[~D.os], 'h', 'REGULAR por horizonte (h=1..9)')
