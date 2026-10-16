"""¿Qué habría pasado con el WAPE y el SPP si se aplicaban las acciones de las señales al forecast real (Consensus)?"""
import numpy as np, pandas as pd, json, sys
sys.path.insert(0, S := '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad')
from base import m
L = np.log
Z = pd.read_pickle(S+'/ind4.pkl')
P = Z[(Z.os == 0) & (Z.s12 >= 150) & (Z.edad >= 13)].copy()
sano = (P.last3_vs_rate >= .6) & (P.zeros3 == 0)
f = lambda c: c.fillna(False).astype(bool)
sig = pd.DataFrame(index=P.index)
sig['C'] = sano & (f((P.s_cv12 >= .9) & (P.s12 < 4000) & (P.s_last_avg < .3)).astype(int) + f((P.rs_br >= L(4)) & (P.s_cv12 >= .9)).astype(int)
          + f((P.rs_pl >= L(6)) & (P.pl_s_yoy3 <= L(.6))).astype(int) + f((P.os_br3 >= .7) & (P.ml >= 150)).astype(int)
          + f((P.s_cv12 >= 1.25) & (P.s12 < 4000)).astype(int) >= 2)
sig['C1'] = sano & ((f((P.s_cv12 >= .9) & (P.s12 < 4000) & (P.s_last_avg < .3)).astype(int) + f((P.rs_br >= L(4)) & (P.s_cv12 >= .9)).astype(int)
          + f((P.rs_pl >= L(6)) & (P.pl_s_yoy3 <= L(.6))).astype(int) + f((P.os_br3 >= .7) & (P.ml >= 150)).astype(int)
          + f((P.s_cv12 >= 1.25) & (P.s12 < 4000)).astype(int)) == 1)
sig['M'] = sano & (f((P.s12 < 4000) & (P.s_cv12 >= 1) & (P.pl_s_yoy3 <= L(.7))).astype(int) + f((P.seg == 'Rabbits') & (P.rs_br_e <= L(.75))).astype(int)
          + f((P.s_cv12 >= 1.25) & (P.s_ms_big <= 3)).astype(int) + f((P.ml >= 150) & (P.s_ms_big <= 2)).astype(int)
          + f((P.s12 < 4000) & (P.pl_s_yoy3 <= L(.7))).astype(int) >= 2)
sig['V'] = f((P.s_last_avg < .1) & (P.cut3 <= 0))
nU = (f((P.n_big12 >= 3) & (P.last3_vs_rate >= 1.5)).astype(int) + f((P.s_zeros12 >= 1) & (P.last3_vs_rate >= 1.2) & (P.os_br3 < .05)).astype(int)
      + f((P.st3 <= .69) & (P.s_ms_big <= 3)).astype(int) + f((P.cut3 >= .6) & (P.br_e_yoy3 <= L(.8))).astype(int))
sig['U'] = nU >= 2
nG = (f((P.s_zeros12 >= 2) & (P.s_ms_big <= 2) & (P.cut3 >= .5)).astype(int) + f((P.cut2 if 'cut2' in P else P.cut3 >= 2) & (P.e_last3_vs_rate <= .65)).astype(int)
      + f((P.br_s_yoy3 <= L(.75)) & (P.os_br_yoy3 >= L(2.5)) & (P.zeros3 == 0)).astype(int) + f((P.mes_obj == 9) & (P.s_zeros12 == 0)).astype(int))
sig['G'] = nG >= 2
# factores de la acción: medianas del periodo ANTIGUO (antes de 2025.M03), para no usar lo que se mide
old = P.F < 2025*12+2
r3 = P.y3 / P.base_rob
fac = {'C': float(np.nanmedian(r3[old & sig.C])), 'C1': float(np.nanmedian(r3[old & sig.C1])),
       'M': float(np.nanmedian((P.y6/(6*P.mu12))[old & sig.M])), 'U': float(np.nanmedian(r3[old & sig.U])),
       'G': float(np.nanmedian((P.a1/P.mu12)[sig.G]))}
