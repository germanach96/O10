import sys; sys.path.insert(0, '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad')
from minero import *
from base import m
S = '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad'
G = pd.read_pickle(S+'/indfoto.pkl'); corte = 2026*12+1
noY = {'y3','y3_ly','s12','tr6','base_ext','sorpresa','base_rob','sorp_rob','I_br','A3','A1','c3','c1','da3','da1','sys3','init3','prom3','c46','c79','c3_prev1','c3_prev3','flag','solo_nuevo','c_vol','lan_pl_next3','lan_br_next3','os','brand','meses_a_disco','i'}
feats = [c for c in G.columns if c not in EXCL and c not in noY and not c.startswith('Y_')]
P = G[(G.F <= 2026*12+5) & (G.c3 >= 60) & (G.os == 1) & ~((G.F < corte) & G.solo_nuevo)].copy()
P['Y_sobre'] = (P.A3 < 0.7*P.c3).astype(float); P['Y_infra'] = (P.A3 > 1.3*P.c3).astype(float)
pd.set_option('display.width', 250); pd.set_option('display.max_colwidth', 120)
out = {}
for y in ['Y_sobre', 'Y_infra']:
    # se mina en las dos direcciones del tiempo y se exige que la regla se confirme en ambas
    res = []
    for nm, Dd, Dv in [('25→26', P[P.F < corte].reset_index(drop=True), P[P.F >= corte].reset_index(drop=True)),
                       ('26→25', P[P.F >= corte].reset_index(drop=True), P[P.F < corte].reset_index(drop=True))]:
        R, bd, bv, conds = minar(Dd, Dv, y, feats, min_n=25, min_cod=8)
        R['A/C val'] = [np.median((Dv.A3/Dv.c3)[mv]) if mv.sum() else np.nan for mv in R.mask_v]
        res.append((nm, R, bd, bv, Dd, Dv))
    (n1, R1, bd1, bv1, D1d, D1v), (n2, R2, bd2, bv2, D2d, D2v) = res
    print(f'\n### ONE SHOT {y}: base 2025 {bd1:.0%} / 2026 {bv1:.0%} · confirmadas 25→26: {R1.confirmada.sum()} · 26→25: {R2.confirmada.sum()}')
    sel = diversas(R1, 12, max_jac=0.4)
    if len(sel): print(sel[['regla','n_desc','p_desc','n_val','cod_val','p_val','lb_val','A/C val']].round(2).to_string(index=False))
    sel2 = diversas(R2, 8, max_jac=0.4)
    print('   -- descubiertas en 2026 y confirmadas en 2025:')
    if len(sel2): print(sel2[['regla','n_desc','p_desc','n_val','cod_val','p_val','lb_val','A/C val']].round(2).to_string(index=False))
    out[y] = (sel, sel2, R1, R2)
pd.to_pickle(out, S+'/run6_os.pkl')
