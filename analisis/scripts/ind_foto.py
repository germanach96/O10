"""Indicadores de la foto (Consensus, DA, revisiones, ajuste manual, capas) + biblioteca técnica, por código x foto. Armonizado."""
from base import *
import json
per = json.load(open(S+'/perimetro.json')); K = per['k']; KB = per['kb']; SOLO = set(per['solo_nuevo'])
fv = pd.read_pickle(S+'/fva_arm.pkl')            # filas foto x código x mes (A, cons_arm, tda_fut_arm, sys_arm, ...)
sy = pd.read_pickle(S+'/sysfc.pkl')
fv = fv.merge(sy[['ean','t','foto','init','prom']].rename(columns={'init':'init2','prom':'prom2'}), on=['ean','t','foto'], how='left')
viejo = fv.foto <= 2026*12+0; kk = fv.ean.map(K).fillna(1.0)
for c in ['init2','prom2']: fv[c] = np.where(viejo, fv[c].fillna(0)*kk, fv[c].fillna(0))
FC2 = FC.copy(); vj = FC2.foto <= 2026*12+0; k2 = FC2.ean.map(K).fillna(1.0)
FC2['cons_a'] = np.where(vj, FC2.cons.fillna(0)*k2, FC2.cons.fillna(0))
def agg(df, lo, hi, col):
    return df[df.h.between(lo, hi)].groupby(['foto','ean'])[col].sum()
g = pd.DataFrame({'c3': agg(fv,1,3,'cons_arm'), 'da3': agg(fv,1,3,'tda_fut_arm'), 'sys3': agg(fv,1,3,'sys_arm'),
                  'init3': agg(fv,1,3,'init2'), 'prom3': agg(fv,1,3,'prom2'), 'A3': agg(fv,1,3,'A'),
                  'c1': agg(fv,1,1,'cons_arm'), 'A1': agg(fv,1,1,'A'), 'da1': agg(fv,1,1,'tda_fut_arm')})
c46 = FC2[FC2.h.between(4,6)].groupby(['foto','ean']).cons_a.sum().rename('c46')
c79 = FC2[FC2.h.between(7,9)].groupby(['foto','ean']).cons_a.sum().rename('c79')
g = g.join(c46).join(c79).reset_index().rename(columns={'foto':'F'})
# revisiones: el mismo bloque de meses (F+1..F+3) en la foto anterior (F-1, h=2..4) y en F-3 (h=4..6)
prev = FC2.copy(); prev['F'] = prev.foto + 1; r1 = prev[prev.t.between(prev.F+1, prev.F+3)].groupby(['F','ean']).cons_a.sum().rename('c3_prev1')
prev3 = FC2.copy(); prev3['F'] = prev3.foto + 3; r3 = prev3[prev3.t.between(prev3.F+1, prev3.F+3)].groupby(['F','ean']).cons_a.sum().rename('c3_prev3')
g = g.merge(r1.reset_index(), on=['F','ean'], how='left').merge(r3.reset_index(), on=['F','ean'], how='left')
flag = sy.groupby(['foto','ean']).flag.first().reset_index().rename(columns={'foto':'F'})
g = g.merge(flag, on=['F','ean'], how='left')
Z = pd.read_pickle(S+'/ind3.pkl')
G = g.merge(Z, on=['F','ean'], how='left')
L = lambda a, b: np.log((a+1)/(b+1))
G['c_gc'] = L(G.c3, G.y3_ly)                    # crecimiento YoY que asume el Consensus
G['c_vs_s3'] = L(G.c3, G.s12/12*3 if False else np.expm1(G.log_vol12)/4)   # Consensus 3M vs nivel trimestral de 12M
G['c_vs_last3'] = L(G.c3, np.nan_to_num(np.expm1(G.log_vol12)) * 0 + G.c3 * 0 + G.c3)  # placeholder (se sobrescribe)
G['c_gap_e'] = G.c_gc - G.e_yoy3                  # Consensus vs EPOS
G['c_gap_s'] = G.c_gc - G.s_yoy3                  # Consensus vs sell-in reciente
G['c_da_share'] = G.da3 / np.maximum(G.c3, 1)
G['c_da_pos'] = (G.da3 > 0.05*G.c3).astype(float); G['c_da_neg'] = (G.da3 < -0.05*G.c3).astype(float)
G['c_man'] = L(G.c3, (G.sys3 + G.da3).clip(lower=0))     # ajuste manual: Consensus vs Sistema+DA
G['c_init_share'] = G.init3 / np.maximum(G.c3, 1); G['c_prom_share'] = G.prom3 / np.maximum(G.c3, 1)
G['c_rev1'] = L(G.c3, G.c3_prev1); G['c_rev3'] = L(G.c3, G.c3_prev3)
G['c_hockey'] = L(G.c46, G.c3)                    # forma: meses 4-6 vs 1-3
G['c_long'] = L(G.c79, G.c3)
G['c_vs_ly'] = G.c_gc
G['c_flag'] = G.flag.fillna('0').map({'0':0,'1':1,'2':2}).astype(float)
G['c_vol'] = np.log1p(G.c3)
G = G.drop(columns=['c_vs_last3'])
G['solo_nuevo'] = G.ean.isin(SOLO)
G['os'] = G.ean.map(dict(zip(EANS, OS))).astype(float)
G['edad'] = G.F - G.ean.map(dict(zip(EANS, PRIMER)))
G.to_pickle(S+'/indfoto.pkl')
print(G.shape, sorted(set(m(f) for f in G.F)))
print(G[['c_gc','c_gap_e','c_da_share','c_man','c_rev1','c_rev3','c_hockey']].describe().round(2).to_string())
