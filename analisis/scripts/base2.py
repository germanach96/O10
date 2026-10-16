"""Base robusta: nivel 12M x índice estacional de la brand (año pasado), sin trend. Y el Consensus armonizado por foto."""
exec(open('/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad/ind.py').read().split('rows = []')[0])
Z = pd.read_pickle(S+'/ind2.pkl')
BR_all = gsum(SI, BRAND)        # brand total (incluye al código, regulares+OS)
BR_reg = gsum(SI, BRAND, REG)
idx = []
for F in sorted(Z.F.unique()):
    if F + 3 > T1 or k(F-12) < 0: idx.append(pd.DataFrame({'F': F, 'ean': EANS, 'I_br': np.nan})); continue
    ly_win = w(BR_reg, F-11, F-9) / 3; ly12 = w(BR_reg, F-12, F-1) / 12          # índice del año pasado: ventana objetivo LY / media 12M
    ly12b = w(BR_reg, F-24, F-13) / 12 if k(F-24) >= 0 else np.full(NE, np.nan)
    I = ly_win / np.maximum(ly12, 1)
    idx.append(pd.DataFrame({'F': F, 'ean': EANS, 'I_br': I}))
I = pd.concat(idx)
Z = Z.drop(columns=[c for c in ['I_br'] if c in Z]).merge(I, on=['F','ean'], how='left')
Z['base_rob'] = Z.s12 / 12 * 3 * Z.I_br.clip(0.3, 3)
L = lambda a, b: np.log((a+1)/(b+1))
Z['sorp_rob'] = L(Z.y3, Z.base_rob)
P = Z[(Z.os == 0) & (Z.s12 >= 150) & (Z.edad >= 13) & Z.sorp_rob.notna() & (Z.base_rob >= 30)]
for nm, b in [('extrapolación (LY x trend 6M)', 'base_ext'), ('robusta (nivel 12M x estacionalidad brand)', 'base_rob')]:
    q = P[P[b].notna()]
    print(f'{nm:45s} WAPE3 {(q.y3-q[b]).abs().sum()/q.y3.sum():.0%}  bias {(q.y3.sum()-q[b].sum())/q.y3.sum():+.0%}  n={len(q)}')
Z.to_pickle(S+'/ind3.pkl')
