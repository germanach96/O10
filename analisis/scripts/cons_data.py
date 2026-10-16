import json, sys
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
sys.path.insert(0, S := '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad')
from base import ATR, m
R = pd.read_pickle(S+'/pesos_cons.pkl'); P, X, SIGDF = pd.read_pickle(S+'/cons_lib.pkl'); H, XH = pd.read_pickle(S+'/cons_hoy.pkl')
sig = lambda z: 1 / (1 + np.exp(-z))
DESC = ATR['Planning Item Description'].to_dict(); BR = ATR['Brand'].to_dict(); SEG = ATR['Final Segment'].to_dict()
out = {'categorias': {}, 'hoy': [], 'ejemplos': [], 'n': len(P), 'codigos': int(P.ean.nunique())}
PTS = {}
for y, r in R.items():
    pts = (r['coef'] * 10).round().astype(int); pts = pts[pts != 0]; PTS[y] = pts; b0 = r['intercept']
    tot = X[pts.index] @ pts; pcv = r['pcv']
    cal = []
    for lo, hi in [(-99, -15), (-14, -8), (-7, -3), (-2, 2), (3, 7), (8, 14), (15, 99)]:
        mk = (tot >= lo) & (tot <= hi)
        if mk.sum() < 12: continue
        cal.append(dict(lo=lo, hi=hi, n=int(mk.sum()), pred=float(sig(b0 + tot[mk] / 10).mean()), obs=float(P[y][mk].mean()), cv=float(pcv[mk.to_numpy()].mean())))
    sen = []
    cr = r['criba'].set_index('id'); sd = SIGDF.drop_duplicates('id').set_index('id')
    for sid, pt in pts.sort_values(ascending=False).items():
        sen.append(dict(id=sid, texto=sd.loc[sid].texto, familia=sd.loc[sid].familia, epos=bool(sd.loc[sid].epos), puntos=int(pt), n=int(cr.loc[sid].n), p_si=float(cr.loc[sid].p_si)))
    out['categorias'][y] = dict(nombre=r['nombre'], base=float(P[y].mean()), inicio=float(sig(b0)), b0=float(b0), auc_cv=float(r['auc_cv']), auc_t=float(r['auc_t']),
                                auc_pts=float(roc_auc_score(P[y], sig(b0 + tot / 10))), cal=cal, senales=sen)
    print(r['nombre'], 'AUC puntos', round(out['categorias'][y]['auc_pts'], 3), [(c['lo'], c['hi'], round(c['pred'], 2), round(c['obs'], 2), c['n']) for c in cal])
for i, row in H.iterrows():
    d = dict(ean=row.ean, desc=DESC.get(row.ean, row.ean), brand=BR.get(row.ean, ''), seg=SEG.get(row.ean, ''), vol12=float(row.s12), c3=float(row.c3))
    for y, pts in PTS.items():
        act = [s for s in pts.index if XH.loc[i, s] == 1]; tot = int(sum(pts[s] for s in act))
        d[y] = float(sig(R[y]['intercept'] + tot / 10)); d[y + '_pts'] = tot; d[y + '_act'] = [(s, int(pts[s])) for s in act]
    out['hoy'].append(d)
out['hoy'] = sorted(out['hoy'], key=lambda d: -d['c3'])
HO = pd.DataFrame(out['hoy'])
pd.set_option('display.width', 250); pd.set_option('display.max_colwidth', 38)
print(HO.head(12)[['desc', 'c3', 'Y_bajo', 'Y_muy_bajo', 'Y_alto', 'Y_muy_alto', 'Y_orden']].round(2).to_string())
# ejemplos de 2026 (fotos limpias): el caso más probable de cada escenario y lo que pasó
for y, pts in PTS.items():
    tot = X[pts.index] @ pts; p = sig(R[y]['intercept'] + tot / 10)
    rec = P[(P.F >= 2026*12+1) & (P.c3 >= 3000)].index
    for j in p[rec].sort_values(ascending=False).head(2).index:
        out['ejemplos'].append(dict(cat=y, desc=DESC.get(P.ean[j], ''), foto=m(int(P.F[j])), p=float(p[j]), pts=int(tot[j]), c3=float(P.c3[j]), a3=float(P.A3[j]),
                                     ratio=float(P.ratio_c[j]), paso=int(P[y][j]), act=[(s, int(pts[s])) for s in pts.index if X.loc[j, s] == 1]))
print(pd.DataFrame(out['ejemplos'])[['cat', 'desc', 'foto', 'p', 'c3', 'a3', 'ratio', 'paso']].round(2).to_string())
json.dump(out, open(S+'/cons_cartas.json', 'w'), ensure_ascii=False, default=float)
