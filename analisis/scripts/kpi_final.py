import numpy as np, pandas as pd, sys
exec(open('/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad/kpi_acciones.py').read().split("ACC = {")[0])
print('1) Recorte del DA positivo con un único factor: WAPE90 y SPP3 en cada periodo')
for rho in [1.0, 0.8, 0.7, 0.6, 0.55, 0.5, 0.4]:
    r = []
    for msk in [A1, A2]:
        w, s = kpi(da_corte(d[msk], rho), d[msk]); r.append(f'WAPE {w:.1%} SPP {s:+.1%}')
    print(f'   llega el {rho:.0%} del DA ->  2025 (armonizadas): {r[0]}   |   2026 (limpias): {r[1]}')
print('\n2) Lanzamientos: SPP del forecast real por edad del código en el mes objetivo')
for nm, msk in [('2025 (armonizadas)', A1), ('2026 (limpias)', A2)]:
    q = d[msk].copy(); q['eb'] = pd.cut(q.edad_t, [-1, 2, 5, 11, 1000], labels=['meses 1-3','meses 4-6','meses 7-12','> 12 meses'])
    E = (q.cons - q.A).abs().sum()
    print('   ' + nm + ': ' + ' | '.join(f'{b}: WAPE {kpi(g.cons, g)[0]:.0%} SPP {kpi(g.cons, g)[1]:+.0%} ({(g.cons-g.A).abs().sum()/E:.0%} del error)' for b, g in q.groupby('eb', observed=True)))
print('\n3) Peso de los 20 códigos con más error en cada periodo')
for nm, msk in [('2025', A1), ('2026', A2)]:
    q = d[msk].copy(); q['e'] = (q.cons - q.A).abs()
    pc = q.groupby('ean').e.sum().sort_values(ascending=False)
    print(f'   {nm}: top 20 = {pc.head(20).sum()/pc.sum():.0%} del error, de {len(pc)} códigos; ¿mismos códigos en ambos periodos?')
t25 = set(d[A1].assign(e=(d.cons-d.A).abs()).groupby('ean').e.sum().nlargest(20).index); t26 = set(d[A2].assign(e=(d.cons-d.A).abs()).groupby('ean').e.sum().nlargest(20).index)
print(f'   coinciden {len(t25 & t26)} de 20')
