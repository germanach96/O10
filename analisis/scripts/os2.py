from base import *
from scipy import stats
import statsmodels.api as sm
# Por PL y temporada (ventana de 6 meses: jul-dic = temporada de regalo; ene-jun), cambio YoY de OS vs cambio YoY de regulares
rows = []
for key in np.unique(PL):
    msk = PL == key
    for y in [2023, 2024, 2025]:
        for h, (a, b) in {'Jul-Dic': (6, 11), 'Ene-Jun': (12, 17)}.items():
            t0 = y*12 + a; t1 = y*12 + b
            if t1 > T1 or t0 - 12 < T0: continue
            def s(M, mm, t0, t1): return np.nansum(M[mm][:, k(t0):k(t1)+1])
            r, rly = s(ACT, msk & ~OS, t0, t1), s(ACT, msk & ~OS, t0-12, t1-12)
            o, oly = s(ACT, msk & OS, t0, t1), s(ACT, msk & OS, t0-12, t1-12)
            er, erly = (s(EPOS, msk & ~OS, t0, t1), s(EPOS, msk & ~OS, t0-12, t1-12)) if t0-12 >= 2024*12+6 else (np.nan, np.nan)
            rows.append(dict(pl=key, temp=f'{h} {y}', r=r, rly=rly, o=o, oly=oly, er=er, erly=erly))
D = pd.DataFrame(rows)
D = D[(D.rly >= 2000) & (D.r > 0)]
D['dreg'] = np.log(D.r / D.rly)
D['dos_rel'] = (D.o - D.oly) / D.rly           # cambio de OS en unidades, relativo al volumen regular del año anterior
D['dep'] = np.log(D.er / D.erly)
print('obs PL x temporada:', len(D))
for y, nm in [('dreg', 'sell-in regular YoY'), ('dep', 'EPOS regular YoY')]:
    d = D.dropna(subset=[y]); d = d[np.isfinite(d[y])]
    d = d[d.dos_rel.abs() < 5]
    X = sm.add_constant(d[['dos_rel']]); r = sm.WLS(d[y], X, weights=np.sqrt(d.rly)).fit(cov_type='HC1')
    rho, p = stats.spearmanr(d.dos_rel, d[y])
    print(f'\n{nm} ~ cambio de OS (unidades OS extra / volumen regular LY): n={len(d)}  pendiente {r.params.dos_rel:+.3f} (p={r.pvalues.dos_rel:.3f})  Spearman {rho:+.2f} (p={p:.3f})')
    d['b'] = pd.cut(d.dos_rel, [-10, -.1, .1, .5, 10], labels=['OS baja >10% del regular','OS estable ±10%','OS sube 10-50%','OS sube >50%'])
    for b, g in d.groupby('b', observed=True):
        print(f'   {b:28s} n={len(g):3d}  {nm} agregado {g.r.sum()/g.rly.sum()-1 if y=="dreg" else g.er.sum()/g.erly.sum()-1:+.0%}  P(regular baja)={(g[y]<0).mean():.0%}')
