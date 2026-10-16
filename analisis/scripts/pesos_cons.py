"""Pesos por señal para cada categoría: cribado por estabilidad, logística conjunta y validación fuera de muestra."""
import numpy as np
import pandas as pd
from scipy.stats import fisher_exact
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, brier_score_loss

S = '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad'
P, X, SIGDF = pd.read_pickle(S + '/cons_lib.pkl')
OBJ = {'Y_bajo': 'Real más bajo', 'Y_muy_bajo': 'Real mucho más bajo', 'Y_alto': 'Real más alto', 'Y_muy_alto': 'Real mucho más alto', 'Y_orden': 'Orden no prevista'}
CORTE = 2026 * 12 + 1
rng = np.random.default_rng(11)
cods = P.ean.unique().copy(); rng.shuffle(cods)
mitad = dict(zip(cods, np.arange(len(cods)) % 2)); P['mitad'] = P.ean.map(mitad)
fold = dict(zip(cods, np.arange(len(cods)) % 5)); P['fold'] = P.ean.map(fold)
# disponibilidad de las señales de EPOS: filas con EPOS de 3 meses comparable
EP_OK = P.e_yoy3.notna() | P.st3.notna() | P.e_last3_vs_rate.notna()
epos = dict(zip(SIGDF.id, SIGDF.epos))


def lor(x, y):
    a = ((x == 1) & (y == 1)).sum() + .5; b = ((x == 1) & (y == 0)).sum() + .5
    c = ((x == 0) & (y == 1)).sum() + .5; d = ((x == 0) & (y == 0)).sum() + .5
    return np.log(a * d / (b * c)), int((x == 1).sum())


def cribar(y):
    filas = []
    for sid in X.columns:
        x = X[sid]
        if epos[sid]:
            base = EP_OK
            parts = [base & (P.mitad == 0), base & (P.mitad == 1)]
        else:
            base = pd.Series(True, index=P.index)
            parts = [P.F < CORTE, P.F >= CORTE]
        l1, n1 = lor(x[parts[0]], P[y][parts[0]]); l2, n2 = lor(x[parts[1]], P[y][parts[1]])
        lt, nt = lor(x[base], P[y][base])
        tab = [[int(((x == 1) & (P[y] == 1) & base).sum()), int(((x == 1) & (P[y] == 0) & base).sum())],
               [int(((x == 0) & (P[y] == 1) & base).sum()), int(((x == 0) & (P[y] == 0) & base).sum())]]
        p = fisher_exact(tab)[1]
        pon = P[y][base & (x == 1)].mean() if nt else np.nan
        ok = (min(n1, n2) >= 20) and (np.sign(l1) == np.sign(l2)) and (min(abs(l1), abs(l2)) >= .3) and (p < .05)
        filas.append(dict(id=sid, lor=lt, lor1=l1, lor2=l2, n=nt, p=p, p_si=pon, ok=ok))
    return pd.DataFrame(filas)


def ajustar(y, ids, C=0.2):
    m = LogisticRegression(C=C, max_iter=5000)
    m.fit(X[ids], P[y])
    return m


RES = {}
for y, nombre in OBJ.items():
    cr = cribar(y)
    ids = list(cr[cr.ok].sort_values('lor', key=abs, ascending=False).id)
    # quitar redundantes: correlación > 0,6 con una ya elegida
    sel = []
    for s in ids:
        if all(abs(np.corrcoef(X[s], X[t])[0, 1]) < .6 for t in sel):
            sel.append(s)
    # logística conjunta; fuera las que cambian de signo o pesan poco
    for _ in range(6):
        m = ajustar(y, sel)
        co = dict(zip(sel, m.coef_[0]))
        uni = dict(zip(cr.id, cr.lor))
        quitar = [s for s in sel if np.sign(co[s]) != np.sign(uni[s]) or abs(co[s]) < .12]
        if not quitar:
            break
        sel = [s for s in sel if s not in quitar]
    m = ajustar(y, sel)
    co = pd.Series(m.coef_[0], index=sel)
    # validación: CV por código (5 pliegues) y split temporal
    pcv = np.zeros(len(P))
    for k in range(5):
        tr, te = P.fold != k, P.fold == k
        mk = LogisticRegression(C=0.2, max_iter=5000).fit(X.loc[tr, sel], P.loc[tr, y])
        pcv[te.to_numpy()] = mk.predict_proba(X.loc[te, sel])[:, 1]
    mt = LogisticRegression(C=0.2, max_iter=5000).fit(X.loc[P.F < CORTE, sel], P.loc[P.F < CORTE, y])
    pt = mt.predict_proba(X.loc[P.F >= CORTE, sel])[:, 1]
    yt = P.loc[P.F >= CORTE, y]
    auc_cv, auc_t = roc_auc_score(P[y], pcv), roc_auc_score(yt, pt)
    print(f'\n######## {nombre}: base {P[y].mean():.0%} · señales estables {int(cr.ok.sum())} → en el modelo {len(sel)} · AUC CV por código {auc_cv:.2f} · AUC antiguo→reciente {auc_t:.2f} · Brier {brier_score_loss(P[y], pcv):.3f} (base {brier_score_loss(P[y], np.full(len(P), P[y].mean())):.3f})')
    tab = SIGDF.set_index('id').loc[sel, ['familia', 'texto']].assign(peso=co.round(2), puntos=(co * 10).round().astype(int))
    tab = tab.join(cr.set_index('id')[['n', 'p_si', 'lor1', 'lor2']])
    print(f'   punto de partida (ninguna señal activa): {1 / (1 + np.exp(-m.intercept_[0])):.0%}  (intercepto {m.intercept_[0]:.2f})')
    pd.set_option('display.width', 250); pd.set_option('display.max_colwidth', 95)
    print(tab.sort_values('puntos', ascending=False)[['puntos', 'texto', 'n', 'p_si']].to_string())
    # calibración CV
    b = pd.cut(pcv, [0, .1, .2, .3, .4, .5, .6, .7, .8, .9, 1.0])
    cal = pd.DataFrame({'p': pcv, 'y': P[y], 'b': b}).groupby('b', observed=True).agg(n=('y', 'size'), pred=('p', 'mean'), obs=('y', 'mean'))
    print('   calibración (CV por código): ' + ' | '.join(f'{str(i)}: pred {r.pred:.0%} obs {r.obs:.0%} n={r.n}' for i, r in cal.iterrows()))
    RES[y] = dict(nombre=nombre, sel=sel, coef=co, intercept=float(m.intercept_[0]), auc_cv=auc_cv, auc_t=auc_t, pcv=pcv, criba=cr, cal=cal, tab=tab)
pd.to_pickle(RES, S + '/pesos_cons_0.2.pkl')
