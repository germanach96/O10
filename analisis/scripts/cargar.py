import json, sys, pickle, glob
sys.path.insert(0, '/home/user/O10')
from motor.lector import leer_foto, int_a_mes
cfg = json.load(open('/home/user/O10/motor/config.json'))
fotos = [leer_foto(p, cfg) for p in sorted(glob.glob('/home/user/O10/data/Gucci/Consensus/*.csv'))]
pickle.dump(fotos, open(sys.argv[1], 'wb'))
for f in fotos:
    c = f.codigos
    print(f.etiqueta, len(f.eans), 'meses', int_a_mes(f.meses[0]), int_a_mes(f.meses[-1]), 'act desde', int_a_mes(f.primer_mes_actuals),
          'OS', (c['Article Type']!='Regular Item').sum(), 'scope', c.scope.sum(), f.avisos[:1])
