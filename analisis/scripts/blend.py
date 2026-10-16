"""Combinar receta (elegida walk-forward) con el Consensus: ¿la mezcla gana a ambos?"""
import sys, pickle, json
src = open(sys.argv[1] + '/cubo_arm.py').read().split('t0 = time.time()')[0]
sys.argv = [sys.argv[0], sys.argv[1]]
exec(src)
RC = pd.read_csv(S/'recetas.csv'); key = ['s','h','e','c','p']
fb = RC.merge(RC[(RC.w==0)&(RC.m==0)&(RC.N==6)&(RC.g==0)][key+['receta']].rename(columns={'receta':'fb'}), on=key, how='left').fb.to_numpy()
el = pickle.load(open(S/'wf3_arm_elec.pkl','rb'))
LAM = [0, .25, .5, .75, 1.0]
NIV = ['Casa', 'Product Line', 'Edad', 'Segmento', 'Código']
acc = {(n, l, x): 0.0 for n in NIV for l in LAM for x in ['abs','sgn']}; acc_act = 0.0; cons_abs = cons_sgn = 0.0
porfoto = []
for f in fotos:
    if not (2026*12+0 <= f.mes <= 2026*12+5): continue
    r_ = calcular_foto(f, fotos, cfg, R, ()); M = r_.motor; A = r_.A
    F_lab = f.etiqueta; fa = {n: {'abs': np.zeros(len(LAM)), 'sgn': np.zeros(len(LAM))} for n in NIV}; fact = 0; fcons = 0
    for a, i in enumerate(r_.scope):
        e = f.eans[i]
        if (F_lab, 'Casa', e) not in el: continue
        act = A[i, :3]
        if np.isnan(act).any(): continue
        Fc, val = M.forecasts(i); C = M.cons_fut[i, :3]
        acc_act += act.sum(); fact += act.sum(); cons_abs += np.abs(C - act).sum(); cons_sgn += (C - act).sum(); fcons += np.abs(C-act).sum()
        for n in NIV:
            r = el[(F_lab, n, e)]; r = r if val[r] else fb[r]
            for j, l in enumerate(LAM):
                Fb = l * Fc[r, :3] + (1 - l) * C
                acc[(n, l, 'abs')] += np.abs(Fb - act).sum(); acc[(n, l, 'sgn')] += (Fb - act).sum()
                fa[n]['abs'][j] += np.abs(Fb - act).sum()
    porfoto.append((F_lab, fcons/fact, {n: fa[n]['abs']/fact for n in NIV}))
    print(F_lab, 'ok', flush=True)
print(f'\nConsensus: WAPE90 {cons_abs/acc_act:.1%}  SPP {-cons_sgn/acc_act:+.1%}')
for n in NIV:
    print(f'{n:14s} ' + '  '.join(f'λ={l:.2f}: {acc[(n,l,"abs")]/acc_act:.1%} (SPP {-acc[(n,l,"sgn")]/acc_act:+.0%})' for l in LAM))
print('\nPor foto, λ=0.25 / 0.5 frente al Consensus:')
for F_lab, c, d in porfoto:
    print(f'  {F_lab}: Consensus {c:.0%}  ' + '  '.join(f'{n[:6]} {d[n][1]:.0%}/{d[n][2]:.0%}' for n in NIV))
