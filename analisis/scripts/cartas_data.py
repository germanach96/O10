import json, sys
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
sys.path.insert(0, S := '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad')
from base import ATR, m
R = pd.read_pickle(S+'/pesos.pkl'); P, X, SIGDF = pd.read_pickle(S+'/senales_lib.pkl'); H, XH = pd.read_pickle(S+'/senales_hoy.pkl')
sig = lambda z: 1 / (1 + np.exp(-z))
out = {'categorias': {}, 'hoy': [], 'ejemplos': []}
DESC = ATR['Planning Item Description'].to_dict(); BR = ATR['Brand'].to_dict(); SEG = ATR['Final Segment'].to_dict()
PTS = {}
for y, r in R.items():
    pts = (r['coef'] * 10).round().astype(int); pts = pts[pts != 0]; PTS[y] = pts
    b0 = r['intercept']
    tot = X[pts.index] @ pts
    p_pts = sig(b0 + tot / 10)
    auc_pts = roc_auc_score(P[y], p_pts)
    # calibración por puntos con la predicción CV (fuera de muestra)
    pcv = r['pcv']
    bandas = [(-99, -15), (-14, -8), (-7, -3), (-2, 2), (3, 7), (8, 14), (15, 99)]
    cal = []
    for lo, hi in bandas:
        mk = (tot >= lo) & (tot <= hi)
        if mk.sum() < 15: continue
        cal.append(dict(lo=lo, hi=hi, n=int(mk.sum()), pred=float(sig(b0 + tot[mk] / 10).mean()), obs=float(P[y][mk].mean()), cv=float(pcv[mk.to_numpy()].mean())))
    tab = r['tab']
    sen = []
    for sid, pt in pts.sort_values(ascending=False).items():
        row = SIGDF.set_index('id').loc[sid]
        cr = r['criba'].set_index('id').loc[sid]
        sen.append(dict(id=sid, texto=row.texto, familia=row.familia, epos=bool(row.epos), puntos=int(pt), n=int(cr.n), p_si=float(cr.p_si)))
    out['categorias'][y] = dict(nombre=r['nombre'], base=float(P[y].mean()), inicio=float(sig(b0)), b0=float(b0), auc_cv=float(r['auc_cv']), auc_t=float(r['auc_t']),
                                auc_pts=float(auc_pts), cal=cal, senales=sen, minpts=int(pts[pts < 0].sum()), maxpts=int(pts[pts > 0].sum()))
    print(r['nombre'], 'AUC puntos redondeados', round(auc_pts, 3), 'vs CV', round(r['auc_cv'], 3), ' rango puntos', int(pts[pts<0].sum()), int(pts[pts>0].sum()))
    for c in cal: print('   ', c)
# hoy: 5 probabilidades por código
filas = []
for i, row in H.iterrows():
    d = dict(ean=row.ean, desc=DESC.get(row.ean, row.ean), brand=BR.get(row.ean, ''), seg=SEG.get(row.ean, ''), vol12=float(row.s12))
    for y, pts in PTS.items():
        act = [s for s in pts.index if XH.loc[i, s] == 1]
        tot = int(sum(pts[s] for s in act))
        d[y] = float(sig(R[y]['intercept'] + tot / 10)); d[y + '_pts'] = tot; d[y + '_act'] = [(s, int(pts[s])) for s in act]
    filas.append(d)
HO = pd.DataFrame(filas)
out['hoy'] = HO.sort_values('vol12', ascending=False).to_dict('records')
print('\nHOY (decisión', m(int(H.F.iloc[0])), ')', len(HO), 'códigos')
pd.set_option('display.width', 250); pd.set_option('display.max_colwidth', 40)
print(HO.sort_values('vol12', ascending=False).head(12)[['desc','vol12','Y_caida','Y_caida_fuerte','Y_subida','Y_subida_fuerte','Y_pedido3']].round(2).to_string())
# ejemplos históricos (periodo reciente): casos con probabilidad alta en cada categoría y lo que pasó
for y, pts in PTS.items():
    tot = X[pts.index] @ pts; p = sig(R[y]['intercept'] + tot / 10)
    rec = P[(P.F >= 2026*12+0) & (P.s12 >= 5000)].index
    top = p[rec].sort_values(ascending=False).head(3).index
    for j in top:
        out['ejemplos'].append(dict(cat=y, ean=P.ean[j], desc=DESC.get(P.ean[j], ''), foto=m(int(P.F[j])), p=float(p[j]), pts=int(tot[j]),
                                     act=[(s, int(pts[s])) for s in pts.index if X.loc[j, s] == 1], ratio=float(P.ratio3[j]), paso=int(P[y][j])))
ej = pd.DataFrame(out['ejemplos']); print(ej[['cat','desc','foto','p','pts','ratio','paso']].round(2).to_string())
json.dump(out, open(S+'/cartas.json', 'w'), ensure_ascii=False, default=float)
