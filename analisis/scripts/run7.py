import sys; sys.path.insert(0, '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad')
from minero import *
from base import m, BRAND, EANS
S = '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad'
Z = pd.read_pickle(S+'/ind4.pkl')
P = Z[(Z.os == 0) & (Z.s12 >= 150) & (Z.edad >= 13)].copy().reset_index(drop=True)
r3 = P.y3 / P.base_rob
sano = (P.last3_vs_rate >= .6) & (P.zeros3 == 0); flojo = P.last3_vs_rate < .6
EV = {
 'PEDIDO GRANDE el mes que viene':        (P.a1.notna(), (P.a1 >= P.thr_big), P.a1 / P.mu12, 'sell-in F+1 / media 12M'),
 'MES VACÍO el mes que viene (<25% media)': (P.a1.notna() & (P.zeros3 < 3), (P.a1 < .25*P.mu12), P.a1 / P.mu12, 'sell-in F+1 / media 12M'),
 'CAÍDA 3M de un código hoy sano (<0.5x esperable)': (sano & r3.notna() & (P.base_rob >= 30), (r3 < .5), r3, 'sell-in 3M / esperable'),
 'MUERTE 6M de un código hoy sano (<20% de su ritmo)': (sano & P.y6.notna(), (P.y6 < .2*6*P.mu12), P.y6 / (6*P.mu12), 'sell-in 6M / ritmo'),
 'REBOTE de un código hoy flojo (>=1x esperable)': (flojo & r3.notna() & (P.base_rob >= 30), (r3 >= 1), r3, 'sell-in 3M / esperable'),
 'SUBIDA FUERTE 3M (>1.5x esperable)': (r3.notna() & (P.base_rob >= 30), (r3 > 1.5), r3, 'sell-in 3M / esperable'),
}
noY = {'y3','y3_ly','s12','tr6','base_ext','sorpresa','base_rob','sorp_rob','I_br','a1','a2','y6','mu12','thr_big','lan_pl_next3','lan_br_next3','brand','os','i','Y_yoy3','Y_vs_last3','Y_big1','Y_ratio1'}
todas = [c for c in Z.columns if c not in EXCL and c not in noY and not c.startswith('Y_')]
EPOSF = [f for f in todas if f.startswith('e_') or '_e_' in f or f.endswith('_e') or f in ('st3','st3_raw','stock6','div3','div_mom','agot')]
sin_epos = [f for f in todas if f not in EPOSF]
rng = np.random.default_rng(7)
cods = pd.Series(EANS); mitad = {}
for b, g in pd.Series(BRAND, index=EANS).groupby(BRAND):
    e = list(g.index); rng.shuffle(e)
    for j, x in enumerate(e): mitad[x] = j % 2
P['mitad'] = P.ean.map(mitad)
corte = 2025*12+3
pd.set_option('display.width', 260); pd.set_option('display.max_colwidth', 115)
RES = {}
for nombre, (pob, hit, mag, magn) in EV.items():
    D = P[pob].copy(); D['Y'] = hit[pob].astype(float); D['mag'] = mag[pob]
    salidas = []
    esquemas = [('T1', D[D.F < corte], D[D.F >= corte], sin_epos), ('T2', D[D.F >= corte], D[D.F < corte], sin_epos)]
    De = D[D.F >= 2024*12+9]
    esquemas += [('C1', De[De.mitad == 0], De[De.mitad == 1], todas), ('C2', De[De.mitad == 1], De[De.mitad == 0], todas)]
    for tag, Dd, Dv, fs in esquemas:
        Dd, Dv = Dd.reset_index(drop=True), Dv.reset_index(drop=True)
        R, bd, bv, conds = minar(Dd, Dv, 'Y', fs, min_n=30, min_cod=10)
        if len(R): R['mag_val'] = [np.median(Dv.mag[mv]) if mv.sum() else np.nan for mv in R.mask_v]
        salidas.append((tag, R, bd, bv))
    RES[nombre] = salidas
    print(f'\n################ {nombre}  [magnitud: mediana de {magn}]')
    for tag, R, bd, bv in salidas:
        if R.empty: print(f'   {tag}: sin reglas'); continue
        dv = diversas(R, 6, max_jac=0.4)
        print(f'   {tag} ({"tiempo" if tag[0]=="T" else "códigos, con EPOS"}): base {bd:.0%}/{bv:.0%} · confirmadas {R.confirmada.sum()} de {len(R)}')
        if len(dv): print(dv[['regla','n_desc','p_desc','n_val','cod_val','p_val','lb_val','mag_val']].round(2).to_string(index=False))
pd.to_pickle(RES, S+'/run7.pkl')
