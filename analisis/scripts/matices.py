import numpy as np, pandas as pd
from statsmodels.stats.proportion import proportion_confint as ci
S = '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad'
Z = pd.read_pickle(S+'/ind4.pkl'); P = Z[(Z.os == 0) & (Z.s12 >= 150) & (Z.edad >= 13)].copy()
corte = 2025*12+3
def t(nm, d, y):
    lo, hi = ci(int(y[d.index].sum()), len(d), method='wilson')
    a = d[d.F < corte]; b = d[d.F >= corte]
    print(f'   {nm:62s} {y[d.index].mean():4.0%} [{lo:.0%}-{hi:.0%}] n={len(d):4d} ({d.ean.nunique()} cód., {d.F.nunique()} meses)  antiguo {y[a.index].mean() if len(a) else np.nan:.0%} · reciente {y[b.index].mean() if len(b) else np.nan:.0%}')
v = P[P.a1.notna()]; vac = (v.a1 < .25*v.mu12)
print('1) Último mes ~0: ¿demanda o supply?  -> P(mes siguiente también vacío)')
t('último mes <10% media, SIN cortes en 3M', v[(v.s_last_avg < .1) & (v.cut3 <= 0)], vac)
t('último mes <10% media, CON cortes en 3M', v[(v.s_last_avg < .1) & (v.cut3 > 0)], vac)
t('último mes <10% media, cortes > 1 mes de venta', v[(v.s_last_avg < .1) & (v.cut3 > 1)], vac)
big = (v.a1 >= v.thr_big)
t('   -> y P(pedido grande) con cortes > 1 mes de venta', v[(v.s_last_avg < .1) & (v.cut3 > 1)], big)
print('\n2) Lanzamientos en la brand -> muerte en 6M de códigos sanos')
s = P[(P.last3_vs_rate >= .6) & (P.zeros3 == 0) & P.y6.notna()]; muere = (s.y6 < .2*6*s.mu12)
for nm, q in [('brand sin lanzamientos en 6M', s.lan_br_6 == 0), ('brand con 1-4 lanzamientos', s.lan_br_6.between(1, 4)), ('brand con >=5 lanzamientos', s.lan_br_6 >= 5)]:
    t(nm, s[q], muere)
    t(nm + ' · código pequeño (<4.000/año)', s[q & (s.s12 < 4000)], muere)
    t(nm + ' · código grande (>=4.000/año)', s[q & (s.s12 >= 4000)], muere)
print('\n3) Lanzamientos en la brand -> caída 3M de códigos sanos (<0.5x esperable)')
s3 = P[(P.last3_vs_rate >= .6) & (P.zeros3 == 0) & P.y3.notna() & (P.base_rob >= 30)]; cae = (s3.y3 < .5*s3.base_rob)
for nm, q in [('sin lanzamientos', s3.lan_br_6 == 0), ('1-4', s3.lan_br_6.between(1, 4)), ('>=5', s3.lan_br_6 >= 5)]:
    t(nm + ' · pequeño', s3[q & (s3.s12 < 4000)], cae); t(nm + ' · grande', s3[q & (s3.s12 >= 4000)], cae)
print('\n4) Campaña de One Shots en la brand (OS >= 70% del regular en 3M) -> caída de regulares por tamaño')
for nm, q in [('OS < 20%', s3.os_br3 < .2), ('OS 20-70%', s3.os_br3.between(.2, .7)), ('OS >= 70%', s3.os_br3 >= .7)]:
    t(nm + ' · tamaño >=150 ml', s3[q & (s3.ml >= 150)], cae); t(nm + ' · tamaño 50-100 ml', s3[q & s3.ml.between(50, 100)], cae); t(nm + ' · tamaño <=30 ml', s3[q & (s3.ml <= 30)], cae)
