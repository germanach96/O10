import sys; sys.path.insert(0, '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad')
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score, brier_score_loss
from sklearn.inspection import permutation_importance
from statsmodels.stats.proportion import proportion_confint
from base import m
S = '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad'
out = pd.read_pickle(S+'/run5.pkl')
pd.set_option('display.width', 250)
modelos = {}
for (horiz, y), (R, Dd, Dv, bd, bv, conds) in out.items():
    A, C = ('A3','c3') if horiz == '3M' else ('A1','c1')
    feats = sorted({c[1] for c in conds})
    num = [f for f in feats if f not in ('seg','brand','mes_obj')]
    def X_(D):
        X = D[num].astype(float).replace([np.inf, -np.inf], np.nan).clip(-50, 50)
        for c in ['seg']:
            for v in sorted(Dd[c].dropna().unique()): X[f'{c}={v}'] = (D[c] == v).astype(float)
        return X
    Xd, Xv = X_(Dd), X_(Dv); yd, yv = Dd[y].astype(int), Dv[y].astype(int)
    gb = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=200, min_samples_leaf=25, l2_regularization=1.0, random_state=0).fit(Xd, yd)
    lr = make_pipeline(SimpleImputer(strategy='median', add_indicator=True), StandardScaler(), LogisticRegression(C=0.1, max_iter=2000)).fit(Xd, yd)
    pg, pl = gb.predict_proba(Xv)[:, 1], lr.predict_proba(Xv)[:, 1]
    print(f'\n######## Consensus {horiz} · {y} · validación {m(Dv.F.min())}-{m(Dv.F.max())} (n={len(Dv)}, base {yv.mean():.0%})')
    print(f'   AUC  boosting {roc_auc_score(yv, pg):.2f}   logística {roc_auc_score(yv, pl):.2f}    (0.5 = azar)')
    p = (pg + pl) / 2
    print(f'   AUC  media de ambos {roc_auc_score(yv, p):.2f}   Brier {brier_score_loss(yv, p):.3f} vs base {brier_score_loss(yv, np.full(len(yv), yd.mean())):.3f}')
    bins = [0, .2, .4, .6, .8, 1.01]
    Dv2 = Dv.assign(p=p)
    print('   puntuación (prob. predicha) -> % observado en validación   [actual/Consensus]')
    for lo, hi in zip(bins, bins[1:]):
        mk = (p >= lo) & (p < hi)
        if mk.sum() == 0: continue
        a, b = proportion_confint(int(yv[mk].sum()), int(mk.sum()), method='wilson')
        print(f'     {lo:.0%}-{min(hi,1):.0%}: n={mk.sum():4d} ({Dv.ean[mk].nunique():3d} cód.)  observado {yv[mk].mean():.0%} [{a:.0%}-{b:.0%}]   A/C {Dv[A][mk].sum()/max(Dv[C][mk].sum(),1):.2f}   volumen Cons {Dv[C][mk].sum():,.0f}')
    pi = permutation_importance(gb, Xv, yv, scoring='roc_auc', n_repeats=10, random_state=0)
    imp = pd.Series(pi.importances_mean, index=Xv.columns).sort_values(ascending=False)
    print('   indicadores que más pesan (pérdida de AUC al barajarlos):', ', '.join(f'{k} {v:.3f}' for k, v in imp.head(10).items()))
    modelos[(horiz, y)] = dict(gb=gb, lr=lr, cols=list(Xd.columns), num=num, p_val=p, imp=imp)
pd.to_pickle(modelos, S+'/modelos.pkl')
