exec(open(S+'/adj.py').read().split('rows = []')[0]) if False else None
from base import *
src = open(S+'/adj.py').read().split('rows = []')[0]
exec(src)
# objetivo: WAPE + |SPP| (meta del equipo: WAPE bajo y SPP cerca de 0)
def obj(g, bg, r):
    f = ajuste(g, bg, r); return wape(f, g.A) + abs((g.A.sum() - f.sum()) / g.A.sum())
rows = []
for F in FOT:
    tr = d[(d.foto <= F - 4)]; te = d[d.foto == F]
    for sub, a, b in [('Regular', tr[~tr.os], te[~te.os]), ('One Shot', tr[tr.os], te[te.os])]:
        if len(a) < 50 or len(b) == 0: continue
        _, bg, r = min((obj(a, bg, r), bg, r) for bg in np.linspace(0, 1, 11) for r in np.linspace(0, 1, 11))
        _, r_only = min((obj(a, 0, r_), r_) for r_ in np.linspace(0, 1, 21))
        f2 = ajuste(b, bg, r); f1 = ajuste(b, 0, r_only)
        rows.append(dict(F=m(F), tipo=sub, A=b.A.sum(), b_gap=bg, rho=r, rho_solo=r_only,
                         W_cons=wape(b.cons, b.A), W_da=wape(f1, b.A), W_ambos=wape(f2, b.A),
                         S_cons=(b.A.sum()-b.cons.sum())/b.A.sum(), S_da=(b.A.sum()-f1.sum())/b.A.sum(), S_ambos=(b.A.sum()-f2.sum())/b.A.sum()))
R = pd.DataFrame(rows); pd.set_option('display.width', 250)
print(R.round(2).to_string(index=False))
for tipo, g in R.groupby('tipo'):
    w = g.A / g.A.sum()
    print(f'\n{tipo} (objetivo WAPE+|SPP|), {len(g)} fotos de prueba:')
    for c, s in [('W_cons','S_cons'),('W_da','S_da'),('W_ambos','S_ambos')]:
        print(f'   {c:8s} WAPE90 {(g[c]*w).sum():.1%}  SPP {(g[s]*w).sum():+.1%}  WAPE+|SPP| {((g[c]+g[s].abs())*w).sum():.1%}  mejor que Consensus (WAPE+|SPP|) en {((g[c]+g[s].abs()) < (g.W_cons+g.S_cons.abs())-1e-9).sum()}/{len(g)}')
