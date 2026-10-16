import numpy as np, pandas as pd
from statsmodels.stats.proportion import proportion_confint as ci
S = '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad'
Z = pd.read_pickle(S+'/ind4.pkl'); P = Z[(Z.os == 0) & (Z.s12 >= 150) & (Z.edad >= 13)].copy()
corte = 2025*12+3
rng = np.random.default_rng(7); cods = P.ean.unique(); rng.shuffle(cods); mit = {e: i % 2 for i, e in enumerate(cods)}
P['mitad'] = P.ean.map(mit)
L = np.log
sano = (P.last3_vs_rate >= .6) & (P.zeros3 == 0); r3 = P.y3 / P.base_rob
EV = {
 'CAÍDA 3M (código hoy sano vende < 0,5x lo esperable)': (sano & r3.notna() & (P.base_rob >= 30), r3 < .5, r3),
 'MUERTE 6M (código hoy sano vende < 20% de su ritmo)': (sano & P.y6.notna(), P.y6 < .2*6*P.mu12, P.y6/(6*P.mu12)),
 'PEDIDO GRANDE el mes que viene': (P.a1.notna(), P.a1 >= P.thr_big, P.a1/P.mu12),
 'SUBIDA FUERTE 3M (> 1,5x lo esperable)': (r3.notna() & (P.base_rob >= 30), r3 > 1.5, r3),
 'MES VACÍO el mes que viene (< 25% de la media)': (P.a1.notna(), P.a1 < .25*P.mu12, P.a1/P.mu12),
}
SEN = {
 'CAÍDA 3M (código hoy sano vende < 0,5x lo esperable)': {
   'C1 Errático (CV ≥ 0,9), pequeño (< 4.000 uds/año) y último mes < 30% de su media': (P.s_cv12 >= .9) & (P.s12 < 4000) & (P.s_last_avg < .3),
   'C2 Sobre-rendimiento: crece ≥ 4x más que su brand y es errático (CV ≥ 0,9)': (P.rs_br >= L(4)) & (P.s_cv12 >= .9),
   'C3 Crece ≥ 6x más que su PL mientras la PL cae ≥ 40%': (P.rs_pl >= L(6)) & (P.pl_s_yoy3 <= L(.6)),
   'C4 Brand en campaña de One Shots (OS ≥ 70% del regular en 3M) y tamaño ≥ 150 ml': (P.os_br3 >= .7) & (P.ml >= 150),
   'C5 Muy errático (CV ≥ 1,25) y pequeño (< 4.000 uds/año)': (P.s_cv12 >= 1.25) & (P.s12 < 4000)},
 'MUERTE 6M (código hoy sano vende < 20% de su ritmo)': {
   'M1 Pequeño (< 4.000 uds/año), errático (CV ≥ 1) y su PL cae ≥ 30% (3M YoY)': (P.s12 < 4000) & (P.s_cv12 >= 1) & (P.pl_s_yoy3 <= L(.7)),
   'M2 Rabbit con EPOS ≥ 25% peor que el EPOS de su brand': (P.seg == 'Rabbits') & (P.rs_br_e <= L(.75)),
   'M3 Muy errático (CV ≥ 1,25) y pedido grande en los últimos 3 meses (pico aislado)': (P.s_cv12 >= 1.25) & (P.s_ms_big <= 3),
   'M4 Tamaño ≥ 150 ml con pedido grande en los últimos 2 meses': (P.ml >= 150) & (P.s_ms_big <= 2),
   'M5 Pequeño (< 4.000 uds/año) y la PL cae ≥ 30%': (P.s12 < 4000) & (P.pl_s_yoy3 <= L(.7))},
 'PEDIDO GRANDE el mes que viene': {
   'G1 Re-pedido tras corte: ≥ 2 meses a cero en 12M, pedido grande en los últimos 2 meses y cortes ≥ 0,5 meses de venta': (P.s_zeros12 >= 2) & (P.s_ms_big <= 2) & (P.cut3 >= .5),
   'G2 Estantería vacía: cortes ≥ 2 meses de venta y EPOS 3M ≤ 0,65x su media': (P.cut3 >= 2) & (P.e_last3_vs_rate <= .65),
   'G3 Brand cae ≥ 25% en sell-in pero sus One Shots crecen ≥ 2,5x, y el código pide todos los meses': (P.br_s_yoy3 <= L(.75)) & (P.os_br_yoy3 >= L(2.5)) & (P.zeros3 == 0),
   'G4 Septiembre y el código pide todos los meses (12M sin ceros)': (P.mes_obj == 9) & (P.s_zeros12 == 0)},
 'SUBIDA FUERTE 3M (> 1,5x lo esperable)': {
   'U1 Momentum de pedidos: ≥ 3 pedidos grandes en 12M y últimos 3M ≥ 1,5x su ritmo': (P.n_big12 >= 3) & (P.last3_vs_rate >= 1.5),
   'U2 Código irregular (algún mes a cero) que se reactiva: últimos 3M ≥ 1,2x ritmo y su brand sin campaña OS (< 5%)': (P.s_zeros12 >= 1) & (P.last3_vs_rate >= 1.2) & (P.os_br3 < .05),
   'U3 Llenado de canal: el retailer compra ≥ 45% más de lo que vende (sell-through ≤ 0,69 de lo normal) y hubo pedido grande en 3 meses': (P.st3 <= .69) & (P.s_ms_big <= 3),
   'U4 Recuperación tras cortes: cortes ≥ 0,6 meses de venta y EPOS de la brand cae ≥ 20%': (P.cut3 >= .6) & (P.br_e_yoy3 <= L(.8))},
 'MES VACÍO el mes que viene (< 25% de la media)': {
   'V1 Último mes < 10% de la media y SIN cortes (demanda, no supply)': (P.s_last_avg < .1) & (P.cut3 <= 0),
   'V2 Último mes < 10% de la media y tendencia 12M negativa': (P.s_last_avg < .1) & (P.s_slope12 < -.1),
   'V3 Último mes < 10% de la media CON cortes > 1 mes (supply: ojo, puede volver)': (P.s_last_avg < .1) & (P.cut3 > 1)},
}
filas, conf = [], []
for ev, (pob, y, mag) in EV.items():
    D = P[pob]; Y = y[pob]; M = mag[pob]; base = Y.mean()
    part = {'antiguo': D.F < corte, 'reciente': D.F >= corte, 'mitad A': D.mitad == 0, 'mitad B': D.mitad == 1}
    cnt = pd.Series(0, index=D.index)
    for nm, cond in SEN[ev].items():
        c = cond[pob].fillna(False).astype(bool); cnt += c
        lo, hi = ci(int(Y[c].sum()), max(int(c.sum()), 1), method='wilson')
        pp = {k: (Y[c & v].mean() if (c & v).sum() >= 10 else np.nan) for k, v in part.items()}
        filas.append(dict(evento=ev, señal=nm, p=Y[c].mean(), lo=lo, hi=hi, base=base, n=int(c.sum()), cod=D.ean[c].nunique(), meses=D.F[c].nunique(),
                          mag=np.median(M[c]) if c.sum() else np.nan, **{k: v for k, v in pp.items()}))
    for k_ in [0, 1, 2]:
        sel = (cnt == k_) if k_ < 2 else (cnt >= 2)
        if sel.sum() < 5: continue
        lo, hi = ci(int(Y[sel].sum()), int(sel.sum()), method='wilson')
        conf.append(dict(evento=ev, señales=f'{k_}' if k_ < 2 else '2+', p=Y[sel].mean(), lo=lo, hi=hi, n=int(sel.sum()), cod=D.ean[sel].nunique(), mag=np.median(M[sel]),
                         antiguo=Y[sel & part['antiguo']].mean(), reciente=Y[sel & part['reciente']].mean(), n_ant=int((sel & part['antiguo']).sum()), n_rec=int((sel & part['reciente']).sum())))
F = pd.DataFrame(filas); C = pd.DataFrame(conf)
pd.set_option('display.width', 280); pd.set_option('display.max_colwidth', 120)
for ev, g in F.groupby('evento', sort=False):
    print(f'\n### {ev}  (base {g.base.iloc[0]:.0%})')
    for _, r in g.iterrows():
        print(f"  {r.señal}\n      -> {r.p:.0%} [{r.lo:.0%}-{r.hi:.0%}] · n={r.n} ({r.cod} cód., {r.meses} meses) · mediana {r.mag:.2f} · antiguo {r.antiguo:.0%} · reciente {r.reciente:.0%} · mitad A {r['mitad A']:.0%} · mitad B {r['mitad B']:.0%}")
    c = C[C.evento == ev]
    print('  CONFLUENCIA: ' + ' | '.join(f"{r.señales} señales: {r.p:.0%} [{r.lo:.0%}-{r.hi:.0%}] n={r.n} (ant {r.antiguo:.0%}/rec {r.reciente:.0%}) med {r.mag:.2f}" for _, r in c.iterrows()))
F.to_pickle(S+'/senales_final.pkl'); C.to_pickle(S+'/confluencia_final.pkl')
