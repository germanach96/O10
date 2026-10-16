"""Biblioteca de señales binarias legibles (todas con información hasta F-1) y objetivos de los próximos 3 meses."""
import sys
import numpy as np
import pandas as pd

S = '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad'
sys.path.insert(0, S)
from base import ACT, IX, T0, T1, k as kk  # noqa: E402

Z = pd.read_pickle(S + '/ind4.pkl')
P = Z[(Z.os == 0) & (Z.s12 >= 150) & (Z.edad >= 13)].copy().reset_index(drop=True)
P['tiene_y'] = P.y3.notna() & (P.base_rob > 0)
L = np.log

# ---------- objetivos (próximos 3 meses)
r = P.y3 / P.base_rob
P['Y_caida'] = (r < .8).astype(int)
P['Y_caida_fuerte'] = (r < .5).astype(int)
P['Y_subida'] = (r > 1.2).astype(int)
P['Y_subida_fuerte'] = (r > 1.5).astype(int)
i = P.ean.map(IX).to_numpy()
f = P.F.to_numpy()
big3 = np.zeros(len(P), bool)
for h in (1, 2, 3):
    t = f + h - T0
    ok = t <= T1 - T0
    big3[ok] |= ACT[i[ok], t[ok]] >= P.thr_big.to_numpy()[ok]
P['Y_pedido3'] = big3.astype(int)
P['ratio3'] = r
# pedido grande el mismo trimestre del año pasado
ly_big3 = np.zeros(len(P), bool)
for h in (1, 2, 3):
    t = f + h - 12 - T0
    ok = t >= 0
    ly_big3[ok] |= ACT[i[ok], t[ok]] >= P.thr_big.to_numpy()[ok]
P['ly_big3'] = ly_big3

# ---------- señales: (id, familia, texto, usa_epos, máscara)
SIG = []


def add(sid, fam, texto, mask, epos=False):
    m = pd.Series(mask, index=P.index).fillna(False).astype(bool)
    SIG.append(dict(id=sid, familia=fam, texto=texto, epos=epos, mask=m))


g = lambda x: np.exp(x) - 1  # noqa: E731  log-ratio -> variación
si3, si6, si12 = P.s_yoy3, P.s_yoy6, P.s_yoy12
ep3, ep6 = P.e_yoy3, P.e_yoy6
up, dn, UP, DN = L(1.1), L(0.9), L(1.3), L(0.7)

# 1. Trend de sell-in del código
add('SI_up3', 'Trend sell-in', 'Sell-in de los últimos 3 meses > +10 % frente al año pasado', si3 > up)
add('SI_UP3', 'Trend sell-in', 'Sell-in de los últimos 3 meses > +30 % frente al año pasado', si3 > UP)
add('SI_dn3', 'Trend sell-in', 'Sell-in de los últimos 3 meses < −10 % frente al año pasado', si3 < dn)
add('SI_DN3', 'Trend sell-in', 'Sell-in de los últimos 3 meses < −30 % frente al año pasado', si3 < DN)
add('SI_dn12', 'Trend sell-in', 'Sell-in de 12 meses < −10 % frente al año anterior', si12 < dn)
add('SI_up12', 'Trend sell-in', 'Sell-in de 12 meses > +10 % frente al año anterior', si12 > up)
add('SI_acel', 'Trend sell-in', 'Acelera: el trend de 3 meses es 20 puntos mejor que el de 12', (si3 - si12) > L(1.2))
add('SI_frena', 'Trend sell-in', 'Frena: el trend de 3 meses es 20 puntos peor que el de 12', (si3 - si12) < L(.8))
add('SI_giro_up', 'Trend sell-in', 'Giro al alza: 12 meses en negativo pero los últimos 3 en positivo', (si12 < dn) & (si3 > up))
add('SI_giro_dn', 'Trend sell-in', 'Giro a la baja: 12 meses en positivo pero los últimos 3 en negativo', (si12 > up) & (si3 < dn))
add('SI_racha_up', 'Trend sell-in', 'Racha: 5 o 6 de los últimos 6 meses por encima del año pasado', P.s_up6 >= 5 / 6 - 1e-9)
add('SI_racha_dn', 'Trend sell-in', 'Racha: ninguno de los últimos 6 meses por encima del año pasado', P.s_up6 <= 0)
add('SI_last_hi', 'Trend sell-in', 'Último mes > 1,5× su media de 12 meses', P.s_last_avg > 1.5)
add('SI_last_lo', 'Trend sell-in', 'Último mes < 0,3× su media de 12 meses', P.s_last_avg < .3)
add('SI_3m_hi', 'Trend sell-in', 'Últimos 3 meses > 1,3× su ritmo de 12 meses', P.last3_vs_rate > 1.3)
add('SI_3m_lo', 'Trend sell-in', 'Últimos 3 meses < 0,6× su ritmo de 12 meses', P.last3_vs_rate < .6)
add('SI_max', 'Trend sell-in', 'Está en máximos: últimos 3 meses ≥ 90 % de su mejor trimestre del año', P.s_dd >= .9)
add('SI_suelo', 'Trend sell-in', 'Está en mínimos: últimos 3 meses < 25 % de su mejor trimestre del año', P.s_dd < .25)

