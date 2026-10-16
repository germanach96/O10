"""Panel maestro: una fila por EAN x mes con la verdad (de la foto más reciente que cubre el mes) y atributos."""
import pickle, sys, numpy as np, pandas as pd
sys.path.insert(0, '/home/user/O10')
from motor.lector import int_a_mes
S = sys.argv[1]
fotos = sorted(pickle.load(open(f'{S}/fotos.pkl','rb')), key=lambda f: f.mes)
rows = []
for f in fotos:
    pas = f.meses < f.mes
    for c in ['Actuals','Supply Cuts','Total Demand Assumption','EPOS','Consensus - Final','hist']:
        pass
    M = {c: f.mat[c] for c in ['Actuals','Supply Cuts','Total Demand Assumption','EPOS','Consensus - Final','hist']}
    idx = np.where(pas)[0]
    for i, e in enumerate(f.eans):
        for k in idx:
            rows.append((f.mes, e, int(f.meses[k]), M['hist'][i,k], M['Supply Cuts'][i,k], M['Total Demand Assumption'][i,k], M['EPOS'][i,k]))
hist = pd.DataFrame(rows, columns=['foto','ean','t','act','cuts','tda','epos'])
# verdad: foto más reciente que trae el código y el mes (mes < foto)
hist = hist.sort_values('foto')
last = hist.groupby(['ean','t']).tail(1).copy()
# EPOS: el más reciente no nulo
ep = hist.dropna(subset=['epos']).groupby(['ean','t']).tail(1)[['ean','t','epos']]
last = last.drop(columns='epos').merge(ep, on=['ean','t'], how='left')
last = last.rename(columns={'foto':'foto_fuente'})
# códigos que salieron del export: meses posteriores a su última foto -> 0
ult_foto = hist.groupby('ean').foto.max()
last['act'] = last['act']
# atributos: de la última foto que trae el código
attrs = []
for f in fotos:
    a = f.codigos.copy(); a['foto']=f.mes; a.index.name='ean'; attrs.append(a.reset_index())
attrs = pd.concat(attrs)
attrs_last = attrs.sort_values('foto').groupby('ean').tail(1).set_index('ean')
attrs_last['ultima_foto'] = ult_foto
# forecast por foto (futuro)
fc = []
for f in fotos:
    fut = (f.meses > f.mes) & (f.meses <= f.mes + 12)
    k = np.where(fut)[0]
    for i, e in enumerate(f.eans):
        for kk in k:
            fc.append((f.mes, e, int(f.meses[kk]), f.mat['Consensus - Final'][i,kk], f.mat['Total Demand Assumption'][i,kk], f.mat['Supply Cuts'][i,kk]))
fc = pd.DataFrame(fc, columns=['foto','ean','t','cons','tda_fut','cuts_fut'])
fc['h'] = fc.t - fc.foto
pickle.dump({'truth': last, 'hist_all': hist, 'attrs_all': attrs, 'attrs': attrs_last, 'fc': fc}, open(f'{S}/panel.pkl','wb'))
print(last.shape, fc.shape, attrs_last.shape)
print('rango verdad', int_a_mes(last.t.min()), int_a_mes(last.t.max()))
