import numpy as np, pandas as pd
S = '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad'
FOTOS = ['2025.M09','2025.M10','2025.M11','2025.M12','2026.M01','2026.M02','2026.M03','2026.M04','2026.M05','2026.M06']
RC = pd.read_csv(S+'/recetas.csv')
D = {f: dict(np.load(f'{S}/np_{f}.npz', allow_pickle=True)) for f in FOTOS}
# WAPE90 por receta fija, agregado sobre todas las fotos (tramo 1), solo códigos con receta válida en esa foto
num = np.zeros(75816); den = 0; cons = 0; numv = np.zeros(75816); denv = np.zeros(75816)
porfoto = {}
for f in FOTOS:
    d = D[f]; m = d['cer'][:, 0]
    a = np.where(d['val'][m], d['abs'][m][:, :, 0], np.nan)
    act = d['act'][m, 0]
    numv += np.nansum(a, 0); denv += (np.where(~np.isnan(a), act[:, None], 0)).sum(0)
    cons += d['cabs'][m, 0].sum(); den += act.sum()
    porfoto[f] = (np.nansum(a, 0) / (np.where(~np.isnan(a), act[:, None], 0)).sum(0), d['cabs'][m, 0].sum()/act.sum())
w = numv / denv
RC['wape90'] = w
print(f'Consensus WAPE90 (10 fotos): {cons/den:.1%}')
print('\nMejores 10 recetas FIJAS (la misma para todos los códigos y fotos), ex post:')
print(RC.sort_values('wape90').head(10).to_string(index=False))
def q(**kw):
    m = np.ones(len(RC), bool)
    for k, v in kw.items(): m &= RC[k].eq(v)
    return RC[m].sort_values('wape90').head(1)
print('\nRecetas de referencia:')
for nm, kw in [('Naive estacional (s=1 propio e=1, w=0, c=0, p=0)', dict(s=1, h='Propio', e=1, w=0, c=0, p=0, m=0, N=12, g=0)),
               ('Media plana 12M (s=0, w=0, c=0, p=0)', dict(s=0, w=0, c=0, p=0, m=0, N=12, g=0, e=1, h='Propio')),
               ('Media plana + trend propio sell-in 12M', dict(s=0, w=1, c=0, p=0, m=0, N=12, g=0, e=1, h='Propio'))]:
    r = q(**kw); print(f'   {nm:50s} WAPE90 {float(r.wape90.iloc[0]):.1%}')
# estabilidad: ¿la mejor receta fija de una foto es buena en la siguiente?
print('\nMejor receta fija de cada foto, y cómo le va en la foto siguiente:')
for f, g in zip(FOTOS, FOTOS[1:]):
    wf, cf = porfoto[f]; wg, cg = porfoto[g]
    r = int(np.nanargmin(wf))
    print(f'   {f}: mejor fija {wf[r]:.0%} (cons {cf:.0%})  ->  en {g}: {wg[r]:.0%} (cons {cg:.0%}, mejor fija ex post {np.nanmin(wg):.0%})  {RC.loc[r, ["s","h","e","w","m","N","c","p","grupo"]].to_dict()}')
RC.to_pickle(S+'/rc_wape.pkl')
