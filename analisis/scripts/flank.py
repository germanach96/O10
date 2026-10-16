from base import *
pls = pd.DataFrame({'pl': PL, 'brand': BRAND, 'p': PRIMER, 'os': OS})
first = pls[(pls.p > 0) & ~pls.os].groupby('pl').agg(L=('p','min'), brand=('brand','first'))
new = first[first.L >= 2022*12+9].copy()
new['vol6'] = [ACT[(PL==p)&~OS][:, k(L):k(L)+6].sum() for p, L in zip(new.index, new.L)]
new = new[new.vol6 >= 5000].sort_values('L')
house_reg = lambda mask: mask & ~OS & (PRIMER > 0)
out = []
for p, r in new.iterrows():
    L = r.L
    for M, nm, ok0 in [(ACT, 'sell-in', T0), (EPOS, 'EPOS', 2024*12+6)]:
        if L - 6 < ok0 or L + 5 > T1: continue
        sib = (BRAND == r.brand) & (PL != p) & ~OS & (PRIMER > 0) & (PRIMER <= L-12)
        ctrl = (BRAND != r.brand) & ~OS & (PRIMER > 0) & (PRIMER <= L-12)
        f = lambda mm, a, b: np.nansum(M[mm][:, k(a):k(b)+1])
        s_pre, s_post, c_pre, c_post = f(sib, L-6, L-1), f(sib, L, L+5), f(ctrl, L-6, L-1), f(ctrl, L, L+5)
        did = np.log(s_post/s_pre) - np.log(c_post/c_pre)
        # placebo un año antes
        pl_ = np.nan
        if L - 18 >= ok0:
            a, b, c, d = f(sib, L-18, L-13), f(sib, L-12, L-7), f(ctrl, L-18, L-13), f(ctrl, L-12, L-7)
            pl_ = np.log(b/a) - np.log(d/c)
        out.append(dict(PL_nueva=p[:38], brand=r.brand[:16], L=m(L), vol6=int(r.vol6), rel=r.vol6/max(s_pre,1), medida=nm, did=did, placebo=pl_, efecto_neto=did - pl_ if not np.isnan(pl_) else np.nan))
R = pd.DataFrame(out)
pd.set_option('display.width', 250)
R['did%'] = np.expm1(R.did).map('{:+.0%}'.format); R['neto%'] = np.expm1(R.efecto_neto).map(lambda v: '' if np.isnan(v) else f'{v:+.0%}')
print(R[['PL_nueva','brand','L','vol6','rel','medida','did%','neto%']].round(2).to_string(index=False))
v = R[R.medida=='sell-in'].efecto_neto.dropna(); print(f'\nSell-in, efecto neto sobre el resto de la brand: n={len(v)} mediana {np.expm1(v.median()):+.0%}  P(<0)={(v<0).mean():.0%}')
v = R[R.medida=='EPOS'].did.dropna(); print(f'EPOS (DiD sin placebo): n={len(v)} mediana {np.expm1(v.median()):+.0%}  P(<0)={(v<0).mean():.0%}')