# 2. Trend de sell-out (EPOS)
add('EP_up3', 'Trend sell-out', 'EPOS de los últimos 3 meses > +10 % frente al año pasado', ep3 > up, True)
add('EP_dn3', 'Trend sell-out', 'EPOS de los últimos 3 meses < −10 % frente al año pasado', ep3 < dn, True)
add('EP_DN3', 'Trend sell-out', 'EPOS de los últimos 3 meses < −30 % frente al año pasado', ep3 < DN, True)
add('EP_acel', 'Trend sell-out', 'EPOS acelera: trend de 3 meses 15 puntos mejor que el de 6', P.e_acc > L(1.15), True)
add('EP_frena', 'Trend sell-out', 'EPOS frena: trend de 3 meses 15 puntos peor que el de 6', P.e_acc < L(.85), True)
add('EP_last_hi', 'Trend sell-out', 'EPOS de los últimos 3 meses > 1,2× su media de 12 meses', P.e_last3_vs_rate > 1.2, True)
add('EP_last_lo', 'Trend sell-out', 'EPOS de los últimos 3 meses < 0,7× su media de 12 meses', P.e_last3_vs_rate < .7, True)

# 3. Sell-in frente a sell-out (conjuntas)
add('X_si_dn_ep_up', 'Sell-in vs sell-out', 'Sell-in baja (< −10 %) mientras el EPOS sube (> +10 %): el retailer se quedó corto', (si3 < dn) & (ep3 > up), True)
add('X_si_up_ep_dn', 'Sell-in vs sell-out', 'Sell-in sube (> +10 %) mientras el EPOS baja (< −10 %): el retailer se está cargando', (si3 > up) & (ep3 < dn), True)
add('X_ambos_up', 'Sell-in vs sell-out', 'Sell-in y EPOS suben los dos (> +10 %)', (si3 > up) & (ep3 > up), True)
add('X_ambos_dn', 'Sell-in vs sell-out', 'Sell-in y EPOS bajan los dos (< −10 %)', (si3 < dn) & (ep3 < dn), True)
add('X_ambos_DN', 'Sell-in vs sell-out', 'Sell-in y EPOS se hunden los dos (< −30 %)', (si3 < DN) & (ep3 < DN), True)
add('X_div_pos', 'Sell-in vs sell-out', 'El sell-in va 30 puntos por encima del EPOS (trend de 3 meses)', P.div3 > L(1.3), True)
add('X_div_neg', 'Sell-in vs sell-out', 'El sell-in va 30 puntos por debajo del EPOS (trend de 3 meses)', P.div3 < L(.7), True)
add('X_st_alto', 'Sell-in vs sell-out', 'El retailer vende más de lo que compra: sell-through 3 meses > 1,3× lo normal', P.st3 > 1.3, True)
add('X_st_bajo', 'Sell-in vs sell-out', 'El retailer compra más de lo que vende: sell-through 3 meses < 0,7× lo normal', P.st3 < .7, True)
add('X_stock_alto', 'Sell-in vs sell-out', 'Canal cargado: en 6 meses entró más de 1 mes de venta de más', P.stock6 > 1, True)
add('X_stock_bajo', 'Sell-in vs sell-out', 'Canal vacío: en 6 meses entró más de 1 mes de venta de menos', P.stock6 < -1, True)

