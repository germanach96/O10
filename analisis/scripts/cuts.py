from base import *
import statsmodels.api as sm
print('Cortes totales', CUT.sum().round(), ' meses-código con corte', (CUT>0).sum(), ' en regular', (CUT[~OS]>0).sum())
rows = []
for i in np.where(~OS)[0]:
    for t in range(12, NM-3):
        prev = ACT[i, t-12:t]; 
        if prev.sum() < 120: continue
        mu = prev.mean()
        rows.append(dict(ean=EANS[i], t=MESES[t], cut=CUT[i,t], a=ACT[i,t], a1=ACT[i,t+1], a2=ACT[i,t+2], a3=ACT[i,t+3], ly1=ACT[i,t-11], ly2=ACT[i,t-10], ly3=ACT[i,t-9], mu=mu))
D = pd.DataFrame(rows)
# exceso de actuals en t+1..t+3 frente a la misma ventana del año anterior, escalado
D['exc'] = (D.a1 + D.a2 + D.a3) - (D.ly1 + D.ly2 + D.ly3)
D['cut_rel'] = D.cut / (3*D.mu)
X = sm.add_constant(pd.DataFrame({'cut': D.cut, 'a': D.a, 'ly': D.ly1+D.ly2+D.ly3}))
r = sm.WLS(D.a1 + D.a2 + D.a3, X, weights=1/(D.mu+10)).fit(cov_type='cluster', cov_kwds={'groups': D.ean.astype('category').cat.codes})
print(f'Actuals t+1..t+3 = {r.params.const:.0f} + {r.params.cut:.2f}·Corte(t) + {r.params.a:.2f}·Actual(t) + {r.params.ly:.2f}·LY   (IC corte {r.conf_int().loc["cut",0]:.2f}..{r.conf_int().loc["cut",1]:.2f}, p={r.pvalues.cut:.3f})')
c = D[D.cut > 0.1*D.mu]
print(f'\nMeses con corte relevante (>10% de la media mensual): n={len(c)}, códigos {c.ean.nunique()}')
for lag, col in [(1,'a1'),(2,'a2'),(3,'a3')]:
    print(f'   t+{lag}: actual / media 12M = {c[col].sum()/c.mu.sum():.2f}   (sin corte: {D[D.cut==0][col].sum()/D[D.cut==0].mu.sum():.2f})')
print(f'   recuperado en t+1..t+3 sobre LY por unidad cortada: {(c.exc.sum())/c.cut.sum():+.2f}  (sin corte, exceso medio por unidad de media: {D[D.cut==0].exc.sum()/D[D.cut==0].mu.sum():+.2f})')
