"""Biblioteca de indicadores tipo análisis técnico por código x mes de decisión F (solo info <= F-1) y resultados Y."""
from base import *
import json, re
per = json.load(open(S+'/perimetro.json')); K = per['k']; KB = per['kb']
# --- armonizar meses que vienen de fotos del perímetro viejo (<= 2026.M01)
SRC = mat(T, 'foto_fuente')
kk = np.array([K.get(e, KB.get(BRAND[i], 1.0)) for i, e in enumerate(EANS)])[:, None]
viejo = np.nan_to_num(SRC) <= 2026*12+0
SI = np.where(viejo, ACT*kk, ACT); CU = np.where(viejo, CUT*kk, CUT)
EP = EPOS.copy()
NE, NMm = SI.shape
TAM = ATR['tamano'].to_numpy()
ml = np.array([float(re.match(r'([\d.]+)', t).group(1)) if re.match(r'([\d.]+)', str(t)) else np.nan for t in TAM])
disco = ATR['disco_mes'].to_numpy(float)
# grupos (regulares + OS cuentan en el grupo; se excluye al propio código)
def gsum(M, keys, mask=None):
    out = np.zeros_like(M); M0 = np.nan_to_num(M) if mask is None else np.where(mask[:, None], np.nan_to_num(M), 0)
    for g in np.unique(keys):
        idx = keys == g; out[idx] = M0[idx].sum(0)
    return out
REG = ~OS
SI_pl = gsum(SI, PL, REG) - np.where(REG[:, None], SI, 0); SI_br = gsum(SI, BRAND, REG) - np.where(REG[:, None], SI, 0)
SI_ho = np.nansum(np.where(REG[:, None], SI, 0), 0)[None, :] - np.where(REG[:, None], SI, 0)
EPz = np.nan_to_num(EP)
EP_pl = gsum(EPz, PL, REG) - np.where(REG[:, None], EPz, 0); EP_br = gsum(EPz, BRAND, REG) - np.where(REG[:, None], EPz, 0)
EP_ho = EPz[REG].sum(0)[None, :] - np.where(REG[:, None], EPz, 0)
OS_pl = gsum(SI, PL, OS); OS_br = gsum(SI, BRAND, OS)
REG_pl_tot = gsum(SI, PL, REG); REG_br_tot = gsum(SI, BRAND, REG)
EP_ok = ~np.isnan(EP).all(0)   # meses con EPOS cargado
# lanzamientos regulares por PL/brand y mes (primera venta)
LAN = np.zeros_like(SI); LANV = np.zeros_like(SI)
for i in np.where(REG & (PRIMER >= T0 + 1))[0]:
    LAN[i, k(PRIMER[i])] = 1; LANV[i, k(PRIMER[i])] = SI[i, k(PRIMER[i]):k(PRIMER[i])+6].sum()
LAN_pl = gsum(LAN, PL); LAN_br = gsum(LAN, BRAND); LANV_pl = gsum(LANV, PL); LANV_br = gsum(LANV, BRAND)
SAMESIZE_NEW = np.zeros(NE, int)
L = lambda a, b: np.log((a + 1) / (b + 1))
def w(M, a, b):  # suma meses absolutos [a, b]; NaN si la ventana sale del panel
    if k(a) < 0 or k(b) >= NMm: return np.full(M.shape[0], np.nan)
    return M[:, k(a):k(b)+1].sum(1)
def wn(M, a, b):
    if k(a) < 0 or k(b) >= NMm: return np.full(M.shape[0], np.nan)
    X = M[:, k(a):k(b)+1]; return np.where(np.isnan(X).any(1), np.nan, np.nansum(X, 1))
