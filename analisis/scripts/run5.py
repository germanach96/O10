import sys; sys.path.insert(0, '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad')
from minero import *
from base import m
S = '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad'
G = pd.read_pickle(S+'/indfoto.pkl')
noY = {'y3','y3_ly','s12','tr6','base_ext','sorpresa','base_rob','sorp_rob','I_br','A3','A1','c3','c1','da3','da1','sys3','init3','prom3','c46','c79','c3_prev1','c3_prev3','flag','solo_nuevo','c_vol'}
feats = [c for c in G.columns if c not in EXCL and c not in noY and not c.startswith('Y_')]
pd.set_option('display.width', 260); pd.set_option('display.max_colwidth', 105)
corte = 2026*12+1
out = {}
for horiz, A, C, fmax, cmin in [('3M', 'A3', 'c3', 2026*12+5, 60), ('1M', 'A1', 'c1', 2026*12+7, 20)]:
    P = G[(G.F <= fmax) & (G[C] >= cmin) & ~((G.F < corte) & G.solo_nuevo)].copy()
    P['Y_sobre'] = (P[A] < 0.7 * P[C]).astype(float)
    P['Y_infra'] = (P[A] > 1.3 * P[C]).astype(float)
    for y in ['Y_sobre', 'Y_infra']:
        Dd, Dv = P[P.F < corte].reset_index(drop=True), P[P.F >= corte].reset_index(drop=True)
        R, bd, bv, conds = minar(Dd, Dv, y, feats, min_n=35, min_cod=12)
        R['A/C val'] = [Dv[A][mv].sum() / max(Dv[C][mv].sum(), 1) for mv in R.mask_v]
        R['A/C desc'] = [Dd[A][md].sum() / max(Dd[C][md].sum(), 1) for md in R.mask_d]
        out[(horiz, y)] = (R, Dd, Dv, bd, bv, conds)
        dv = diversas(R, 10)
        print(f'\n### Consensus {horiz} · {y} · desc {m(Dd.F.min())}-{m(Dd.F.max())} n={len(Dd)} · val {m(Dv.F.min())}-{m(Dv.F.max())} n={len(Dv)} · base {bd:.0%}/{bv:.0%} · A/C global val {Dv[A].sum()/Dv[C].sum():.2f} · probadas {len(R)} · confirmadas {R.confirmada.sum()}')
        if len(dv): print(dv[['regla','n_desc','p_desc','n_val','cod_val','p_val','lb_val','A/C val']].round(2).to_string(index=False))
pd.to_pickle(out, S+'/run5.pkl')
