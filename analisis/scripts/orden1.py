from base import *
import statsmodels.api as sm
from statsmodels.stats.proportion import proportion_confint as ci
# lumpiness
mask = (~OS) & (ACT[:, k(2024*12+9):].sum(1) >= 600)   # regulares con >=600 uds en 24M
A = ACT[mask][:, k(2024*12+9):]
print('regulares con volumen', mask.sum())
z = (A==0).mean(1); cv = A.std(1)/A.mean(1)
print('fracción de meses sin pedido: mediana', np.median(z).round(2), ' CV mensual mediana', np.median(cv).round(2))
# big order: mes con sell-in >= 2x mediana de los 12 meses previos (incluyendo ceros) y >= 1.5x media 12M
rows = []
idx = np.where(mask)[0]
for i in idx:
    a = ACT[i]; e = EPOS[i]
    for t in range(k(2024*12+6+12), NM):   # EPOS 12M disponible
        prev = a[t-12:t]; ep = e[t-12:t]
        if np.isnan(ep).sum() > 2 or np.nansum(ep) <= 0 or prev.sum() <= 0: continue
        big_thr = max(2*np.median(prev), 1.5*prev.mean())
        bigs_prev = np.where(prev >= big_thr)[0]
        kappa = np.nansum(ep)/prev.sum()          # cobertura EPOS/sell-in del código (12M)
        # meses desde el último pedido grande en la ventana
        if len(bigs_prev):
            j = bigs_prev[-1]; ms = 12 - j
            shipped = prev[j:].sum(); sold = np.nansum(ep[j:]) / kappa
            dep = sold / shipped
        else:
            ms = 13; dep = np.nan
        # sell-through reciente: EPOS 3M / sellin 3M normalizado
        st3 = (np.nansum(ep[-3:])/kappa) / max(prev[-3:].sum(), 1)
        rows.append((EANS[i], MESES[t], a[t] >= big_thr, a[t]/prev.mean(), ms, dep, st3, kappa))
O = pd.DataFrame(rows, columns=['ean','t','big','ratio','ms','dep','st3','kappa'])
print('obs', len(O), 'tasa base de pedido grande', O.big.mean().round(3))
def tab(by, nm):
    print('\n'+nm)
    for b, g in O.groupby(by, observed=True):
        lo, hi = ci(g.big.sum(), len(g), method='wilson')
        print(f'  {str(b):28s} n={len(g):4d}  P(pedido grande este mes)={g.big.mean():.0%} [{lo:.0%}-{hi:.0%}]  sell-in medio {g.ratio.mean():.2f}x')
O['stb'] = pd.cut(O.st3, [0,.6,.9,1.2,1.8,100], labels=['sell-through 3M < 0.6','0.6-0.9','0.9-1.2','1.2-1.8','> 1.8 (vende más de lo que entra)'])
tab('stb', 'Sell-through de los últimos 3M (EPOS/cobertura ÷ sell-in) -> pedido grande el mes siguiente')
O['db'] = pd.cut(O.dep, [0,.5,.8,1.0,1.3,100], labels=['vendido <50% del último gran pedido','50-80%','80-100%','100-130%','>130%'])
tab('db', 'Agotamiento desde el último gran pedido -> pedido grande')
O['msb'] = pd.cut(O.ms, [0,2,4,6,9,12,13], labels=['1-2 meses','3-4','5-6','7-9','10-12','sin gran pedido en 12M'])
tab('msb', 'Meses desde el último gran pedido -> pedido grande')
O.to_pickle(S+'/ordenes.pkl')
