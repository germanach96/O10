from base import *
from statsmodels.stats.proportion import proportion_confint as ci
O = pd.read_pickle(S+'/ordenes.pkl'); O['mes'] = O.t % 12 + 1
print('P(pedido grande) por mes natural:')
print('  ' + '  '.join(f'M{mm:02d}:{g.big.mean():.0%}' for mm, g in O.groupby('mes')))
# ¿destocking o ciclo de vida? separar por tendencia del EPOS
E = pd.read_pickle(S+'/feats.pkl')
# Tamaño de la carga de Q4 (sep-nov) vs EPOS de verano (jun-ago) YoY, por código regular
r = []
for y in [2025]:
    q4 = ACT[:, k(y*12+8):k(y*12+10)+1].sum(1); q4ly = ACT[:, k((y-1)*12+8):k((y-1)*12+10)+1].sum(1)
    ep = np.nansum(EPOS[:, k(y*12+5):k(y*12+7)+1],1); eply = np.nansum(EPOS[:, k((y-1)*12+5):k((y-1)*12+7)+1],1)  # jun-ago 2024 existe solo desde jul
    ep = np.nansum(EPOS[:, k(y*12+6):k(y*12+7)+1],1); eply = np.nansum(EPOS[:, k((y-1)*12+6):k((y-1)*12+7)+1],1)  # jul-ago
    si = ACT[:, k(y*12+5):k(y*12+7)+1].sum(1); sily = ACT[:, k((y-1)*12+5):k((y-1)*12+7)+1].sum(1)
    ok = (~OS) & (q4ly >= 100) & (eply >= 30) & (sily>=30)
    d = pd.DataFrame({'q4g': q4[ok]/q4ly[ok]-1, 'epg': ep[ok]/eply[ok]-1, 'sig': si[ok]/sily[ok]-1, 'w': q4ly[ok]})
    from scipy.stats import spearmanr
    print(f'\nCarga sep-nov {y} vs año anterior, por código regular (n={len(d)}):')
    print(f'  Spearman con EPOS jul-ago YoY: {spearmanr(d.epg, d.q4g)[0]:+.2f} (p={spearmanr(d.epg, d.q4g)[1]:.3f});  con sell-in jun-ago YoY: {spearmanr(d.sig, d.q4g)[0]:+.2f} (p={spearmanr(d.sig, d.q4g)[1]:.3f})')
    d['b'] = pd.cut(d.epg, [-1,-.3,-.1,.1,100], labels=['EPOS verano < -30%','-30..-10%','±10%','> +10%'])
    for b, g in d.groupby('b', observed=True):
        print(f'  {b:20s} n={len(g):3d}  carga Q4 agregada {(g.q4g+1).mul(g.w).sum()/g.w.sum()-1:+.0%}  P(carga baja)={(g.q4g<0).mean():.0%}')
# destocking: sell-through alto separado por tendencia de EPOS
O2 = O.merge(E[['ean','F','ep3','ep3_ly']].rename(columns={'F':'t'}), on=['ean','t'], how='left')
O2['epg'] = (O2.ep3+1)/(O2.ep3_ly+1)-1
O2 = O2[O2.ep3_ly >= 30]
O2['eb'] = np.where(O2.epg < -.1, 'EPOS YoY baja', 'EPOS YoY estable/sube')
O2['sb'] = np.where(O2.st3 > 1.2, 'sell-through >1.2', 'sell-through <=1.2')
print('\nSell-through alto separado por tendencia del EPOS (desde 2025.M10):')
for (a, b), g in O2.groupby(['eb','sb']):
    lo, hi = ci(g.big.sum(), len(g), method='wilson')
    print(f'  {a:22s} {b:20s} n={len(g):4d}  P(pedido grande)={g.big.mean():.0%} [{lo:.0%}-{hi:.0%}]  sell-in {g.ratio.mean():.2f}x media 12M')
