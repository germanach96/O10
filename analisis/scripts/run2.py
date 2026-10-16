import sys; sys.path.insert(0, '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad')
from minero import *
from base import m
S = '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad'
Z = pd.read_pickle(S+'/ind.pkl')
L = lambda a, b: np.log((a+1)/(b+1))
# extrapolación estándar: mismos 3 meses del año pasado x trend de 6 meses (recortado)
Z['tr6'] = np.clip(np.exp(Z.s_yoy6), 0.2, 5)
Z['base_ext'] = Z.y3_ly * Z.tr6
Z['sorpresa'] = L(Z.y3, Z.base_ext)
Z.to_pickle(S+'/ind2.pkl')
P = Z[(Z.os == 0) & (Z.s12 >= 150) & (Z.edad >= 13) & Z.sorpresa.notna() & (Z.base_ext >= 30)].copy()
P['Y_muy_por_debajo'] = (P.sorpresa < np.log(.7)).astype(float)
P['Y_muy_por_encima'] = (P.sorpresa > np.log(1.4)).astype(float)
feats = [c for c in Z.columns if c not in EXCL and not c.startswith('Y_') and c not in ('y3','y3_ly','s12','tr6','base_ext','sorpresa')]
sin_epos = [f for f in feats if not (f.startswith('e_') or '_e_' in f or f.endswith('_e') or f in ('st3','st3_raw','stock6','div3','div_mom'))]
pd.set_option('display.width', 250); pd.set_option('display.max_colwidth', 110)
print('Extrapolación estándar: WAPE 3M agregado', f'{(P.y3-P.base_ext).abs().sum()/P.y3.sum():.0%}', ' bias', f'{(P.y3.sum()-P.base_ext.sum())/P.y3.sum():+.0%}')
corte = 2025*12+3; res = {}
for y in ['Y_muy_por_debajo', 'Y_muy_por_encima']:
    Dd, Dv = P[P.F < corte], P[P.F >= corte]
    R, bd, bv, conds = minar(Dd, Dv, y, sin_epos)
    res[y] = R
    dv = diversas(R, 10)
    print(f'\n### {y} · descubrir {m(Dd.F.min())}-{m(Dd.F.max())} (n={len(Dd)}), validar {m(Dv.F.min())}-{m(Dv.F.max())} (n={len(Dv)}) · base {bd:.0%}/{bv:.0%} · probadas {len(R)} · confirmadas {R.confirmada.sum()}')
    if len(dv): print(dv[['regla','n_desc','p_desc','n_val','cod_val','p_val','lb_val','q']].round(3).to_string(index=False))
pd.to_pickle(res, S+'/run2.pkl')
