"""Paso 2-3 de la búsqueda de patrones: tablas de casos (señales + resultados) de todas las casas.

Uso: python -m scripts.patrones_02_casos
Guarda resultados/cache/casos_{K,Y}.parquet y senales_{K,Y}.json, y comprueba que ninguna señal usa el futuro.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from motor import escenarios as es
from scripts import patrones_lib as pl

CACHE = pl.RAIZ / "resultados" / "cache"


def construir():
    CACHE.mkdir(parents=True, exist_ok=True)
    tablas = {"K": [], "Y": []}
    for casa in pl.CASAS:
        fotos, panel = pl.cargar(casa)
        k, kb, sn, vieja = es.perimetro(panel, pl.CFG["escenarios"]["ruptura_perimetro"].get(casa))
        K, S_motor, info = pl.casos_K(panel)
        Y, _ = pl.casos_Y(panel, k, kb, vieja)
        for nom, Z in (("K", K), ("Y", Y)):
            Z = pl.listas(pl.grupos(Z, panel))
            tablas[nom].append(Z)
            print(f"{casa:10s} {nom}: {len(Z):5d} casos · {Z.ean.nunique():3d} códigos · "
                  f"{Z.F.nunique():2d} fotos ({pl.int_a_mes(int(Z.F.min()))}…{pl.int_a_mes(int(Z.F.max()))}) · "
                  + " · ".join(f"{e} {Z[f'Y_{e}'].mean():.0%}" for e in pl.UMBRALES))
    for nom, lst in tablas.items():
        Z = pd.concat(lst, ignore_index=True)
        S = pl.senales(Z, con_consensus=(nom == "K"))
        X = pd.DataFrame({s["id"]: s["mask"] for s in S})
        meta = [{k: v for k, v in s.items() if k != "mask"} for s in S]
        Z = Z.loc[:, ~Z.columns.duplicated()]
        objetos = [c for c in Z.columns if Z[c].dtype == object]
        Z[objetos] = Z[objetos].astype(str)
        Z.to_parquet(CACHE / f"casos_{nom}.parquet")
        X.to_parquet(CACHE / f"senales_{nom}.parquet")
        (CACHE / f"senales_{nom}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=0), encoding="utf-8")
        print(f"Tabla {nom}: {len(Z)} casos, {len(S)} señales")


def comprobar_futuro():
    fallos = []
    for casa in pl.CASAS:
        fallos += pl.prueba_sin_futuro(casa, n_origenes=4)
    print("Prueba sin futuro:", "OK (ninguna señal cambia al borrar los meses ≥ F)" if not fallos else fallos)
    return fallos


if __name__ == "__main__":
    construir()
    comprobar_futuro()
