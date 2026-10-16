"""Validación fuera de muestra: ajustar el Consensus con señales calibradas solo con fotos pasadas."""
from base import *
from scipy.optimize import minimize_scalar, minimize
fv = pd.read_pickle(S+'/fva_arm.pkl'); fv['cons']=fv.cons_arm; fv['tda_fut']=fv.tda_fut_arm; fv['base']=fv.base_arm; X = pd.read_pickle(S+'/feats.pkl')
L = lambda a, b: np.log((a+1)/(b+1))
X['gep'] = L(X.ep3, X.ep3_ly); X['gs'] = L(X.si3, X.si3_ly)
X['c3'] = np.nan
c3 = fv[fv.h.between(1,3)].groupby(['foto','ean']).cons.sum().rename('c3').reset_index().rename(columns={'foto':'F'})
X = X.drop(columns='c3').merge(c3, on=['F','ean'], how='left')
X['gc'] = L(X.c3, X.y3_ly)
d = fv[fv.h.between(1,3)].merge(X[['F','ean','gep','gs','gc','si12','ep3_ly','edad']].rename(columns={'F':'foto'}), on=['foto','ean'], how='left')
d = d[(d.cons > 0) | (d.A > 0)]
d['Dp'] = d.tda_fut.clip(lower=0)
d['tiene_ep'] = d.gep.notna() & (d.ep3_ly >= 30) & d.gc.notna()
FOT = sorted(d.foto.unique())
def wape(F, A): return np.abs(F - A).sum() / A.sum()
def ajuste(g, b_gap, rho):
    base = g.cons - (1 - rho) * g.Dp                    # recorte del DA positivo
    gap = np.where(g.tiene_ep, (g.gep - g.gc).clip(-2, 2), 0.0)
    return np.clip(base * np.exp(b_gap * gap), 0, None)
rows = []
for F in FOT:
    tr = d[(d.foto <= F - 4)]; te = d[d.foto == F]
    if tr.foto.nunique() < 1 or len(te) == 0: continue
    for sub, msk_tr, msk_te in [('Regular', ~tr.os, ~te.os), ('One Shot', tr.os, te.os)]:
        a, b = tr[msk_tr], te[msk_te]
        if len(a) < 50: continue
        f = lambda x: wape(ajuste(a, x[0], x[1]), a.A)
        best = min((f((bg, r)), bg, r) for bg in np.linspace(0, 1, 11) for r in np.linspace(0, 1, 11))
        _, bg, r = best
        f_r = lambda x: wape(ajuste(a, 0, x), a.A); r_only = min((f_r(r_), r_) for r_ in np.linspace(0,1,21))[1]
        f_g = lambda x: wape(ajuste(a, x, 1), a.A); g_only = min((f_g(g_), g_) for g_ in np.linspace(0,1,21))[1]
        rows.append(dict(F=m(F), tipo=sub, n=len(b), A=b.A.sum(), b_gap=bg, rho=r, rho_solo=r_only, gap_solo=g_only,
                         Consensus=wape(b.cons, b.A), Ajuste_DA=wape(ajuste(b, 0, r_only), b.A),
                         Ajuste_EPOS=wape(ajuste(b, g_only, 1), b.A), Ajuste_ambos=wape(ajuste(b, bg, r), b.A),
                         SPP_cons=(b.A.sum()-b.cons.sum())/b.A.sum(), SPP_ambos=(b.A.sum()-ajuste(b,bg,r).sum())/b.A.sum()))
R = pd.DataFrame(rows); pd.set_option('display.width', 250)
print(R.round(2).to_string(index=False))
for tipo, g in R.groupby('tipo'):
    w = g.A / g.A.sum()
    print(f'\n{tipo}: WAPE90 mensual fuera de muestra (ponderado), {len(g)} fotos de prueba')
    for c in ['Consensus','Ajuste_DA','Ajuste_EPOS','Ajuste_ambos']:
        print(f'   {c:14s} {(g[c]*w).sum():.1%}   mejora al Consensus en {(g[c] < g.Consensus - 1e-9).sum()}/{len(g)} fotos')
R.to_pickle(S+'/adj.pkl')