# 4. Código frente a su grupo (casa, brand, línea)
ho3, br3, pl3 = P.ho_s_yoy3, P.br_s_yoy3, P.pl_s_yoy3
add('G_casa_dn', 'Código vs grupo', 'La casa cae (sell-in regular < −10 % en 3 meses)', ho3 < dn)
add('G_casa_up', 'Código vs grupo', 'La casa crece (sell-in regular > +10 % en 3 meses)', ho3 > up)
add('G_brand_dn', 'Código vs grupo', 'Su brand cae (< −10 % en 3 meses)', br3 < dn)
add('G_brand_DN', 'Código vs grupo', 'Su brand se hunde (< −30 % en 3 meses)', br3 < DN)
add('G_brand_up', 'Código vs grupo', 'Su brand crece (> +10 % en 3 meses)', br3 > up)
add('G_linea_dn', 'Código vs grupo', 'Su línea cae (< −10 % en 3 meses)', pl3 < dn)
add('G_linea_DN', 'Código vs grupo', 'Su línea se hunde (< −30 % en 3 meses)', pl3 < DN)
add('G_linea_up', 'Código vs grupo', 'Su línea crece (> +10 % en 3 meses)', pl3 > up)
add('G_contra_casa', 'Código vs grupo', 'Contracorriente: el código sube (> +10 %) mientras la casa cae (< −10 %)', (si3 > up) & (ho3 < dn))
add('G_contra_brand', 'Código vs grupo', 'Contracorriente: el código sube (> +10 %) mientras su brand cae (< −10 %)', (si3 > up) & (br3 < dn))
add('G_contra_linea', 'Código vs grupo', 'Contracorriente: el código sube (> +10 %) mientras su línea cae (< −10 %)', (si3 > up) & (pl3 < dn))
add('G_rezagado', 'Código vs grupo', 'Rezagado: el código cae (< −10 %) mientras su brand crece (> +10 %)', (si3 < dn) & (br3 > up))
add('G_rs_brand_hi', 'Código vs grupo', 'Va mucho mejor que su brand (trend 2× mejor)', P.rs_br > L(2))
add('G_rs_brand_lo', 'Código vs grupo', 'Va mucho peor que su brand (trend la mitad)', P.rs_br < L(.5))
add('G_rs_linea_hi', 'Código vs grupo', 'Va mucho mejor que su línea (trend 2× mejor)', P.rs_pl > L(2))
add('G_rs_linea_lo', 'Código vs grupo', 'Va mucho peor que su línea (trend la mitad)', P.rs_pl < L(.5))
add('G_cuota_up', 'Código vs grupo', 'Gana cuota en su línea (cuota de 3 meses > 1,2× la de 12)', P.pl_share_chg > L(1.2))
add('G_cuota_dn', 'Código vs grupo', 'Pierde cuota en su línea (cuota de 3 meses < 0,8× la de 12)', P.pl_share_chg < L(.8))
add('G_ep_brand_hi', 'Código vs grupo', 'Su EPOS va mejor que el EPOS de su brand (20 puntos)', P.rs_br_e > L(1.2), True)
add('G_ep_brand_lo', 'Código vs grupo', 'Su EPOS va peor que el EPOS de su brand (20 puntos)', P.rs_br_e < L(.8), True)
add('G_casa_ep_dn', 'Código vs grupo', 'El EPOS de la casa cae (< −10 %)', P.ho_e_yoy3 < dn, True)
add('G_brand_ep_up', 'Código vs grupo', 'El EPOS de su brand sube (> +10 %)', P.br_e_yoy3 > up, True)
add('G_brand_ep_dn', 'Código vs grupo', 'El EPOS de su brand cae (< −10 %)', P.br_e_yoy3 < dn, True)
add('G_brand_destock', 'Código vs grupo', 'Su brand desstocka: sell-in de la brand 20 puntos por debajo de su EPOS', (br3 - P.br_e_yoy3) < L(.8), True)

