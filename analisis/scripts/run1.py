import sys; sys.path.insert(0, '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad')
from minero import *
from base import m, BRAND
S = '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad'
Z = pd.read_pickle(S+'/ind.pkl')
P = Z[(Z.os == 0) & (Z.s12 >= 150) & (Z.edad >= 13)].copy()
P['Y_baja20'] = (P.Y_yoy3 < np.log(.8)).astype(float); P['Y_sube20'] = (P.Y_yoy3 > np.log(1.2)).astype(float)
P['Y_colapso'] = (P.y3 < 0.3 * P.y3_ly).astype(float)
feats = [c for c in Z.columns if c not in EXCL and not c.startswith('Y_') and c not in ('y3','y3_ly','s12')]
sin_epos = [f for f in feats if not (f.startswith('e_') or '_e_' in f or f.endswith('_e') or f in ('st3','st3_raw','stock6','div3','div_mom'))]
pd.set_option('display.width', 250); pd.set_option('display.max_colwidth', 120)
res = {}
# RUN A: split temporal, sin EPOS (historia larga)
corte = 2025*12+3
for y in ['Y_baja20', 'Y_sube20', 'Y_colapso', 'Y_big1']:
    D = P[P[y].notna() & P.Y_yoy3.notna()] if y != 'Y_big1' else P[P[y].notna()]
    Dd, Dv = D[D.F < corte], D[D.F >= corte]
    R, bd, bv, conds = minar(Dd, Dv, y, sin_epos, nombre=y)
    res[('A', y)] = (R, bd, bv)
    c = R[R.confirmada]
    print(f'\n### RUN A (tiempo: descubrir {m(Dd.F.min())}-{m(Dd.F.max())}, validar {m(Dv.F.min())}-{m(Dv.F.max())}) · {y}: base desc {bd:.0%} / val {bv:.0%} · reglas probadas {len(R)} · confirmadas {len(c)}')
    print(c.head(12)[['regla','n_desc','p_desc','n_val','cod_val','p_val','q']].round(3).to_string(index=False))
pd.to_pickle(res, S+'/runA.pkl')
