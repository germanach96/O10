"""Carga el cubo a numpy: por foto, abs/sgn (códigos x recetas x 3 tramos), act, cerrado, valida, cons."""
import duckdb, numpy as np, pandas as pd, pickle, glob, os
S = '/tmp/claude-0/-home-user-O10/27f9b52f-96ca-5cae-9c56-8ca1c5e82549/scratchpad'
NR = 75816
out = {}
for d in sorted(glob.glob(S+'/cubo_arm/casa=Gucci/foto=*'))[:10]:
    foto = d.split('=')[-1]
    t = duckdb.sql(f"select ean, receta, tramo, abs_err, sgn_err, act, cerrado, valida from read_parquet('{d}/recetas.parquet') order by ean, receta, tramo").df()
    eans = t.ean.astype(str).unique(); n = len(eans)
    a = t.abs_err.to_numpy(np.float32).reshape(n, NR, 3); s = t.sgn_err.to_numpy(np.float32).reshape(n, NR, 3)
    act = t.act.to_numpy(np.float32).reshape(n, NR, 3)[:, 0, :]; cer = t.cerrado.to_numpy().reshape(n, NR, 3)[:, 0, :]
    val = t.valida.to_numpy().reshape(n, NR, 3)[:, :, 0]
    c = pd.read_parquet(f'{d}/consensus.parquet'); c['ean'] = c.ean.astype(str)
    c = c.set_index(['ean','tramo']).reindex(pd.MultiIndex.from_product([eans, [1,2,3]]))
    np.savez(f'{S}/nparm_{foto}.npz', eans=eans, abs=a, sgn=s, act=act, cer=cer, val=val,
             cabs=c.cons_abs.to_numpy().reshape(n,3), csgn=c.cons_sgn.to_numpy().reshape(n,3))
    print(foto, n, cer.any(0), flush=True)
    del t, a, s
