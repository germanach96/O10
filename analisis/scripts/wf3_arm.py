"""Walk-forward con el respaldo del motor (receta inválida en un código -> la misma sin trend)."""
import numpy as np, pandas as pd, json, sys, pickle
sys.path.insert(0, '/home/user/O10'); from motor.lector import mes_a_int
S = '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad'
FOTOS = ['2025.M09','2025.M10','2025.M11','2025.M12','2026.M01','2026.M02','2026.M03','2026.M04','2026.M05','2026.M06']
RC = pd.read_csv(S+'/recetas.csv'); NR = len(RC)
key = ['s','h','e','c','p']
fb = RC.merge(RC[(RC.w==0)&(RC.m==0)&(RC.N==6)&(RC.g==0)][key+['receta']].rename(columns={'receta':'fb'}), on=key, how='left').fb.to_numpy()
D = {f: dict(np.load(f'{S}/nparm_{f}.npz', allow_pickle=True)) for f in FOTOS}
for f in FOTOS:   # aplicar respaldo
    d = D[f]; v = d['val'][:, :, None]
    d['absR'] = np.where(v, d['abs'], d['abs'][:, fb, :]); d['sgnR'] = np.where(v, d['sgn'], d['sgn'][:, fb, :])
res = json.load(open(S+'/resultados_arm.json'))['resumenes']
edad = {r['foto']: {e: c['tramo_edad'] for e, c in r['codigos'].items()} for r in res}
A = pickle.load(open(S+'/panel.pkl','rb'))['attrs']
W = np.array([4., 2., 1.])
def clave(nivel, e, F):
    return {'Código': e, 'Product Line': A.loc[e,'Product Line'], 'Brand': A.loc[e,'Brand'], 'Segmento': A.loc[e,'Final Segment'],
            'Edad': edad[F].get(e,'?'), 'Casa': 'Casa', 'Brand×Segmento': (A.loc[e,'Brand'], A.loc[e,'Final Segment'])}[nivel]
NIV = ['Código (sin respaldo)', 'Código', 'Product Line', 'Brand', 'Brand×Segmento', 'Segmento', 'Edad', 'Casa']
filas = []; elecciones = {}
for F in FOTOS:
    fi = mes_a_int(F)
    tr = [(f, j) for f in FOTOS for j in range(3) if mes_a_int(f) + 3*(j+1) <= fi - 1]
    if not tr: continue
    num, numR, den, val = {}, {}, {}, {}
    for f, j in tr:
        d = D[f]
        for i, e in enumerate(d['eans']):
            if not d['cer'][i, j]: continue
            num[e] = num.get(e, 0) + W[j]*d['abs'][i, :, j].astype(np.float64)
            numR[e] = numR.get(e, 0) + W[j]*d['absR'][i, :, j].astype(np.float64)
            den[e] = den.get(e, 0) + W[j]*float(d['act'][i, j]); val[e] = val.get(e, True) & d['val'][i]
    d = D[F]; test = [i for i, e in enumerate(d['eans']) if d['cer'][i, 0] and e in num]
    act = sum(float(d['act'][i, 0]) for i in test)
    fila = dict(F=F, n=len(test), act=act, entren=len(tr), Consensus=sum(float(d['cabs'][i,0]) for i in test)/act,
                SPP_Consensus=-sum(float(d['csgn'][i,0]) for i in test)/act,
                Oraculo=sum(float(np.nanmin(np.where(d['val'][i], d['abs'][i,:,0], np.nan))) for i in test)/act)
    for nivel in NIV:
        niv = 'Código' if nivel.startswith('Código') else nivel
        grupos = {}
        for e in num: grupos.setdefault(clave(niv, e, F), []).append(e)
        if nivel == 'Código (sin respaldo)':
            sc = {e: np.where(val[e], num[e], np.inf) / max(den[e], 1e-9) for e in num}
            gs = lambda e: sc[e]
        else:
            g_sc = {g: sum(numR[e] for e in es) / max(sum(den[e] for e in es), 1e-9) for g, es in grupos.items()}
            gs = lambda e: g_sc[clave(niv, e, F)]
        tot = sg = 0.0
        for i in test:
            e = d['eans'][i]; r = int(np.argmin(gs(e)))
            tot += float(d['absR'][i, r, 0]); sg += float(d['sgnR'][i, r, 0])
            elecciones[(F, nivel, e)] = r
        fila[nivel] = tot/act; fila['SPP_'+nivel] = -sg/act
    filas.append(fila)
R = pd.DataFrame(filas); R.to_pickle(S+'/wf3_arm.pkl'); pickle.dump(elecciones, open(S+'/wf3_arm_elec.pkl','wb'))
pd.set_option('display.width', 250)
print(R[['F','n','entren','Consensus','Oraculo'] + NIV].round(2).to_string(index=False))
t = R.act.sum()
print('\nWAPE90 fuera de muestra (6 fotos de prueba, ponderado):')
for c in ['Consensus'] + NIV + ['Oraculo']:
    s = f'   SPP {(R["SPP_"+c]*R.act).sum()/t:+.0%}' if 'SPP_'+c in R else ''
    print(f'   {c:22s} {(R[c]*R.act).sum()/t:.1%}   mejor que Consensus en {(R[c] < R.Consensus).sum()}/{len(R)} fotos{s}')
