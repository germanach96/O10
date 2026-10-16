import pickle, sys, numpy as np, pandas as pd
sys.path.insert(0, '/home/user/O10'); from motor.lector import int_a_mes
P = pickle.load(open(sys.argv[1]+'/panel.pkl','rb')); T=P['truth']; A=P['attrs']
T = T.join(A[['Article Type','Brand','Product Line','Final Segment','Final Responsibility','tamano','primer_mes_venta']], on='ean')
T['os'] = T['Article Type'].ne('Regular Item')
g = T.groupby(['t','os']).agg(act=('act','sum'), epos=('epos','sum'), n_epos=('epos', lambda s: s.notna().sum()), tda=('tda','sum'), cuts=('cuts','sum')).unstack('os')
g.index = [int_a_mes(i) for i in g.index]
pd.set_option('display.width',250); pd.set_option('display.max_rows',200)
print(g.round(0).astype('Int64').to_string())
print(A['Article Type'].value_counts()); print(A['Brand'].value_counts()); print(A['Final Segment'].value_counts()); print(A['Final Responsibility'].value_counts())
print(A.groupby('Brand')['Product Line'].nunique())
