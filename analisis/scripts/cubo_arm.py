"""Cubo con las fotos 2025.M09-2026.M01 armonizadas al perímetro nuevo (factor por código = actuals nuevos / viejos 2024-2025)."""
import sys, json, pickle, time, glob
sys.path.insert(0, '/home/user/O10')
from pathlib import Path
import numpy as np, pandas as pd
from motor.pipeline import *
from motor.lector import leer_foto, agregar_desaparecidos
S = Path(sys.argv[1]); cfg = cargar_config(); R = Rejilla(cfg)
fotos = sorted([leer_foto(p, cfg) for p in sorted(glob.glob('/home/user/O10/data/Gucci/Consensus/*.csv'))], key=lambda f: f.mes)
viejo = [f for f in fotos if f.mes <= 2026*12+0]; nuevo = next(f for f in fotos if f.mes == 2026*12+1); ref = viejo[-1]
sel = lambda f: (f.meses >= 2024*12) & (f.meses <= 2025*12+11)
so = dict(zip(ref.eans, np.nansum(ref.mat['Actuals'][:, sel(ref)], 1)))
sn = dict(zip(nuevo.eans, np.nansum(nuevo.mat['Actuals'][:, sel(nuevo)], 1)))
brand = pd.concat([ref.codigos['Brand'], nuevo.codigos['Brand']]); brand = brand[~brand.index.duplicated()]
kb = {}
for b in brand.unique():
    es = [e for e in brand.index[brand == b] if e in so and e in sn]
    o, n = sum(so[e] for e in es), sum(sn[e] for e in es); kb[b] = n / o if o > 0 else 1.0
k = {}
for e in set(so) | set(sn):
    o, n = so.get(e, 0), sn.get(e, np.nan)
    if np.isnan(n): k[e] = kb.get(brand.get(e), 1.0)          # salió del export: factor de su brand
    elif o >= 50: k[e] = float(np.clip(n / o, 0.5, 5))
    else: k[e] = kb.get(brand.get(e), 1.0)
solo_nuevo = [e for e in sn if so.get(e, 0) < 0.1 * sn[e] and sn[e] >= 100]
json.dump({'k': k, 'kb': kb, 'solo_nuevo': solo_nuevo}, open(S/'perimetro.json', 'w'))
print('factor por brand', {b[:20]: round(v, 2) for b, v in kb.items()}, ' códigos casi solo en el perímetro nuevo:', len(solo_nuevo))
for f in viejo:
    kk = np.array([k.get(e, kb.get(f.codigos.loc[e, 'Brand'], 1.0)) for e in f.eans])[:, None]
    for c in ['Actuals', 'Supply Cuts', 'Total Demand Assumption', 'Consensus - Final', 'hist']:
        f.mat[c] = f.mat[c] * kk
agregar_desaparecidos(fotos)
t0 = time.time(); res = []
for f in fotos:
    r = calcular_foto(f, fotos, cfg, R, ()); escribir_cubo(r, R, S/'cubo_arm'); res.append(r)
    print(f.etiqueta, len(r.scope), round(time.time()-t0), flush=True)
rs = [resumen_foto(r, cfg, R) for r in res]
elegida, num, sgn, den = score_multifoto(res, cfg, R)
json.dump({'resumenes': rs, 'elegida': elegida}, open(S/'resultados_arm.json', 'w'), default=str)
print('ok')
