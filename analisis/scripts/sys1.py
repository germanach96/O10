import pickle, numpy as np, pandas as pd, sys
sys.path.insert(0, S:='/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad')
fotos = pickle.load(open(S+'/fotos.pkl','rb'))
rows = []
for f in fotos:
    d = f.df[(f.df.t > f.mes) & (f.df.t <= f.mes + 9)][['EAN','t','System FC - Final','Consensus - Final','Total Demand Assumption','Initiative Forecast','Prometheus Fcst Consensus','Ignore System Forecast Flag','Final Segment']].copy()
    d['foto'] = f.mes; rows.append(d)
D = pd.concat(rows).rename(columns={'EAN':'ean','System FC - Final':'sys','Consensus - Final':'cons2','Initiative Forecast':'init','Prometheus Fcst Consensus':'prom','Ignore System Forecast Flag':'flag','Final Segment':'seg_foto'})
for c in ['sys','cons2','init','prom','Total Demand Assumption']: D[c] = D[c].fillna(0)
D.to_pickle(S+'/sysfc.pkl'); print(D.shape); print(D[['sys','cons2','init','prom']].describe().round(1))
print(D.flag.value_counts(dropna=False))
