import numpy as np, pandas as pd
from statsmodels.stats.proportion import proportion_confint
S = '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad'
G = pd.read_pickle(S+'/indfoto.pkl'); corte = 2026*12+1
P = G[(G.F <= 2026*12+5) & (G.c3 >= 60) & ~((G.F < corte) & G.solo_nuevo)].copy()
P['ratio'] = P.c3 / np.maximum(np.expm1(P.log_vol12) / 4, 1)        # Consensus 3M / trimestre medio de los últimos 12M
P['sobre'] = P.A3 < 0.7*P.c3; P['infra'] = P.A3 > 1.3*P.c3
def curva(col, bins, labels, nombre, D=P):
    D = D.assign(b=pd.cut(D[col], bins, labels=labels))
    print(f'\n{nombre}')
    for per, Dx in [('desc', D[D.F < corte]), ('VAL', D[D.F >= corte])]:
        row = []
        for b, g in Dx.groupby('b', observed=True):
            row.append(f'{b}: n={len(g)} sobre {g.sobre.mean():.0%} infra {g.infra.mean():.0%} A/C {g.A3.sum()/g.c3.sum():.2f}')
        print(f'  {per:4s} | ' + ' | '.join(row))
curva('ratio', [0, .5, .8, 1.25, 2, 4, 1e9], ['<0.5x','0.5-0.8x','0.8-1.25x','1.25-2x','2-4x','>4x'], 'Consensus 3M / ritmo trimestral de 12M (c_vs_s3)')
P['long'] = P.c79 / np.maximum(P.c3, 1)
curva('long', [-1, .5, .8, 1.25, 2, 1e9], ['<0.5','0.5-0.8','0.8-1.25','1.25-2','>2'], 'Consensus meses 7-9 / meses 1-3 (¿espera recuperación tardía?) (c_long)')
P['rev3'] = P.c3 / np.maximum(P.c3_prev3, 1)
curva('rev3', [0, .6, .85, 1.15, 1.6, 1e9], ['recortado >40%','-15..-40%','estable','+15..60%','subido >60%'], 'Revisión del Consensus de esos meses frente a 3 fotos antes (c_rev3)', P[P.c3_prev3 > 20])
curva('c_da_share', [-1e9, -.05, .05, .4, 1e9], ['DA negativo','sin DA','DA 5-40%','DA >40%'], 'Peso del DA en el Consensus 3M (c_da_share)')
P['cutm'] = P.cut3
curva('cutm', [-1, 0.0001, .5, 2, 1e9], ['sin cortes','cortes <0.5 mes','0.5-2 meses','>2 meses de venta'], 'Supply Cuts de los últimos 3M, en meses de venta (cut3)')
curva('rs_pl', [-1e9, -.7, -.2, .2, .7, 1e9], ['mucho peor que su PL','peor','igual','mejor','mucho mejor'], 'Fuerza relativa: sell-in YoY 3M del código menos el de su PL (rs_pl)')
curva('os_pl3', [-1, 0.0001, .1, .4, 1e9], ['sin OS','OS <10%','10-40%','>40% del regular'], 'One Shots en su PL los últimos 3M, frente al regular de la PL (os_pl3)')
P['ep'] = np.expm1(P.c_gap_e)
curva('c_gap_e', [-1e9, np.log(.8), np.log(1.2), np.log(1.5), 1e9], ['Cons < EPOS -20%','≈ EPOS','Cons > EPOS 20-50%','Cons > EPOS >50%'], 'Crecimiento YoY del Consensus frente al del EPOS (c_gap_e)')
curva('s_last_avg', [-1, .15, .5, 1.5, 1e9], ['último mes ~0','<0.5x media','normal','>1.5x media'], 'Sell-in del último mes / media 12M (s_last_avg)')
