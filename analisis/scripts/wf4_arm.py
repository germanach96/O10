import numpy as np, pandas as pd, pickle
S = '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad'
RC = pd.read_csv(S+'/recetas.csv'); el = pickle.load(open(S+'/wf3_arm_elec.pkl','rb'))
cols = ['s','h','e','w','m','N','c','p','grupo']
print('Receta de Casa elegida en cada foto de prueba (con lo que se sabía):')
for F in ['2026.M01','2026.M02','2026.M03','2026.M04','2026.M05','2026.M06']:
    r = [v for (f, n, e), v in el.items() if f == F and n == 'Casa'][0]
    print('  ', F, RC.loc[r, cols].to_dict())
FOTOS = ['2025.M09','2025.M10','2025.M11','2025.M12','2026.M01','2026.M02','2026.M03','2026.M04','2026.M05','2026.M06']
key = ['s','h','e','c','p']
fb = RC.merge(RC[(RC.w==0)&(RC.m==0)&(RC.N==6)&(RC.g==0)][key+['receta']].rename(columns={'receta':'fb'}), on=key, how='left').fb.to_numpy()
# WAPE90 por foto de cada receta fija con respaldo
WR = {}
for f in FOTOS:
    d = np.load(f'{S}/nparm_{f}.npz', allow_pickle=True); m = d['cer'][:, 0]
    a = d['abs'][m][:, :, 0]; v = d['val'][m]; a = np.where(v, a, a[:, fb])
    WR[f] = (a.sum(0) / d['act'][m, 0].sum(), d['cabs'][m, 0].sum() / d['act'][m, 0].sum())
tot = np.mean([WR[f][0] for f in FOTOS], 0); r = int(np.argmin(tot))
print('\nMejor receta fija con respaldo (media de 10 fotos):', RC.loc[r, cols].to_dict(), f'{tot[r]:.1%}', ' Consensus medio', f'{np.mean([WR[f][1] for f in FOTOS]):.1%}')
print('  por foto:', '  '.join(f'{f[2:]}: {WR[f][0][r]:.0%} vs {WR[f][1]:.0%}' for f in FOTOS))
# ¿qué pasa si entreno solo con el tramo 1 y con la foto más reciente disponible (F-4)?
print('\nEntrenar con la mejor receta fija de la foto F-4 (la más reciente medida) -> aplicar en F:')
for i in range(4, len(FOTOS)):
    f0, F = FOTOS[i-4], FOTOS[i]; r0 = int(np.argmin(WR[f0][0]))
    acc = np.mean([WR[f][0] for f in FOTOS[:i-3]], 0); r1 = int(np.argmin(acc))
    print(f'   {F}: con {f0}: {WR[F][0][r0]:.0%}   con todas las medidas: {WR[F][0][r1]:.0%}   Consensus {WR[F][1]:.0%}   mejor ex post {WR[F][0].min():.0%}')
pickle.dump(WR, open(S+'/wr_arm.pkl','wb'))
