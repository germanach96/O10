from base import *
from scipy import stats
W = 6
L = pd.DataFrame({'i': range(len(EANS)), 'primer': PRIMER, 'os': OS, 'brand': BRAND, 'pl': PL})
L = L[L.primer >= 2022*12+8]
L['vol6'] = [ACT[i, k(p):k(p)+W].sum() for i, p in zip(L.i, L.primer)]
def eventos(df, clave):
    ev = []
    for key, g in df.sort_values('primer').groupby(clave):
        # agrupar lanzamientos de la misma clave separados <= 3 meses
        grupo = []
        for _, r in g.iterrows():
            if grupo and r.primer - grupo[-1].primer > 3:
                ev.append(grupo); grupo = []
            grupo.append(r)
        if grupo: ev.append(grupo)
    out = []
    for g in ev:
        out.append(dict(key=g[0][clave], brand=g[0].brand, pl=g[0].pl, L=min(r.primer for r in g), launch_idx=[r.i for r in g], vol=sum(r.vol6 for r in g)))
    return pd.DataFrame(out)
nuevos = set(L.i)
def did(ev, sib_mask_fn, nombre, usar_epos=False):
    res = []
    M = EPOS if usar_epos else ACT
    for _, e in ev.iterrows():
        Lm = e.L
        if k(Lm-W) < 0 or k(Lm+W-1) >= NM: continue
        if usar_epos and (Lm - W < 2024*12+6): continue
        maduro = (PRIMER > 0) & (PRIMER <= Lm - 12) & ~OS
        sib = sib_mask_fn(e) & maduro
        sib[list(e.launch_idx)] = False
        ctrl = maduro & (BRAND != e.brand)
        if sib.sum() == 0: continue
        pre = slice(k(Lm-W), k(Lm)); post = slice(k(Lm), k(Lm+W))
        s_pre, s_post = np.nansum(M[sib][:, pre]), np.nansum(M[sib][:, post])
        c_pre, c_post = np.nansum(M[ctrl][:, pre]), np.nansum(M[ctrl][:, post])
        if min(s_pre, s_post, c_pre, c_post) <= 0: continue
        d = np.log(s_post/s_pre) - np.log(c_post/c_pre)
        # placebo: mismo cálculo un año antes (estacionalidad propia del grupo)
        pl_ = np.nan
        if k(Lm-12-W) >= 0 and (not usar_epos or Lm-12-W >= 2024*12+6):
            pre0 = slice(k(Lm-12-W), k(Lm-12)); post0 = slice(k(Lm-12), k(Lm-12+W))
            a, b, c_, dd = np.nansum(M[sib][:, pre0]), np.nansum(M[sib][:, post0]), np.nansum(M[ctrl][:, pre0]), np.nansum(M[ctrl][:, post0])
            if min(a,b,c_,dd) > 0: pl_ = np.log(b/a) - np.log(dd/c_)
        rel = e.vol / max(s_pre, 1)
        res.append(dict(key=e.key, L=m(Lm), n_sib=int(sib.sum()), vol_lanz=e.vol, rel=rel, did=d, placebo=pl_, ddd=d - pl_ if not np.isnan(pl_) else np.nan))
    R = pd.DataFrame(res)
    if R.empty: print(nombre, 'sin eventos'); return R
    print(f'\n{nombre}: {len(R)} eventos')
    for col in ['did', 'ddd']:
        v = R[col].dropna()
        if len(v) < 3: continue
        t = stats.ttest_1samp(v, 0); w = stats.wilcoxon(v) if len(v) >= 6 else None
        print(f'  {col}: media {np.expm1(v.mean()):+.0%}  mediana {np.expm1(v.median()):+.0%}  P(efecto<0)={(v<0).mean():.0%}  n={len(v)}  t-test p={t.pvalue:.3f}' + (f'  wilcoxon p={w.pvalue:.3f}' if w else ''))
    big = R[R.rel >= 0.3]
    if len(big) >= 3:
        v = big.ddd.dropna() if big.ddd.notna().sum() >= 3 else big.did
        print(f'  lanzamientos grandes (>=30% del volumen previo de los hermanos): n={len(v)} media {np.expm1(v.mean()):+.0%}  P(<0)={(v<0).mean():.0%}')
    return R
pd.set_option('display.width', 250)
evR_pl = eventos(L[~L.os], 'pl')
evR_pl = evR_pl[evR_pl.vol >= 3000]
R1 = did(evR_pl, lambda e: PL == e.pl, 'REGULAR nuevo -> hermanos de la MISMA product line (sell-in)')
R2 = did(evR_pl, lambda e: (BRAND == e.brand) & (PL != e.pl), 'REGULAR nuevo -> otras product lines de la MISMA brand (sell-in)')
R1e = did(evR_pl, lambda e: PL == e.pl, 'REGULAR nuevo -> misma PL (EPOS)', True)
R2e = did(evR_pl, lambda e: (BRAND == e.brand) & (PL != e.pl), 'REGULAR nuevo -> otras PL misma brand (EPOS)', True)
evO_pl = eventos(L[L.os], 'pl'); evO_pl = evO_pl[evO_pl.vol >= 3000]
R3 = did(evO_pl, lambda e: PL == e.pl, 'ONE SHOT nuevo -> regulares de la MISMA product line (sell-in)')
R4 = did(evO_pl, lambda e: (BRAND == e.brand) & (PL != e.pl), 'ONE SHOT nuevo -> regulares de otras PL de la misma brand (sell-in)')
R3e = did(evO_pl, lambda e: PL == e.pl, 'ONE SHOT nuevo -> regulares misma PL (EPOS)', True)
print('\nDetalle regular -> misma PL:'); print(R1.round(2).to_string(index=False))
print('\nDetalle one shot -> misma PL:'); print(R3.round(2).to_string(index=False))
pd.to_pickle(dict(R1=R1,R2=R2,R1e=R1e,R2e=R2e,R3=R3,R4=R4,R3e=R3e), S+'/lanz.pkl')
