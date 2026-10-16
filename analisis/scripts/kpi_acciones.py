"""Acciones dirigidas al KPI: calibradas en unas fotos y medidas en otras, sobre el WAPE90 y SPP3 de toda la casa (regulares)."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, S := '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad')
from base import m, ACT, IX, k as kk, T0, EANS, PRIMER
import json
per = json.load(open(S+'/perimetro.json')); K = per['k']
fv = pd.read_pickle(S+'/fva_arm.pkl'); Z = pd.read_pickle(S+'/ind4.pkl')
d = fv[(~fv.os) & fv.h.between(1, 3) & (fv.foto <= 2026*12+5)].copy()
d['cons'] = d.cons_arm.clip(lower=0); d['da'] = d.tda_fut_arm
d = d.merge(Z[['F','ean','mu12','s12','s_cv12','s_last_avg','cut3','last3_vs_rate','zeros3']].rename(columns={'F':'foto'}), on=['foto','ean'], how='left')
# perfil de pedidos del año pasado del propio código: actual del mismo mes LY (armonizado)
i = d.ean.map(IX).to_numpy(); tly = (d.t - 12 - T0).to_numpy()
ok = tly >= 0
ly = np.full(len(d), np.nan); ly[ok] = ACT[i[ok], tly[ok]]
viejo = (d.t - 12) <= 2026*12+0      # meses LY que venían del perímetro viejo en la verdad -> armonizar
ly = np.where(viejo, ly * d.ean.map(K).fillna(1.0).to_numpy(), ly)
d['ly'] = ly
d['edad_t'] = d.t - d.ean.map(dict(zip(EANS, PRIMER)))
A1, A2 = d.foto < 2026*12+1, d.foto >= 2026*12+1       # 2025.M09-2026.M01 (armonizadas) / 2026.M02-M06 (limpias)
def kpi(F_, g): return np.abs(F_ - g.A).sum() / g.A.sum(), (g.A.sum() - F_.sum()) / g.A.sum()
def obj(F_, g): w, s = kpi(F_, g); return w + abs(s)
# --- acciones parametrizadas
def da_corte(g, rho): return np.clip(g.cons - (1 - rho) * g.da.clip(lower=0), 0, None)
def da_neg(g, rho): return np.clip(g.cons - (1 - rho) * g.da.clip(upper=0), 0, None)
def reparto(g, cvmin):
    """Repartir el total de los 3 meses según los meses del año pasado del propio código (calendario de pedidos)."""
    g = g.copy(); key = ['foto','ean']
    tot_c = g.groupby(key).cons.transform('sum'); tot_ly = g.groupby(key).ly.transform('sum')
    usa = (g.s_cv12 >= cvmin) & (tot_ly > 0) & g.ly.notna() & (g.groupby(key).h.transform('count') == 3)
    return np.where(usa, tot_c * g.ly / tot_ly.where(tot_ly > 0, 1), g.cons)
def vacio(g, _): return np.where((g.s_last_avg < .1) & (g.cut3 <= 0) & (g.h == 1), 0.0, g.cons)
ACC = {
  'Recortar el DA positivo (solo llega una parte)': (da_corte, np.linspace(0, 1, 21)),
  'DA negativo: solo se cumple una parte': (da_neg, np.linspace(0, 1, 21)),
  'Repartir los 3 meses según el calendario de pedidos del año pasado': (reparto, [0.0, 0.5, 0.8, 1.0, 1.25, 1.5, 9]),
  'Mes a cero sin cortes: forecast 0 el mes siguiente': (vacio, [0]),
}
w0a, s0a = kpi(d.cons[A2], d[A2]); w0b, s0b = kpi(d.cons[A1], d[A1])
print(f'Base (forecast real): limpias 2026.M02-M06 WAPE90 {w0a:.1%} SPP3 {s0a:+.1%} · armonizadas 2025.M09-2026.M01 WAPE90 {w0b:.1%} SPP3 {s0b:+.1%}')
res = {}
for nm, (fn, grid) in ACC.items():
    out = []
    for cal, test, lab in [(A1, A2, 'cal 25→ test 26'), (A2, A1, 'cal 26→ test 25')]:
        best = min(grid, key=lambda p: obj(fn(d[cal], p), d[cal]))
        w, s = kpi(fn(d[test], best), d[test]); wb, sb = kpi(d.cons[test], d[test])
        out.append((lab, best, wb, w, sb, s))
    res[nm] = out
    print(f'\n{nm}')
    for lab, best, wb, w, sb, s in out:
        print(f'   {lab}: parámetro {best}  WAPE90 {wb:.1%} -> {w:.1%} ({w-wb:+.1%})   SPP3 {sb:+.1%} -> {s:+.1%}')
# combinación con parámetros calibrados en 2025 y medidos en 2026 (limpias)
p_da = res['Recortar el DA positivo (solo llega una parte)'][0][1]; p_dn = res['DA negativo: solo se cumple una parte'][0][1]; p_rep = res['Repartir los 3 meses según el calendario de pedidos del año pasado'][0][1]
g = d[A2].copy(); g['cons'] = da_corte(g, p_da); g['cons'] = da_neg(g, p_dn); g['cons'] = reparto(g, p_rep); g['cons'] = vacio(g, 0)
w, s = kpi(g.cons, g)
print(f'\nTODAS JUNTAS (calibradas en 2025, medidas en 2026 limpias): WAPE90 {w0a:.1%} -> {w:.1%} ({w-w0a:+.1%})   SPP3 {s0a:+.1%} -> {s:+.1%}')
# lanzamientos: sesgo en los primeros meses de vida
print('\nLanzamientos: SPP del forecast real según la edad del código en el mes objetivo (fotos limpias)')
q = d[A2].copy(); q['eb'] = pd.cut(q.edad_t, [-100, -1, 2, 5, 11, 1000], labels=['aún no vendía','meses 1-3','meses 4-6','meses 7-12','> 12 meses'])
for b, gg in q.groupby('eb', observed=True):
    ww, ss = kpi(gg.cons, gg); print(f'   {b:15s} filas {len(gg):4d}  % error {(gg.cons-gg.A).abs().sum()/(q.cons-q.A).abs().sum():4.0%}  WAPE {ww:.0%}  SPP {ss:+.0%}')
pd.to_pickle(dict(res=res, base=(w0a, s0a), todas=(w, s), params=dict(da=p_da, dn=p_dn, rep=p_rep)), S+'/kpi_acciones.pkl')
