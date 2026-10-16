import sys; sys.path.insert(0, '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad')
from minero import *
S = '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad'
out = pd.read_pickle(S+'/run5.pkl')
pd.set_option('display.width', 250); pd.set_option('display.max_colwidth', 110)
conf = {}
for (horiz, y), (R, Dd, Dv, bd, bv, conds) in out.items():
    A, C = ('A3','c3') if horiz == '3M' else ('A1','c1')
    R = R.copy(); R['lb_desc'] = wilson_lb(R.p_desc*R.n_desc, R.n_desc)
    sel = []
    for _, r in R[R.cod_desc >= 12].sort_values('lb_desc', ascending=False).iterrows():   # SOLO estadística de descubrimiento
        if all((r.mask_d & s.mask_d).sum() / max((r.mask_d | s.mask_d).sum(), 1) < 0.5 for s in sel): sel.append(r)
        if len(sel) >= 8: break
    sel = pd.DataFrame(sel)
    nd = np.sum([s for s in sel.mask_d], 0); nv = np.sum([s for s in sel.mask_v], 0)
    yd, yv = Dd[y].to_numpy().astype(bool), Dv[y].to_numpy().astype(bool)
    print(f'\n######## Consensus {horiz} · {y} · 8 señales elegidas solo con descubrimiento')
    print(sel[['regla','n_desc','p_desc','n_val','p_val']].round(2).to_string(index=False))
    print(f'   nº de señales activas -> P({y})  [base val {bv:.0%}]   y actual/Consensus')
    for lo, hi, nm in [(0,0,'0'), (1,1,'1'), (2,2,'2'), (3,99,'3+')]:
        md, mv = (nd >= lo) & (nd <= hi), (nv >= lo) & (nv <= hi)
        if mv.sum() == 0: continue
        lo_, hi_ = proportion_confint(int(yv[mv].sum()), int(mv.sum()), method='wilson')
        print(f'     {nm:3s} señales: descubrimiento {yd[md].mean():.0%} (n={md.sum()})   VALIDACIÓN {yv[mv].mean():.0%} [{lo_:.0%}-{hi_:.0%}] (n={mv.sum()}, {Dv.ean[mv].nunique()} cód.)   A/C val {Dv[A][mv].sum()/max(Dv[C][mv].sum(),1):.2f}')
    conf[(horiz, y)] = (sel, nd, nv)
pd.to_pickle(conf, S+'/confluencia.pkl')
