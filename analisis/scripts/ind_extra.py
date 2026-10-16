"""Indicadores extra del ciclo de pedidos y objetivos de demanda real (sin Consensus)."""
exec(open('/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad/ind.py').read().split('rows = []')[0])
Z = pd.read_pickle(S+'/ind3.pkl')
rows = []
for F in sorted(Z.F.unique()):
    d = {'F': np.full(NE, F), 'ean': np.array(EANS)}
    X12 = SI[:, k(F-12):k(F)]; mu = X12.mean(1)
    thr = np.maximum(2*np.median(X12, 1), 1.5*mu)
    big = X12 >= thr[:, None]
    d['n_big12'] = big.sum(1)
    d['ly_next1'] = SI[:, k(F-11)] / np.maximum(mu, 1e-9)                    # mismo mes objetivo, año pasado / media
    d['ly_next1_big'] = (SI[:, k(F-11)] >= thr).astype(float)
    d['ly_next3'] = w(SI, F-11, F-9) / np.maximum(3*mu, 1e-9)
    d['ly2_next1_big'] = (SI[:, k(F-23)] >= thr).astype(float) if k(F-23) >= 0 else np.full(NE, np.nan)
    # agotamiento desde el último gran pedido: EPOS acumulado (en unidades de sell-in) / tamaño de ese pedido
    last = np.array([np.where(b)[0].max() if b.any() else -1 for b in big])
    E12 = EP[:, k(F-12):k(F)]; kap = np.nansum(E12, 1) / np.maximum(X12.sum(1), 1)
    dep = np.full(NE, np.nan)
    for i in np.where(last >= 0)[0]:
        if kap[i] > 0 and not np.isnan(E12[i, last[i]:]).all():
            dep[i] = (np.nansum(E12[i, last[i]+1:]) / kap[i]) / max(X12[i, last[i]], 1)
    d['agot'] = dep
    d['last3_vs_rate'] = w(SI, F-3, F-1) / np.maximum(3*mu, 1e-9)
    d['zeros3'] = (SI[:, k(F-3):k(F)] <= 0).sum(1)
    d['e_last3_vs_rate'] = wn(EP, F-3, F-1) / np.maximum(3*np.nanmean(E12, 1), 1e-9)
    # objetivos
    if F + 1 <= T1: d['a1'] = SI[:, k(F+1)]
    if F + 2 <= T1: d['a2'] = SI[:, k(F+1)] + SI[:, k(F+2)]
    if F + 6 <= T1: d['y6'] = w(SI, F+1, F+6)
    d['mu12'] = mu; d['thr_big'] = thr
    rows.append(pd.DataFrame(d))
E = pd.concat(rows)
Z = Z.merge(E, on=['F','ean'], how='left')
Z.to_pickle(S+'/ind4.pkl'); print(Z.shape)