# 5. Ciclo de pedidos y calendario
add('C_ly_big3', 'Pedidos y calendario', 'El año pasado tuvo un pedido grande en estos mismos 3 meses', P.ly_big3)
add('C_ly_pico', 'Pedidos y calendario', 'El año pasado estos 3 meses fueron temporada alta para el código (> 1,3× su media)', P.ly_next3 > 1.3)
add('C_ly_valle', 'Pedidos y calendario', 'El año pasado estos 3 meses fueron temporada baja para el código (< 0,7× su media)', P.ly_next3 < .7)
add('C_big_reciente', 'Pedidos y calendario', 'Hizo un pedido grande en los últimos 2 meses', P.s_ms_big <= 2)
add('C_big_lejos', 'Pedidos y calendario', 'Lleva 9 meses o más sin pedido grande (pero tuvo alguno)', P.s_ms_big.between(9, 12))
add('C_sin_big', 'Pedidos y calendario', 'No ha hecho ningún pedido grande en 12 meses', P.n_big12 == 0)
add('C_muchos_big', 'Pedidos y calendario', 'Hizo 3 o más pedidos grandes en 12 meses', P.n_big12 >= 3)
add('C_errático', 'Pedidos y calendario', 'Errático: meses muy distintos entre sí (CV ≥ 1)', P.s_cv12 >= 1)
add('C_regular', 'Pedidos y calendario', 'Regular: meses parecidos entre sí (CV < 0,5)', P.s_cv12 < .5)
add('C_ceros', 'Pedidos y calendario', 'Tuvo 2 o más meses a cero en el último año', P.s_zeros12 >= 2)
add('C_q4', 'Pedidos y calendario', 'Los próximos 3 meses incluyen septiembre u octubre (carga de Q4)', P.mes_obj.isin([8, 9, 10]))
add('C_post_navidad', 'Pedidos y calendario', 'Los próximos 3 meses empiezan en enero o febrero', P.mes_obj.isin([1, 2]))

# 6. Supply, lanzamientos, One Shots, ciclo de vida
add('O_cortes', 'Supply y cartera', 'Cortes de supply en los últimos 3 meses (> 0,5 meses de venta)', P.cut3 > .5)
add('O_cortes_altos', 'Supply y cartera', 'Cortes fuertes en los últimos 3 meses (> 2 meses de venta)', P.cut3 > 2)
add('O_lanz_brand', 'Supply y cartera', 'Su brand lanzó 3 o más regulares en los últimos 6 meses', P.lan_br_6 >= 3)
add('O_lanz_linea', 'Supply y cartera', 'Su línea lanzó algún regular en los últimos 6 meses', P.lan_pl_6 >= 1)
add('O_os_campaña', 'Supply y cartera', 'Campaña de One Shots en su brand (≥ 50 % del sell-in regular en 3 meses)', P.os_br3 >= .5)
add('O_os_crece', 'Supply y cartera', 'Los One Shots de su brand crecen más del doble frente al año pasado', P.os_br_yoy3 > L(2))
add('O_grande_ml', 'Supply y cartera', 'Tamaño grande (150 ml o más)', P.ml >= 150)
add('O_mini', 'Supply y cartera', 'Tamaño mini (10 ml o menos)', P.ml <= 10)
add('O_pequeño', 'Supply y cartera', 'Código pequeño (menos de 4.000 uds/año)', P.s12 < 4000)
add('O_grande_vol', 'Supply y cartera', 'Código grande (más de 30.000 uds/año)', P.s12 > 30000)
add('O_joven', 'Supply y cartera', 'Joven: entre 13 y 24 meses desde su primera venta', P.edad <= 24)
for seg in ['Bulls', 'Horses', 'Rabbits', 'Post NPI', 'DISC']:
    add(f'O_seg_{seg.replace(" ", "")}', 'Supply y cartera', f'Segmento {seg}', P.seg == seg)
add('O_disco', 'Supply y cartera', 'Tiene fecha de discontinuación en los próximos 12 meses', P.meses_a_disco.between(0, 12))

SIGDF = pd.DataFrame([{k: v for k, v in s.items() if k != 'mask'} for s in SIG])
X = pd.DataFrame({s['id']: s['mask'].astype(int) for s in SIG})
OBJ = ['Y_caida', 'Y_caida_fuerte', 'Y_subida', 'Y_subida_fuerte', 'Y_pedido3']
if __name__ == '__main__':
    M = P.tiene_y.to_numpy()
    Pm, Xm = P[M].reset_index(drop=True), X[M].reset_index(drop=True)
    print(len(Pm), 'casos ·', Pm.ean.nunique(), 'códigos ·', len(SIG), 'señales')
    print('tasas base:', {o: round(Pm[o].mean(), 3) for o in OBJ})
    pd.to_pickle((Pm, Xm, SIGDF), S + '/senales_lib.pkl')
    cur = (P.F == P.F.max()).to_numpy()
    pd.to_pickle((P[cur].reset_index(drop=True), X[cur].reset_index(drop=True)), S + '/senales_hoy.pkl')
    print('foto actual: decisión', int(P.F.max()), 'códigos', int(cur.sum()))
