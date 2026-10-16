import sys, json, pickle, time
sys.path.insert(0, '/home/user/O10')
from pathlib import Path
from motor.pipeline import *
from motor.lector import leer_foto, agregar_desaparecidos
S = Path(sys.argv[1]); cfg = cargar_config(); R = Rejilla(cfg)
import glob
fotos = sorted([leer_foto(p, cfg) for p in sorted(glob.glob('/home/user/O10/data/Gucci/Consensus/*.csv'))], key=lambda f: f.mes)
agregar_desaparecidos(fotos)
t0=time.time(); res=[]
for f in fotos:
    r = calcular_foto(f, fotos, cfg, R, ())
    escribir_cubo(r, R, S/'cubo'); res.append(r)
    print(f.etiqueta, len(r.scope), time.time()-t0, flush=True)
rs = [resumen_foto(r, cfg, R) for r in res]
elegida, num, sgn, den = score_multifoto(res, cfg, R)
json.dump({'resumenes': rs, 'elegida': elegida}, open(S/'resultados.json','w'), default=str)
tabla_recetas(R).to_csv(S/'recetas.csv')
print('ok', time.time()-t0)
