import numpy as np, pandas as pd, sys
exec(open('/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad/kpi_acciones.py').read().split("ACC = {")[0])
def lanz(g, a): return np.where(g.edad_t.between(6, 11), g.cons * a, g.cons)
grid = np.linspace(.3, 1.2, 19)
for cal, test, lab in [(A1, A2, '2025→2026'), (A2, A1, '2026→2025')]:
    best = min(grid, key=lambda a: obj(lanz(d[cal], a), d[cal]))
    wb, sb = kpi(d.cons[test], d[test]); w, s = kpi(lanz(d[test], best), d[test])
    t = d[test & d.edad_t.between(6, 11)]
    print(f'{lab}: factor {best:.2f}  WAPE90 casa {wb:.1%} -> {w:.1%} ({w-wb:+.1%})  SPP {sb:+.1%} -> {s:+.1%}  · códigos afectados {t.ean.nunique()} ({t.A.sum()/d[test].A.sum():.0%} del volumen)')
for a in [1.0, .8, .7, .6]:
    print(f'  factor {a}: ' + '  '.join(f'{lab} WAPE {kpi(lanz(d[msk], a), d[msk])[0]:.1%} SPP {kpi(lanz(d[msk], a), d[msk])[1]:+.1%}' for lab, msk in [('2025', A1), ('2026', A2)]))
# combinado DA 70% + lanzamiento
for a in [1.0, .8, .7]:
    r = []
    for lab, msk in [('2025', A1), ('2026', A2)]:
        g = d[msk].copy(); g['cons'] = da_corte(g, .7); F_ = lanz(g, a); r.append(f'{lab} WAPE {kpi(F_, g)[0]:.1%} SPP {kpi(F_, g)[1]:+.1%}')
    print(f'  DA 70% + lanzamiento x{a}: ' + '  '.join(r))
