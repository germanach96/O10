"""Escenarios frente al Consensus de cada foto: objetivos, señales de la familia 'Consensus frente a la realidad' y señales generales."""
import json
import sys
import numpy as np
import pandas as pd

S = '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad'
sys.path.insert(0, S)
import senales_lib as SL  # noqa: E402  (P = todos los códigos elegibles x mes; X = señales generales)
from base import FC, ACT, IX, T0, T1, FOTOS  # noqa: E402

per = json.load(open(S + '/perimetro.json')); K = per['k']; SOLO = set(per['solo_nuevo'])
VIEJA = 2026 * 12 + 0                     # fotos <= 2026.M01: perímetro viejo -> se armoniza el Consensus
sy = pd.read_pickle(S + '/sysfc.pkl')
fc = FC[FC.h.between(1, 9)].copy()
fc = fc.merge(sy[['ean', 't', 'foto', 'sys', 'flag']], on=['ean', 't', 'foto'], how='left')
fc[['cons', 'tda_fut', 'sys']] = fc[['cons', 'tda_fut', 'sys']].fillna(0)
k = np.where(fc.foto <= VIEJA, fc.ean.map(K).fillna(1.0), 1.0)
for c in ['cons', 'tda_fut', 'sys']:
    fc[c] = fc[c] * k
piv = fc.pivot_table(index=['foto', 'ean'], columns='h', values='cons', aggfunc='sum').fillna(0)
G = pd.DataFrame({'c1': piv[1], 'c2': piv[2], 'c3m': piv[3]})
G['c3'] = G.c1 + G.c2 + G.c3m
G['c46'] = piv[[4, 5, 6]].sum(1); G['c79'] = piv[[7, 8, 9]].sum(1)
a = fc[fc.h.between(1, 3)].groupby(['foto', 'ean'])
G['da3'] = a.tda_fut.sum(); G['sys3'] = a.sys.sum(); G['flag'] = a.flag.first()
G = G.reset_index()
# revisiones: los mismos meses en la foto de hace 1 y 3 meses
for lag in (1, 3):
    p = fc[['foto', 'ean', 't', 'cons']].copy(); p['F'] = p.foto + lag
    p = p[(p.t >= p.F + 1) & (p.t <= p.F + 3)].groupby(['F', 'ean']).cons.sum().rename(f'c3_prev{lag}').reset_index()
    G = G.merge(p.rename(columns={'F': 'foto'}), on=['foto', 'ean'], how='left')
G = G.rename(columns={'foto': 'F'})

P = SL.P.merge(G, on=['F', 'ean'], how='inner')
X = SL.X.loc[SL.P.merge(G[['F', 'ean']], on=['F', 'ean'], how='left', indicator=True)['_merge'].eq('both').to_numpy()].reset_index(drop=True)
P = P.reset_index(drop=True)
assert len(P) == len(X)
P = P[(P.c3 >= 60)].copy()
X = X.loc[P.index].reset_index(drop=True); P = P.reset_index(drop=True)
P['solo_nuevo'] = P.ean.isin(SOLO) & (P.F <= VIEJA)
keep = ~P.solo_nuevo
P, X = P[keep].reset_index(drop=True), X[keep].reset_index(drop=True)

# ---------- objetivos frente al Consensus (meses F+1..F+3)
i = P.ean.map(IX).to_numpy(); f = P.F.to_numpy()
A = np.full((len(P), 3), np.nan)
for h in (1, 2, 3):
    t = f + h - T0
    ok = t <= T1 - T0
    A[ok, h - 1] = ACT[i[ok], t[ok]]
P['A3'] = A.sum(1)
cerrado = ~np.isnan(A).any(1)
Cm = P[['c1', 'c2', 'c3m']].to_numpy()
r = P.A3 / P.c3
P['Y_bajo'] = (r < .8).astype(int); P['Y_muy_bajo'] = (r < .5).astype(int)
P['Y_alto'] = (r > 1.2).astype(int); P['Y_muy_alto'] = (r > 1.5).astype(int)
thr = P.thr_big.to_numpy()[:, None]
P['Y_orden'] = ((A >= thr) & (A > 2 * Cm)).any(1).astype(int)
P['ratio_c'] = r
P['cerrado'] = cerrado

# ---------- señales de la familia "El Consensus frente a la realidad"
L = np.log
ritmo3 = P.s12 / 4
cg = L((P.c3 + 1) / (P.y3_ly + 1))                  # crecimiento interanual que asume el Consensus
SIGC = []


def add(sid, texto, mask, epos=False):
    SIGC.append(dict(id=sid, familia='Consensus frente a la realidad', texto=texto, epos=epos,
                     mask=pd.Series(mask, index=P.index).fillna(False).astype(bool)))


