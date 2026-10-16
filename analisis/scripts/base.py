"""Matrices EAN x mes de la verdad + forecasts por foto. Uso: from base import *"""
import pickle, sys, numpy as np, pandas as pd
sys.path.insert(0, '/home/user/O10'); from motor.lector import int_a_mes
S = '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad'
P = pickle.load(open(S+'/panel.pkl','rb'))
T, H, A, FC = P['truth'], P['hist_all'], P['attrs'], P['fc']
EANS = sorted(A.index); IX = {e:i for i,e in enumerate(EANS)}
T0, T1 = 2022*12+2, 2026*12+8          # 2022.M03 .. 2026.M09 (meses cerrados con historia)
MESES = np.arange(T0, T1+1); NM = len(MESES)
def mat(df, col, fill=np.nan):
    M = np.full((len(EANS), NM), fill)
    d = df[(df.t>=T0)&(df.t<=T1)]
    M[d.ean.map(IX).to_numpy(), (d.t-T0).to_numpy()] = d[col].to_numpy(float)
    return M
ACT = np.nan_to_num(mat(T,'act'))      # vacío = 0
CUT = np.nan_to_num(mat(T,'cuts'))
EPOS = mat(T,'epos')                     # NaN = sin dato
EPOS[:, MESES < 2024*12+6] = np.nan      # EPOS empieza en 2024.M07
# DA definitivo del mes t = el de la foto t+1 (las fotos borran DAs de más de ~8 meses); antes de 2025.M09, el de la foto 2025.M09
fotos = sorted(H.foto.unique())
H2 = H.copy(); H2['d'] = H2.foto - H2.t
prim = H2[H2.foto == fotos[0]]
sig = H2[H2.d == 1]
tda = pd.concat([prim[prim.t < fotos[0]-1], sig]).drop_duplicates(['ean','t'], keep='last')
DA = mat(tda, 'tda')
DA_OK = np.zeros(NM, bool); DA_OK[MESES >= fotos[0]-8-1] = True   # meses con DA conocido
DA[:, ~DA_OK] = np.nan; DA[:, DA_OK] = np.nan_to_num(DA[:, DA_OK])
ATR = A.reindex(EANS)
OS = ATR['Article Type'].ne('Regular Item').to_numpy()
LOCAL = ATR['Final Responsibility'].eq('Local').to_numpy()
BRAND = ATR['Brand'].to_numpy(); PL = ATR['Product Line'].to_numpy(); SEG = ATR['Final Segment'].to_numpy()
# primer mes de venta en la verdad (lanzamiento) — solo fiable si > 2022.M04
vende = ACT > 0
PRIMER = np.where(vende.any(1), MESES[vende.argmax(1)], -1)
def m(i): return int_a_mes(i)
def k(t): return t - T0
FOTOS = fotos
def cons(foto, h_from=1, h_to=3):
    """Consensus de la foto para h en [h_from, h_to] sumado por EAN -> vector"""
    d = FC[(FC.foto==foto)&(FC.h>=h_from)&(FC.h<=h_to)].groupby('ean').cons.sum()
    return d.reindex(EANS).fillna(0).to_numpy()
def dafut(foto, h_from=1, h_to=3):
    d = FC[(FC.foto==foto)&(FC.h>=h_from)&(FC.h<=h_to)].groupby('ean').tda_fut.sum()
    return d.reindex(EANS).fillna(0).to_numpy()
EN_FOTO = {f: np.isin(EANS, H[H.foto==f].ean.unique()) for f in fotos}
