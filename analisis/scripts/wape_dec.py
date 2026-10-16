"""¿De dónde sale el WAPE? Descomposición del error absoluto del forecast real (regulares, h=1..3, fotos limpias 2026.M02-M06)."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, S := '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad')
from base import m, ATR
fv = pd.read_pickle(S+'/fva_arm.pkl'); Z = pd.read_pickle(S+'/ind4.pkl')
d = fv[(~fv.os) & fv.h.between(1, 3) & (fv.foto >= 2026*12+1) & (fv.foto <= 2026*12+5)].copy()
d['cons'] = d.cons_arm.clip(lower=0); d['err'] = (d.cons - d.A).abs(); d['sgn'] = d.cons - d.A
d = d.merge(Z[['F','ean','s12','mu12','cut3','last3_vs_rate','zeros3','s_cv12','edad','e_yoy3','s_yoy3']].rename(columns={'F':'foto'}), on=['foto','ean'], how='left')
A = d.A.sum(); E = d.err.sum()
print(f'Fotos limpias 2026.M02-M06 · regulares · meses 1-3: WAPE90 {E/A:.1%}  SPP3 {-d.sgn.sum()/A:+.1%}  códigos {d.ean.nunique()}')
# concentración por código
pc = d.groupby('ean').agg(err=('err','sum'), A=('A','sum'), C=('cons','sum'))
pc = pc.sort_values('err', ascending=False); pc['cum'] = pc.err.cumsum()/E
print('\nConcentración del error: top 10 códigos =', f'{pc.err.head(10).sum()/E:.0%}', ' top 20 =', f'{pc.err.head(20).sum()/E:.0%}', ' top 40 =', f'{pc.err.head(40).sum()/E:.0%}', ' de', len(pc))
pc = pc.join(ATR[['Planning Item Description','Brand','Final Segment']])
pc['wape'] = pc.err/pc.A; pc['spp'] = (pc.A-pc.C)/pc.A
pd.set_option('display.width', 250); pd.set_option('display.max_colwidth', 42)
print(pc.head(15)[['Planning Item Description','Final Segment','A','C','err','wape','spp','cum']].round(2).to_string())
# por tamaño
d['tam'] = pd.cut(d.s12, [0, 4000, 20000, 60000, 1e9], labels=['< 4k/año','4-20k','20-60k','> 60k'])
print('\nPor tamaño del código (sell-in 12M):')
for t, g in d.groupby('tam', observed=True):
    print(f'   {t:9s} códigos {g.ean.nunique():3d}  % del volumen {g.A.sum()/A:4.0%}  % del error {g.err.sum()/E:4.0%}  WAPE {g.err.sum()/g.A.sum():.0%}  SPP {-g.sgn.sum()/g.A.sum():+.0%}')
# por tipo de mes
d['da_m'] = np.select([d.tda_fut_arm > .5*d.cons.clip(lower=1), d.tda_fut_arm > 0, d.tda_fut_arm < 0], ['DA dominante','DA parcial','DA negativo'], 'sin DA')
print('\nPor DA del mes:')
for t, g in d.groupby('da_m'):
    print(f'   {t:13s} filas {len(g):4d}  % volumen {g.A.sum()/A:4.0%}  % error {g.err.sum()/E:4.0%}  WAPE {g.err.sum()/g.A.sum():.0%}  SPP {-g.sgn.sum()/g.A.sum():+.0%}  sobre-forecast en unidades {g.sgn.clip(lower=0).sum()/E:.0%} del error total')
print('\nError: sobre-forecast vs infra-forecast:', f'sobre {d.sgn.clip(lower=0).sum()/E:.0%}  infra {(-d.sgn).clip(lower=0).sum()/E:.0%}')
# meses de pico (actual > 2x media) — pedidos grandes no previstos
d['pico'] = d.A > 2*d.mu12
print(f'Meses con pedido grande real (actual > 2x media): {d.pico.mean():.0%} de las filas, {d[d.pico].err.sum()/E:.0%} del error')
d['valle'] = (d.A < .25*d.mu12) & (d.cons > .5*d.mu12)
print(f'Meses vacíos con forecast normal (actual < 25% media y forecast > 50% media): {d.valle.mean():.0%} de las filas, {d[d.valle].err.sum()/E:.0%} del error')
d.to_pickle(S+'/wape_dec.pkl')
