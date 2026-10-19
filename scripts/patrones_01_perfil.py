"""Paso 1 de la búsqueda de patrones: perfil de todos los CSV de data/ (estructura, calidad, grupos).

Uso: python -m scripts.patrones_01_perfil   (desde la raíz del repo)
Escribe resultados/perfil_datos.json y saca un resumen por pantalla.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from motor.lector import int_a_mes, leer_foto

RAIZ = Path(__file__).resolve().parents[1]
CFG = json.loads((RAIZ / "motor" / "config.json").read_text(encoding="utf-8"))


def perfil_casa(carpeta: Path) -> dict | None:
    rutas = sorted(carpeta.glob("Consensus/*.csv"))
    if not rutas:
        return None
    fotos = [leer_foto(r, CFG) for r in rutas]
    ult = fotos[-1]
    out = {"casa": ult.casa, "fotos": [f.etiqueta for f in fotos], "avisos": sorted({a for f in fotos for a in f.avisos})}
    # calidad bruta de la última foto (celdas vacías por columna, negativos)
    df = ult.df
    num = ["Actuals", "EPOS", "Supply Cuts", "Total Demand Assumption", "Consensus - Final", "System FC - Final"]
    pas = df.t < ult.mes
    out["calidad_ultima"] = {
        c: {"vacias_pasado_%": round(100 * df.loc[pas, c].isna().mean(), 1),
            "negativos": int((df[c] < 0).sum()), "suma_pasado": round(float(df.loc[pas, c].sum()), 0)}
        for c in num if c in df}
    out["historia"] = [int_a_mes(int(df.t.min())), int_a_mes(int(df.t.max()))]
    # EPOS: primer mes con dato a nivel casa
    ep = df[df.EPOS.notna() & pas]
    out["epos_desde"] = int_a_mes(int(ep.t.min())) if len(ep) else None
    out["epos_cobertura_codigos_%"] = round(100 * ep.EAN.nunique() / max(df.EAN.nunique(), 1), 1)
    # EANs por foto y altas/bajas
    out["eans_por_foto"] = {f.etiqueta: len(f.eans) for f in fotos}
    sets = [set(f.eans) for f in fotos]
    out["altas_bajas"] = {fotos[i].etiqueta: [len(sets[i] - sets[i - 1]), len(sets[i - 1] - sets[i])]
                          for i in range(1, len(fotos))}
    # salto de historia entre fotos consecutivas (rupturas de perímetro)
    salto = {}
    for a, b in zip(fotos[:-1], fotos[1:]):
        v = (a.meses >= a.mes - 24) & (a.meses < a.mes)
        w = (b.meses >= a.mes - 24) & (b.meses < a.mes)
        sa, sb = np.nansum(a.mat["Actuals"][:, v]), np.nansum(b.mat["Actuals"][:, w])
        salto[b.etiqueta] = round(100 * (sb / sa - 1), 1) if sa else None
    out["salto_historia_24m_%"] = salto
    # grupos en la última foto
    c = ult.codigos
    out["n_eans"] = len(c)
    out["por_tipo"] = dict(Counter(c["Article Type"]))
    out["por_responsable"] = dict(Counter(c["Final Responsibility"].replace("", "(vacío)")))
    out["por_segmento"] = dict(Counter(c["Final Segment"].replace("", "(vacío)")))
    out["por_edad"] = dict(Counter(c["tramo_edad"]))
    out["por_tamano_top"] = dict(Counter(c["tamano"].fillna("(sin tamaño)")).most_common(12))
    out["sin_tamano"] = int(c["tamano"].isna().sum() + (c["tamano"] == "").sum())
    out["n_brands"] = int(c.Brand.nunique())
    out["n_lineas"] = int(c["Product Line"].nunique())
    out["brands"] = {b: int(n) for b, n in c.Brand.value_counts().items()}
    out["scope_central"] = int(c.scope.sum())
    out["disco_real"] = int(c.disco_mes.notna().sum())
    # códigos con volumen suficiente para patrones (regular, ≥ 150 uds en 12M, ≥ 13 meses)
    v12 = np.nansum(ult.mat["Actuals"][:, (ult.meses >= ult.mes - 12) & (ult.meses < ult.mes)], 1)
    ok = c["Article Type"].eq("Regular Item").to_numpy() & (v12 >= 150) & (c.edad_meses.to_numpy() >= 13)
    out["regulares_analizables"] = int(ok.sum())
    out["vol12_casa"] = round(float(v12.sum()), 0)
    # concentración: cuánto pesa el top 10
    s = np.sort(v12)[::-1]
    out["top10_%_vol12"] = round(100 * s[:10].sum() / max(s.sum(), 1), 1)
    # meses con forecast medible: fotos cuyo F+1..F+3 ya cerró en la última foto
    out["fotos_con_3m_cerrados"] = [f.etiqueta for f in fotos if f.mes + 3 <= ult.mes - 1]
    return out


def main():
    res = []
    for carpeta in sorted((RAIZ / "data").iterdir()):
        if carpeta.is_dir():
            p = perfil_casa(carpeta)
            res.append(p or {"casa": carpeta.name, "fotos": []})
    salida = RAIZ / "resultados"
    salida.mkdir(exist_ok=True)
    (salida / "perfil_datos.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    for p in res:
        print(json.dumps(p, ensure_ascii=False, indent=None)[:4000], "\n")


if __name__ == "__main__":
    main()