rows = []
for F in range(T0 + 15, T1 + 2):   # YoY de 3M necesita 15 meses; F = T1+1 es la foto actual (sin resultados)
    d = {'F': np.full(NE, F), 'ean': np.array(EANS), 'i': np.arange(NE)}
    s1, s3, s6, s12 = SI[:, k(F-1)], w(SI, F-3, F-1), w(SI, F-6, F-1), w(SI, F-12, F-1)
    s1l, s3l, s6l, s12l = SI[:, k(F-13)], w(SI, F-15, F-13), w(SI, F-18, F-13), w(SI, F-24, F-13)
    sp3, sp3l = w(SI, F-6, F-4), w(SI, F-18, F-16)
    mu = s12 / 12
    d.update(s_yoy1=L(s1, s1l), s_yoy3=L(s3, s3l), s_yoy6=L(s6, s6l), s_yoy12=L(s12, s12l))
    d['s_acc'] = d['s_yoy3'] - d['s_yoy12']; d['s_acc2'] = d['s_yoy3'] - d['s_yoy6']
    d['s_mom3_sa'] = L(s3, sp3) - L(s3l, sp3l)          # cambio trimestral menos el del año pasado
    X12 = SI[:, k(F-12):k(F)]
    d['s_cv12'] = X12.std(1) / np.maximum(X12.mean(1), 1e-9); d['s_zeros12'] = (X12 <= 0).sum(1)
    r3 = np.array([X12[:, j:j+3].sum(1) for j in range(10)]).T
    d['s_dd'] = s3 / np.maximum(r3.max(1), 1)
    yo = np.array([L(SI[:, k(F-j)], SI[:, k(F-12-j)]) if k(F-12-j) >= 0 else np.full(NE, np.nan) for j in range(1, 7)]).T
    d['s_up6'] = np.where(np.isnan(yo).any(1), np.nan, (yo > 0).mean(1))
    d['s_last_avg'] = s1 / np.maximum(mu, 1e-9)
    big = X12 >= np.maximum(2*np.median(X12, 1), 1.5*X12.mean(1))[:, None]
    last_big = np.where(big.any(1), 12 - (11 - np.argmax(big[:, ::-1], 1)), 13)
    d['s_ms_big'] = np.where(big.any(1), 12 - np.array([np.where(b)[0].max() if b.any() else -1 for b in big]), 13)
    tt = np.arange(12); lx = np.log1p(X12); d['s_slope12'] = ((lx - lx.mean(1, keepdims=True)) * (tt - tt.mean())).sum(1) / ((tt - tt.mean())**2).sum()
    d['s_ly_next3_vs_last3'] = L(w(SI, F-11, F-9), s3l)     # estacionalidad esperada: próximos 3 meses del año pasado vs sus 3 previos
    d['log_vol12'] = np.log1p(s12)
    # EPOS
    e3, e6, e12 = wn(EP, F-3, F-1), wn(EP, F-6, F-1), wn(EP, F-12, F-1)
    e3l, e6l, ep3 = wn(EP, F-15, F-13), wn(EP, F-18, F-13), wn(EP, F-6, F-4)
    d.update(e_yoy3=L(e3, e3l), e_yoy6=L(e6, e6l), e_mom3=L(e3, ep3))
    d['e_acc'] = d['e_yoy3'] - d['e_yoy6']
    d['e_mom3_sa'] = d['e_mom3'] - L(e3l, wn(EP, F-18, F-16))
    kap = e12 / np.maximum(s12, 1)
    d['st3'] = (e3 / np.maximum(s3, 1)) / np.where(kap > 0, kap, np.nan)          # sell-through relativo
    d['st3_raw'] = e3 / np.maximum(s3, 1)
    d['stock6'] = (s6 - e6 / np.where(kap > 0, kap, np.nan)) / np.maximum(mu, 1)   # carga del canal (meses de venta)
    d['div3'] = d['s_yoy3'] - d['e_yoy3']
    d['div_mom'] = L(s3, sp3) - d['e_mom3']
    # grupos (sin el propio código)
    for nm, G, E_ in [('pl', SI_pl, EP_pl), ('br', SI_br, EP_br), ('ho', SI_ho, EP_ho)]:
        d[f'{nm}_s_yoy3'] = L(w(G, F-3, F-1), w(G, F-15, F-13)); d[f'{nm}_s_yoy12'] = L(w(G, F-12, F-1), w(G, F-24, F-13))
        ok3 = k(F-15) >= 0 and EP_ok[k(F-15)] and EP_ok[k(F-1)]
        d[f'{nm}_e_yoy3'] = L(w(E_, F-3, F-1), w(E_, F-15, F-13)) if ok3 and EP_ok[k(F-3)] and EP_ok[k(F-13)] else np.full(NE, np.nan)
        d[f'rs_{nm}'] = d['s_yoy3'] - d[f'{nm}_s_yoy3']
        d[f'rs_{nm}_e'] = d['e_yoy3'] - d[f'{nm}_e_yoy3']
    d['pl_share_chg'] = L(s3, w(REG_pl_tot, F-3, F-1)) - L(s12, w(REG_pl_tot, F-12, F-1))
    # lanzamientos y one shots en el grupo
    d['lan_pl_6'] = w(LAN_pl, F-6, F-1) - np.where(REG & (PRIMER >= F-6) & (PRIMER <= F-1), 1, 0)
    d['lan_br_6'] = w(LAN_br, F-6, F-1) - np.where(REG & (PRIMER >= F-6) & (PRIMER <= F-1), 1, 0)
    d['lanv_br_6'] = w(LANV_br, F-6, F-1) / np.maximum(w(REG_br_tot, F-6, F-1), 1)
    d['lan_pl_next3'] = w(LAN_pl, F+1, F+3) if F+3 <= T1 else np.full(NE, np.nan)   # plan de lanzamientos (conocido de antemano)
    d['lan_br_next3'] = w(LAN_br, F+1, F+3) if F+3 <= T1 else np.full(NE, np.nan)
    d['os_pl3'] = w(OS_pl, F-3, F-1) / np.maximum(w(REG_pl_tot, F-3, F-1), 1)
    d['os_br3'] = w(OS_br, F-3, F-1) / np.maximum(w(REG_br_tot, F-3, F-1), 1)
    d['os_br_yoy3'] = L(w(OS_br, F-3, F-1), w(OS_br, F-15, F-13))
    # cortes, edad, atributos
    d['cut3'] = w(CU, F-3, F-1) / np.maximum(mu, 1); d['cut_any6'] = (w(CU, F-6, F-1) > 0).astype(float)
    d['edad'] = np.where(PRIMER > 0, F - PRIMER, np.nan)
    d['meses_a_disco'] = disco - F
    d['ml'] = ml; d['os'] = OS.astype(float); d['local'] = LOCAL.astype(float)
    d['mes_obj'] = (F + 1) % 12 + 1          # mes natural del primer mes objetivo
    # resultados
    if F + 3 <= T1:
        y3, y3l = w(SI, F+1, F+3), w(SI, F-11, F-9)
        d['y3'] = y3; d['y3_ly'] = y3l; d['Y_yoy3'] = L(y3, y3l)
        d['Y_vs_last3'] = L(y3, s3)
    if F + 1 <= T1:
        a1 = SI[:, k(F+1)]
        d['Y_big1'] = (a1 >= np.maximum(2*np.median(X12, 1), 1.5*X12.mean(1))).astype(float)
        d['Y_ratio1'] = a1 / np.maximum(mu, 1e-9)
    rows.append(pd.DataFrame(d))
Z = pd.concat(rows, ignore_index=True)
Z['seg'] = Z.ean.map(ATR['Final Segment']); Z['brand'] = Z.ean.map(ATR['Brand'])
Z['s12'] = np.expm1(Z.log_vol12)
Z.to_pickle(S+'/ind.pkl')
print(Z.shape, 'F', m(Z.F.min()), m(Z.F.max()))
print([c for c in Z.columns])
