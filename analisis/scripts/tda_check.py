import pickle, sys, numpy as np, pandas as pd
sys.path.insert(0, '/home/user/O10'); from motor.lector import int_a_mes
P = pickle.load(open(sys.argv[1]+'/panel.pkl','rb')); H=P['hist_all']; fc=P['fc']
# TDA pasado según cada foto
p = H.groupby(['foto','t']).tda.sum().unstack('foto')
p = p.loc[p.index>=24300]
p.index=[int_a_mes(i) for i in p.index]; p.columns=[int_a_mes(c)[2:] for c in p.columns]
pd.set_option('display.width',250)
print(p.round(0).astype('Int64').to_string())
# TDA futuro según cada foto (h 1..9)
q = fc.groupby(['foto','t']).tda_fut.sum().unstack('foto')
q.index=[int_a_mes(i) for i in q.index]; q.columns=[int_a_mes(c)[2:] for c in q.columns]
print(q.round(0).astype('Int64').to_string())
