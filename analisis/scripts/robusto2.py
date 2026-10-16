import sys; sys.path.insert(0, '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad')
exec(open('/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad/run7.py').read().split("pd.set_option")[0])
RES = pd.read_pickle(S+'/run7.pkl')
import re
def parse(regla):
    out = []
    for c in regla.split(' Y '):
        mm = re.match(r'(\S+) (<=|>=|=) (.+)', c); f, op, v = mm.groups()
        try: v = float(v)
        except: pass
        out.append((f, op, v))
    return out
def mask(D, conds):
    mk = np.ones(len(D), bool)
    for f, op, v in conds:
        x = D[f].to_numpy()
        mk &= (x == v) if op == '=' else ((x <= v) if op == '<=' else (x >= v))
    return mk
filas = []
for nombre, (pob, hit, mag, magn) in EV.items():
    D = P[pob].copy().reset_index(drop=True); D['Y'] = hit[pob].astype(float).to_numpy(); D['mag'] = mag[pob].to_numpy()
    celdas = {'antiguo': D.F < corte, 'reciente': D.F >= corte, 'mitad A': (D.F >= 2024*12+9) & (D.mitad == 0), 'mitad B': (D.F >= 2024*12+9) & (D.mitad == 1)}
    cands = set()
    for tag, R, bd, bv in RES[nombre]:
        if len(R): cands |= set(diversas(R, 15, max_jac=0.5).regla) if R.confirmada.any() else set()
    for regla in cands:
        cs = parse(regla); mk = mask(D, cs)
        res, ok, test = {}, True, 0
        for cn, cm in celdas.items():
            b = D.Y[cm].mean(); n = (mk & cm).sum()
            if n < 15: res[cn] = (np.nan, n, b); continue
            p = D.Y[mk & cm].mean(); test += 1
            res[cn] = (p, n, b)
            umbral = 2*b if b < 0.2 else b + 0.15
            ok &= p >= umbral
        nmes = D.F[mk].nunique()
        if test >= 3 and ok and nmes >= 4:
            filas.append(dict(evento=nombre, regla=regla, n=int(mk.sum()), cod=D.ean[mk].nunique(), p_total=D.Y[mk].mean(), base=D.Y.mean(),
                              p_min=min(v[0] for v in res.values() if not np.isnan(v[0])), mag=np.median(D.mag[mk]), celdas_ok=test, meses=nmes,
                              **{cn: f'{v[0]:.0%} (n={v[1]})' if not np.isnan(v[0]) else f'— (n={v[1]})' for cn, v in res.items()}))
F = pd.DataFrame(filas)
pd.set_option('display.width', 280); pd.set_option('display.max_colwidth', 100); pd.set_option('display.max_rows', 200)
for ev, g in F.groupby('evento', sort=False):
    g = g.sort_values('p_min', ascending=False)
    print(f'\n######## {ev}  (base {g.base.iloc[0]:.0%}) · reglas robustas en todas las particiones: {len(g)}')
    print(g.head(12)[['regla','n','cod','meses','p_total','p_min','mag','antiguo','reciente','mitad A','mitad B']].round(2).to_string(index=False))
F.to_pickle(S+'/robustas2.pkl')
