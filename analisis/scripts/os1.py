from base import *
import statsmodels.formula.api as smf
def panel(keys, desde=2022*12+8, usar_epos=False):
    rows = []
    M = EPOS if usar_epos else ACT
    for key in np.unique(keys):
        msk = keys == key
        reg = np.nansum(np.where(~OS[msk][:, None], M[msk], 0), 0)
        osv = np.nansum(np.where(OS[msk][:, None], ACT[msk], 0), 0)   # OS siempre en sell-in (lo que se envía)
        oss = np.nansum(np.where(OS[msk][:, None], EPOS[msk], 0), 0)
        for t in range(NM):
            if MESES[t] < desde: continue
            if usar_epos and np.isnan(M[msk][:, t]).all(): continue
            rows.append(dict(g=key, t=MESES[t], cal=MESES[t] % 12, reg=reg[t], os_=osv[t], os_l1=osv[t-1], os_l2=osv[t-2], os_f1=osv[t+1] if t+1 < NM else np.nan, oss=oss[t]))
    D = pd.DataFrame(rows)
    # quedarnos con grupos que tienen regulares y algún OS
    tot = D.groupby('g').agg(r=('reg','sum'), o=('os_','sum'))
    ok = tot[(tot.r > 20000) & (tot.o > 5000)].index
    D = D[D.g.isin(ok)].copy()
    for c in ['reg','os_','os_l1','os_l2','os_f1','oss']: D['l'+c] = np.log1p(D[c])
    D['gcal'] = D.g.astype(str) + '_' + D.cal.astype(str)
    return D
def fit(D, f, nm):
    r = smf.ols(f, D).fit(cov_type='cluster', cov_kwds={'groups': D.g.astype('category').cat.codes})
    keys = [k_ for k_ in r.params.index if k_.startswith('los')]
    print(f'{nm:58s} n={len(D):4d} grupos={D.g.nunique():2d}  ' + '  '.join(f'{k_}={r.params[k_]:+.3f}(p={r.pvalues[k_]:.3f})' for k_ in keys))
for nivel, keys in [('Product Line', PL), ('Brand', BRAND)]:
    D = panel(keys)
    fit(D, 'lreg ~ los_ + C(gcal) + C(t)', f'{nivel}: sell-in regular ~ sell-in OS mismo mes')
    fit(D, 'lreg ~ los_ + los_l1 + los_l2 + C(gcal) + C(t)', f'{nivel}: + OS de 1 y 2 meses antes')
    fit(D.dropna(subset=['los_f1']), 'lreg ~ los_ + los_l1 + los_l2 + los_f1 + C(gcal) + C(t)', f'{nivel}: + OS del mes siguiente (placebo)')
    De = panel(keys, 2024*12+6, True)
    if len(De):
        fit(De, 'lreg ~ loss + C(g) + C(t)', f'{nivel}: EPOS regular ~ EPOS OS mismo mes (consumidor)')
        fit(De, 'lreg ~ los_ + los_l1 + C(g) + C(t)', f'{nivel}: EPOS regular ~ sell-in OS (mes y mes-1)')