add('K_ritmo_hi', 'El Consensus de 3 meses es más de 1,5× su ritmo de los últimos 12 meses', P.c3 > 1.5 * ritmo3)
add('K_ritmo_HI', 'El Consensus de 3 meses es más de 2,5× su ritmo de los últimos 12 meses', P.c3 > 2.5 * ritmo3)
add('K_ritmo_lo', 'El Consensus de 3 meses es menos de 0,67× su ritmo de los últimos 12 meses', P.c3 < .67 * ritmo3)
add('K_ritmo_LO', 'El Consensus de 3 meses es menos de 0,4× su ritmo de los últimos 12 meses', P.c3 < .4 * ritmo3)
add('K_3m_hi', 'El Consensus de 3 meses es más de 1,5× lo vendido en los últimos 3 meses', P.c3 > 1.5 * P.last3_vs_rate * 3 * P.mu12)
add('K_3m_lo', 'El Consensus de 3 meses es menos de 0,67× lo vendido en los últimos 3 meses', P.c3 < .67 * P.last3_vs_rate * 3 * P.mu12)
add('K_ly_hi', 'El Consensus es más de 1,5× lo que vendió en esos mismos meses el año pasado', P.c3 > 1.5 * P.y3_ly)
add('K_ly_lo', 'El Consensus es menos de 0,67× lo que vendió en esos mismos meses el año pasado', P.c3 < .67 * P.y3_ly)
add('K_si_hi', 'El Consensus asume crecer 50 puntos más que el trend de sell-in de 3 meses', (cg - P.s_yoy3) > L(1.5))
add('K_si_lo', 'El Consensus asume crecer 20 puntos menos que el trend de sell-in de 3 meses', (cg - P.s_yoy3) < L(.8))
add('K_ep_hi', 'El Consensus asume crecer 50 puntos más que el trend del EPOS', (cg - P.e_yoy3) > L(1.5), True)
add('K_ep_lo', 'El Consensus asume crecer 20 puntos menos que el trend del EPOS', (cg - P.e_yoy3) < L(.8), True)
add('K_da_alto', 'El DA es más del 40 % del Consensus de los próximos 3 meses', P.da3 > .4 * P.c3)
add('K_da_neg', 'Hay DA negativo en los próximos 3 meses (más del 5 % del Consensus)', P.da3 < -.05 * P.c3)
add('K_frontal', 'Consensus cargado al principio: meses 7-9 por debajo de 0,5× los meses 1-3', P.c79 < .5 * P.c3)
add('K_tardio', 'El Consensus espera recuperación tardía: meses 7-9 más de 2× los meses 1-3', P.c79 > 2 * P.c3)
add('K_rev_up', 'El Consensus de estos meses subió más de un 30 % frente a hace 3 fotos', P.c3 > 1.3 * P.c3_prev3)
add('K_rev_dn', 'El Consensus de estos meses bajó más de un 30 % frente a hace 3 fotos', P.c3 < .7 * P.c3_prev3)
add('K_man_up', 'Ajuste manual al alza: Consensus más de 1,2× el System FC + DA', P.c3 > 1.2 * (P.sys3 + P.da3.clip(lower=0)))
add('K_man_dn', 'Ajuste manual a la baja: Consensus menos de 0,8× el System FC + DA', P.c3 < .8 * (P.sys3 + P.da3.clip(lower=0)))
add('K_flag', 'El System FC no fluye (Ignore System Forecast Flag 1 o 2)', P.flag.isin(['1', '2']))
cm = P[['c1', 'c2', 'c3m']]
add('K_plano', 'Consensus plano: los 3 meses casi iguales (variación < 10 %)', (cm.std(1) / cm.mean(1).clip(lower=1)) < .1)
add('K_pico_plan', 'El Consensus ya prevé un mes de pedido grande (≥ 2× su mediana)', cm.max(1) >= P.thr_big)
add('K_ultimo_cero', 'El último mes vino casi a cero pero el Consensus es más de 0,8× su ritmo', (P.s_last_avg < .15) & (P.c3 > .8 * ritmo3))

SIGDF = pd.concat([SL.SIGDF, pd.DataFrame([{k_: v for k_, v in s.items() if k_ != 'mask'} for s in SIGC])], ignore_index=True)
for s in SIGC:
    X[s['id']] = s['mask'].astype(int).to_numpy()
OBJ = {'Y_bajo': 'Real más bajo', 'Y_muy_bajo': 'Real mucho más bajo', 'Y_alto': 'Real más alto', 'Y_muy_alto': 'Real mucho más alto', 'Y_orden': 'Orden no prevista'}

if __name__ == '__main__':
    M = P.cerrado.to_numpy()
    Pm, Xm = P[M].reset_index(drop=True), X[M].reset_index(drop=True)
    print(f'casos con resultado: {len(Pm)} · códigos {Pm.ean.nunique()} · fotos {sorted(set(Pm.F))[0]}..{sorted(set(Pm.F))[-1]} ({Pm.F.nunique()})')
    for o, n in OBJ.items():
        print(f'   {n:22s} base {Pm[o].mean():.0%}   2025: {Pm[Pm.F <= VIEJA][o].mean():.0%}   2026: {Pm[Pm.F > VIEJA][o].mean():.0%}')
    print('señales totales', X.shape[1])
    pd.to_pickle((Pm, Xm, SIGDF), S + '/cons_lib.pkl')
    cur = (P.F == max(FOTOS)).to_numpy()
    pd.to_pickle((P[cur].reset_index(drop=True), X[cur].reset_index(drop=True)), S + '/cons_hoy.pkl')
    print('foto actual: códigos', int(cur.sum()))
