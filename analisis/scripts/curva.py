from base import *
rows = []
for i in np.where((PRIMER >= 2023*12+2) & (PRIMER + 11 <= T1))[0]:
    a = ACT[i, k(PRIMER[i]):k(PRIMER[i])+12]; e = EPOS[i, k(PRIMER[i]):k(PRIMER[i])+12]
    if a.sum() < 2000: continue
    rows.append(dict(ean=EANS[i], os=OS[i], L=PRIMER[i], tot=a.sum(), **{f'a{j+1}': a[j] for j in range(12)}, **{f'e{j+1}': e[j] for j in range(12)}))
C = pd.DataFrame(rows)
for tipo, g in C.groupby('os'):
    sh = g[[f'a{j}' for j in range(1,13)]].div(g.tot, axis=0)
    print(f'\n{"ONE SHOT" if tipo else "REGULAR"} nuevos (n={len(g)}): % del volumen de los primeros 12 meses por mes desde el lanzamiento')
    print('   mediana: ' + ' '.join(f'M{j}:{sh[f"a{j}"].median():.0%}' for j in range(1,13)))
    print('   agregado:' + ' '.join(f'M{j}:{g[f"a{j}"].sum()/g.tot.sum():.0%}' for j in range(1,13)))
    print(f'   meses 1-3 = {g[["a1","a2","a3"]].sum().sum()/g.tot.sum():.0%} del primer año;  mes 1 / media meses 4-12 = {(g.a1.sum())/(g[[f"a{j}" for j in range(4,13)]].sum().sum()/9):.1f}x')
    ge = g[g.L >= 2024*12+6]
    if len(ge):
        si = ge[[f'a{j}' for j in range(1,13)]].sum().to_numpy(); ep = np.nansum(ge[[f'e{j}' for j in range(1,13)]].to_numpy(), 0)
        cum = np.cumsum(si) / np.maximum(np.cumsum(ep), 1)
        print(f'   lanzamientos con EPOS (n={len(ge)}): sell-in acumulado / EPOS acumulado: ' + ' '.join(f'M{j+1}:{cum[j]:.1f}' for j in range(12)))
# ¿qué fracción del volumen del primer año del código nuevo es "nuevo" para la brand? (brand YoY en los 6M tras el lanzamiento grande)
