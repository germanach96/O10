"""Tabla código x mes de decisión F con features (solo meses <= F-1) y objetivos (F+1..F+3, F+4..F+6)."""
from base import *
def sw(M, a, b):  # suma meses [a,b] absolutos
    ka, kb = k(a), k(b)
    if ka < 0 or kb >= NM: return np.full(M.shape[0], np.nan)
    return M[:, ka:kb+1].sum(1)
def swn(M, a, b):  # suma con NaN si falta algún mes
    ka, kb = k(a), k(b)
    if ka < 0 or kb >= NM: return np.full(M.shape[0], np.nan)
    X = M[:, ka:kb+1]; return np.where(np.isnan(X).any(1), np.nan, np.nansum(X,1))
# códigos de un grupo: suma de otros códigos (hermanos) de la misma PL y brand
def grupo_sum(M, keys, excl_self=True):
    out = np.zeros_like(M)
    df = pd.DataFrame({'k': keys})
    for kk, idx in df.groupby('k').groups.items():
        idx = np.array(list(idx)); s = np.nansum(M[idx], 0)
        out[idx] = s - (np.nan_to_num(M[idx]) if excl_self else 0)
    return out
rows = []
for F in range(2023*12+3, T1-2):   # F con objetivo F+1..F+3 cerrado
    d = dict(F=np.full(len(EANS), F), ean=np.array(EANS))
    d['y3'] = sw(ACT, F+1, F+3); d['y6'] = sw(ACT, F+4, F+6) if F+6 <= T1 else np.full(len(EANS), np.nan)
    d['cur'] = ACT[:, k(F)]
    d['y3_ly'] = sw(ACT, F-11, F-9)
    d['si3'] = sw(ACT, F-3, F-1); d['si3_ly'] = sw(ACT, F-15, F-13); d['si12'] = sw(ACT, F-12, F-1); d['si12_ly'] = sw(ACT, F-24, F-13) if F-24>=T0 else np.full(len(EANS), np.nan)
    d['si6'] = sw(ACT, F-6, F-1)
    d['ep3'] = swn(EPOS, F-3, F-1); d['ep3_ly'] = swn(EPOS, F-15, F-13); d['ep12'] = swn(EPOS, F-12, F-1); d['ep6'] = swn(EPOS, F-6, F-1)
    d['ep_prev3'] = swn(EPOS, F-6, F-4)
    d['cut3'] = sw(CUT, F-3, F-1)
    d['last1'] = ACT[:, k(F-1)]
    rows.append(pd.DataFrame(d))
X = pd.concat(rows, ignore_index=True)
X = X.join(ATR[['Article Type','Brand','Product Line','Final Segment','Final Responsibility']], on='ean')
X['os'] = X['Article Type'].ne('Regular Item')
X['primer'] = X.ean.map(dict(zip(EANS, PRIMER)))
X['edad'] = X.F - X.primer
X.to_pickle(S+'/feats.pkl'); print(X.shape, X.F.min(), X.F.max())
