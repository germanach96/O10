import sys; sys.path.insert(0, '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad')
from minero import *
from base import m
S = '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad'
Z = pd.read_pickle(S+'/ind3.pkl')
P = Z[(Z.os == 0) & (Z.s12 >= 150) & (Z.edad >= 13) & Z.sorp_rob.notna() & (Z.base_rob >= 30)].copy()
corte = 2025*12+3
med = P[P.F < corte].sorp_rob.median()
P['Y_debajo'] = (P.sorp_rob < med - 0.4).astype(float)
P['Y_encima'] = (P.sorp_rob > med + 0.4).astype(float)
print(f'sorpresa mediana en descubrimiento {np.expm1(med):+.0%}: "debajo" = actual < {np.exp(med-.4):.2f} x base, "encima" = actual > {np.exp(med+.4):.2f} x base')
noY = ('y3','y3_ly','s12','tr6','base_ext','sorpresa','base_rob','sorp_rob','I_br')
feats = [c for c in Z.columns if c not in EXCL and not c.startswith('Y_') and c not in noY]
sin_epos = [f for f in feats if not (f.startswith('e_') or '_e_' in f or f.endswith('_e') or f in ('st3','st3_raw','stock6','div3','div_mom'))]
pd.set_option('display.width', 250); pd.set_option('display.max_colwidth', 110)
res = {}
for y in ['Y_debajo', 'Y_encima']:
    Dd, Dv = P[P.F < corte], P[P.F >= corte]
    R, bd, bv, conds = minar(Dd, Dv, y, sin_epos); res[y] = R
    dv = diversas(R, 12)
    print(f'\n### {y} · descubrir {m(Dd.F.min())}-{m(Dd.F.max())} (n={len(Dd)}), validar {m(Dv.F.min())}-{m(Dv.F.max())} (n={len(Dv)}) · base {bd:.0%}/{bv:.0%} · probadas {len(R)} · confirmadas {R.confirmada.sum()}')
    if len(dv): print(dv[['regla','n_desc','p_desc','n_val','cod_val','p_val','lb_val']].round(2).to_string(index=False))
pd.to_pickle((res, P), S+'/run3.pkl')
