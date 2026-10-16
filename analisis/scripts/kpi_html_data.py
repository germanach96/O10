import numpy as np, pandas as pd, sys, json
exec(open('/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad/kpi_acciones.py').read().split("ACC = {")[0])
L = np.log
src = open(S+'/sim_kpi.py').read()
exec(src[src.index('Z = pd.read_pickle'):src.index('# forecast real por foto')])   # señales y factores (periodo antiguo)
fac['U'] = float(np.nanmedian((P.y3/P.base_rob)[P.U])) if 'U' in P else 1.2
d2 = d.merge(P[['F','ean','C','C1','M','V','U','G','base_rob']].rename(columns={'F':'foto'}), on=['foto','ean'], how='left')
for c in ['C','C1','M','V','U','G']: d2[c] = d2[c].fillna(False).astype(bool)
g = d2[d2.foto >= 2026*12+1].copy()
w0, s0 = kpi(g.cons, g)
reglas = {
 'M': ('Muerte (2+ señales)', 'Bajar el forecast a 0,23× su ritmo', lambda x: np.where(x.M, np.minimum(x.cons, fac['M']*x.mu12), x.cons)),
 'C': ('Caída (2+ señales)', 'Bajar el forecast a 0,33× lo esperable', lambda x: np.where(x.C, np.minimum(x.cons, fac['C']*x.base_rob/3), x.cons)),
 'V': ('Mes vacío (último mes a cero, sin cortes)', 'Forecast 0 el mes siguiente', lambda x: np.where(x.V & (x.h == 1), 0.0, x.cons)),
 'U': ('Subida fuerte (2+ señales)', f'Subir el forecast a {fac["U"]:.2f}× lo esperable', lambda x: np.where(x.U, np.maximum(x.cons, fac['U']*x.base_rob/3), x.cons)),
 'G': ('Pedido grande (2+ señales)', 'Subir el mes siguiente a 1,55× su media', lambda x: np.where(x.G & (x.h == 1), np.maximum(x.cons, fac['G']*x.mu12), x.cons)),
}
out = []
for k_, (nm, acc, fn) in reglas.items():
    F_ = fn(g); w, s = kpi(F_, g); t = g[k_]
    tt = g[t]; vt = tt.A.sum() / g.A.sum()
    wt0, st0 = kpi(tt.cons, tt) if len(tt) else (np.nan, np.nan); wt1, st1 = kpi(F_[t.to_numpy()], tt) if len(tt) else (np.nan, np.nan)
    out.append(dict(k=k_, nombre=nm, accion=acc, codigos=int(tt.ean.nunique()), vol=float(vt), w0=w0, w1=w, s0=s0, s1=s, wt0=wt0, wt1=wt1, st0=st0, st1=st1))
    print(f'{nm:42s} códigos {out[-1]["codigos"]:3d}  % volumen {vt:5.1%}  WAPE casa {w0:.1%}->{w:.1%}  SPP {s0:+.1%}->{s:+.1%}  | tocados WAPE {wt0:.0%}->{wt1:.0%} SPP {st0:+.0%}->{st1:+.0%}')
# DA 70 %
da = []
for rho in [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4]:
    r = {}
    for nm, msk in [('2025', A1), ('2026', A2)]:
        w, s = kpi(da_corte(d[msk], rho), d[msk]); r[nm] = (w, s)
    da.append(dict(rho=rho, w25=r['2025'][0], s25=r['2025'][1], w26=r['2026'][0], s26=r['2026'][1]))
# descomposición del error (2026 limpias)
q = d[A2].copy(); q['e'] = (q.cons - q.A).abs(); E = q.e.sum(); VA = q.A.sum()
q['tam'] = pd.cut(q.s12, [0, 4000, 20000, 60000, 1e12], labels=['Menos de 4.000 uds/año', '4.000–20.000', '20.000–60.000', 'Más de 60.000'])
tam = [dict(t=str(t), cod=int(x.ean.nunique()), vol=float(x.A.sum()/VA), err=float(x.e.sum()/E)) for t, x in q.groupby('tam', observed=True)]
nuevos = q[q.s12.isna() | (q.edad_t < 12)]
tam.append(dict(t='Lanzamientos (menos de 12 meses)', cod=int(nuevos.ean.nunique()), vol=float(nuevos.A.sum()/VA), err=float(nuevos.e.sum()/E)))
pc = q.groupby('ean').e.sum().sort_values(ascending=False)
pico = q.A > 2*q.mu12; dadom = q.tda_fut_arm > .5*q.cons.clip(lower=1)
dec = dict(top20=float(pc.head(20).sum()/E), ncod=int(len(pc)), pico_filas=float(pico.mean()), pico_err=float(q[pico].e.sum()/E),
           da_filas=float(dadom.mean()), da_err=float(q[dadom].e.sum()/E), da_spp=float((q[dadom].A.sum()-q[dadom].cons.sum())/q[dadom].A.sum()),
           sobre=float((q.cons-q.A).clip(lower=0).sum()/E))
# ejemplo DA: código grande con mes de DA dominante en 2026
ex = q[dadom & (q.cons > 5000)].copy(); ex['mej'] = (ex.cons-ex.A).abs() - (da_corte(ex, .7)-ex.A).abs()
ex = ex.sort_values('mej', ascending=False).head(3)
ej = []
from base import ATR
DESC = ATR['Planning Item Description'].to_dict()
for _, r in ex.iterrows():
    nuevo = max(r.cons - 0.3 * max(r.tda_fut_arm, 0), 0)
    ej.append(dict(desc=str(DESC.get(r.ean, r.ean)), foto=m(int(r.foto)), mes=m(int(r.t)), cons=float(r.cons), da=float(r.tda_fut_arm), A=float(r.A), nuevo=float(nuevo)))
print(ej)
json.dump(dict(reglas=out, da=da, tam=tam, dec=dec, ej=ej, base=dict(w=w0, s=s0)), open(S+'/kpi_html.json', 'w'), ensure_ascii=False, default=float)
print(json.dumps(dec, indent=1)); print(tam)