print('factores (mediana periodo antiguo):', {k: round(v, 2) for k, v in fac.items()}, ' casos antiguos', {k: int((old & sig[k]).sum()) for k in ['C','C1','M','U','G']})
P = P.join(sig)
# forecast real por foto x código x mes (armonizado)
fv = pd.read_pickle(S+'/fva_arm.pkl')
fv = fv[(~fv.os) & fv.h.between(1, 3)].copy()
fv = fv.merge(P[['F','ean','C','C1','M','V','U','G','base_rob','mu12']].rename(columns={'F':'foto'}), on=['foto','ean'], how='left')
for c in ['C','C1','M','V','U','G']: fv[c] = fv[c].fillna(False).astype(bool)
fv['cons'] = fv.cons_arm.clip(lower=0)
esp_m = fv.base_rob / 3
acciones = {
 'V': ('Mes vacío: forecast 0 el mes siguiente', lambda d: np.where(d.V & (d.h == 1), 0.0, d.cons)),
 'M': ('Muerte: forecast ≤ {k}× su ritmo', lambda d: np.where(d.M, np.minimum(d.cons, fac['M'] * d.mu12), d.cons)),
 'C': ('Caída (2+ señales): forecast ≤ {k}× lo esperable', lambda d: np.where(d.C, np.minimum(d.cons, fac['C'] * d.base_rob/3), d.cons)),
 'C1': ('Caída (1 señal): forecast ≤ {k}× lo esperable', lambda d: np.where(d.C1, np.minimum(d.cons, fac['C1'] * d.base_rob/3), d.cons)),
 'U': ('Subida (2+ señales): forecast ≥ {k}× lo esperable', lambda d: np.where(d.U, np.maximum(d.cons, fac['U'] * d.base_rob/3), d.cons)),
 'G': ('Pedido grande (2+ señales): mes siguiente ≥ {k}× su media', lambda d: np.where(d.G & (d.h == 1), np.maximum(d.cons, fac['G'] * d.mu12), d.cons)),
}
def kpi(F_, d):
    A = d.A.sum(); return (np.abs(F_ - d.A).sum() / A, (A - F_.sum()) / A)
d = fv[fv.foto <= 2026*12+5]       # fotos con los 3 meses cerrados
w0, s0 = kpi(d.cons, d)
print(f'\nForecast real (Consensus), regulares, fotos {m(d.foto.min())}-{m(d.foto.max())}: WAPE90 {w0:.1%}  SPP3 {s0:+.1%}  ({d.ean.nunique()} códigos, {len(d)} código-meses)')
res = []
for k_, (nm, fn) in acciones.items():
    F_ = fn(d); w, s = kpi(F_, d); t = d[k_]
    # sobre los códigos tocados
    dt = d[t]
    wt0, st0 = kpi(dt.cons, dt) if len(dt) else (np.nan, np.nan); wt1, st1 = kpi(F_[t.to_numpy()], dt) if len(dt) else (np.nan, np.nan)
    res.append(dict(accion=k_, nombre=nm.format(k=f'{fac.get(k_, 0):.2f}'.replace('.', ',')), casos=int(d[t][['foto','ean']].drop_duplicates().shape[0]), codigos=int(dt.ean.nunique()),
                    wape=w, spp=s, dw=w - w0, wape_t0=wt0, wape_t1=wt1, spp_t0=st0, spp_t1=st1, unidades_cambiadas=float(np.abs(F_ - d.cons).sum())))
    print(f'  {nm.format(k=round(fac.get(k_,0),2)):55s} casos {res[-1]["casos"]:4d} ({res[-1]["codigos"]} cód.)  WAPE90 {w:.1%} ({w-w0:+.1%})  SPP3 {s:+.1%}  | en los tocados: WAPE {wt0:.0%}→{wt1:.0%}  SPP {st0:+.0%}→{st1:+.0%}')
# todas juntas (prioridad: vacío > muerte > caída > subida > pedido)
F_ = d.cons.to_numpy().copy()
for k_ in ['G', 'U', 'C1', 'C', 'M', 'V']:
    F_ = np.where(d[k_].to_numpy(), acciones[k_][1](d.assign(cons=F_)), F_)
wa, sa = kpi(pd.Series(F_, index=d.index), d)
print(f'\n  TODAS LAS ACCIONES: WAPE90 {w0:.1%} -> {wa:.1%} ({wa-w0:+.1%})   SPP3 {s0:+.1%} -> {sa:+.1%}')
for nm, g in [('sin la de 1 señal de caída', ['G','U','C','M','V']), ('solo reducir (vacío, muerte, caída 2+)', ['C','M','V'])]:
    F2 = d.cons.to_numpy().copy()
    for k_ in g: F2 = np.where(d[k_].to_numpy(), acciones[k_][1](d.assign(cons=F2)), F2)
    w2, s2 = kpi(pd.Series(F2, index=d.index), d); print(f'  {nm:40s}: WAPE90 {w2:.1%} ({w2-w0:+.1%})  SPP3 {s2:+.1%}')
# por foto (estabilidad)
print('\n  por foto (todas las acciones):')
pf = []
for ft, g in d.groupby('foto'):
    F3 = g.cons.to_numpy().copy()
    for k_ in ['G', 'U', 'C1', 'C', 'M', 'V']: F3 = np.where(g[k_].to_numpy(), acciones[k_][1](g.assign(cons=F3)), F3)
    a, b = kpi(g.cons, g); c, e = kpi(pd.Series(F3, index=g.index), g)
    pf.append(dict(foto=m(ft), w0=a, w1=c, s0=b, s1=e)); print(f'    {m(ft)}: WAPE {a:.0%} -> {c:.0%}   SPP {b:+.0%} -> {e:+.0%}')
json.dump(dict(base=dict(wape=w0, spp=s0, codigos=int(d.ean.nunique()), filas=len(d)), todas=dict(wape=wa, spp=sa), acciones=res, fac=fac, porfoto=pf), open(S+'/sim_kpi.json', 'w'))
