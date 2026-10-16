"""Walk-forward: elegir receta con lo que se sabía en la foto F y medirla en el tramo 1 (meses F+1..F+3) de F."""
import numpy as np, pandas as pd, json, sys
sys.path.insert(0, '/home/user/O10'); from motor.lector import mes_a_int
S = '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad'
FOTOS = ['2025.M09','2025.M10','2025.M11','2025.M12','2026.M01','2026.M02','2026.M03','2026.M04','2026.M05','2026.M06']
D = {f: dict(np.load(f'{S}/np_{f}.npz', allow_pickle=True)) for f in FOTOS}
res = json.load(open(S+'/resultados.json'))['resumenes']
edad = {r['foto']: {e: c['tramo_edad'] for e, c in r['codigos'].items()} for r in res}
import pickle
P = pickle.load(open(S+'/panel.pkl','rb')); A = P['attrs']
W = np.array([4., 2., 1.])
NR = 75816
def entrenamiento(F):
    """(foto, tramo) disponibles en F: último mes del tramo <= F-1"""
    fi = mes_a_int(F); out = []
    for f in FOTOS:
        for j in range(3):
            if mes_a_int(f) + 3*(j+1) <= fi - 1 and D[f]['cer'][:, j].any():
                out.append((f, j))
    return out
def acumular(F):
    tr = entrenamiento(F)
    num, den, cnt = {}, {}, {}
    for f, j in tr:
        d = D[f]
        for i, e in enumerate(d['eans']):
            if not d['cer'][i, j]: continue
            a = np.where(d['val'][i], d['abs'][i, :, j], np.nan).astype(np.float64)
            if e not in num:
                num[e] = np.zeros(NR); den[e] = 0.0; cnt[e] = np.zeros(NR)
            num[e] += W[j]*np.nan_to_num(a); cnt[e] += W[j]*(~np.isnan(a)); den[e] += W[j]*float(d['act'][i, j])
    # recetas con cobertura completa
    for e in num:
        full = cnt[e] >= cnt[e].max() - 1e-9
        num[e] = np.where(full, num[e], np.inf)
    return num, den, tr
NIVELES = ['Código', 'Product Line', 'Brand', 'Segmento', 'Edad', 'Casa']
def clave(nivel, e, F):
    if nivel == 'Código': return e
    if nivel == 'Product Line': return A.loc[e, 'Product Line']
    if nivel == 'Brand': return A.loc[e, 'Brand']
    if nivel == 'Segmento': return A.loc[e, 'Final Segment']
    if nivel == 'Edad': return edad[F].get(e, '?')
    return 'Casa'
filas = []
for F in FOTOS:
    if mes_a_int(F) < mes_a_int(FOTOS[0]) + 4: continue
    num, den, tr = acumular(F)
    d = D[F]; test = [i for i, e in enumerate(d['eans']) if d['cer'][i, 0] and e in num]
    act = sum(float(d['act'][i, 0]) for i in test)
    cons = sum(float(d['cabs'][i, 0]) for i in test); csg = sum(float(d['csgn'][i, 0]) for i in test)
    orac = sum(float(np.nanmin(np.where(d['val'][i], d['abs'][i, :, 0], np.nan))) for i in test)
    fila = dict(F=F, n=len(test), act=act, entren=len(tr), Consensus=cons/act, SPP_cons=-csg/act, Oraculo_ex_post=orac/act)
    for nivel in NIVELES:
        grupos = {}
        for e in num:
            grupos.setdefault(clave(nivel, e, F), []).append(e)
        gscore = {g: sum(num[e] for e in es) / max(sum(den[e] for e in es), 1e-9) for g, es in grupos.items()}
        tot = 0.0; sg = 0.0
        for i in test:
            e = d['eans'][i]; sc = gscore[clave(nivel, e, F)]
            sc = np.where(d['val'][i], sc, np.inf)
            r = int(np.argmin(sc)); tot += float(d['abs'][i, r, 0]); sg += float(d['sgn'][i, r, 0])
        fila[nivel] = tot/act; fila['SPP_'+nivel] = -sg/act
    filas.append(fila); print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in fila.items()}, flush=True)
R = pd.DataFrame(filas); R.to_pickle(S+'/wf.pkl')
tot = R.act.sum()
print('\nWAPE90 fuera de muestra, agregado sobre las fotos de prueba (ponderado por actuals):')
for c in ['Consensus'] + NIVELES + ['Oraculo_ex_post']:
    print(f'   {c:16s} {(R[c]*R.act).sum()/tot:.1%}   gana al Consensus en {(R[c] < R.Consensus).sum()}/{len(R)} fotos' + (f'   SPP {(R["SPP_"+c]*R.act).sum()/tot:+.1%}' if 'SPP_'+c in R else ''))
