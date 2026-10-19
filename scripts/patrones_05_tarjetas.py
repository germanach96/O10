"""Entregables de la búsqueda de patrones: resultados/tarjetas_actuales.csv y resultados/tarjetas_nuevas.csv.

Uso: python -m scripts.patrones_05_tarjetas   (después de patrones_02_casos y patrones_03_reglas)

Tarjetas actuales:
- Las del motor de escenarios (motor/escenarios.py), frente a los 4 escenarios del Consensus (tabla K). "Lo que dice"
  cada una = el signo de sus puntos en el modelo de cada casa. Las que no tienen puntos se miden en el escenario
  con el que más se relacionan.
- Las del libro de señales (analisis/SENALES-2026-10.md) frente a su propio evento (caída, muerte, subida fuerte,
  mes vacío), con toda la historia (tabla Y). Las de pedido grande (G1-G4) quedan fuera, como la orden no prevista.
Veredicto: se confirma (≥ 5 puntos sobre la base en su dirección, igual en las fotos antiguas y en las recientes,
q < 0,10) · no se cumple (pasa lo contrario de lo que dice) · débil (el resto).
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from motor import escenarios as es
from scripts import patrones_lib as pl
from scripts import patrones_03_reglas as r3

CACHE = pl.RAIZ / "resultados" / "cache"
SALIDA = pl.RAIZ / "resultados"


def descripciones() -> dict:
    d = {}
    for casa in pl.CASAS:
        for ruta in sorted((pl.RAIZ / "data" / casa / "Consensus").glob("*.csv"))[-1:]:
            f = pd.read_csv(ruta, sep=";", skiprows=1, dtype=str, encoding="utf-8-sig", usecols=["EAN", "Planning Item Description"])
            d.update(f.dropna().drop_duplicates("EAN").set_index("EAN")["Planning Item Description"].str.strip().to_dict())
    return d


def puntos_motor(K: pd.DataFrame, X: pd.DataFrame, meta: list[dict]) -> dict:
    """Puntos de cada señal del motor en cada casa y escenario (el mismo ajuste que hace el pipeline)."""
    ids = [m["id"] for m in meta if m.get("origen") == "motor"]
    out = {}
    for casa, g in K.groupby("casa"):
        if len(g) < 200:      # Kylie Frag: muy pocos casos para ajustar un modelo propio
            continue
        idx = g.index
        P = g.reset_index(drop=True).copy()
        if "Y_orden" not in P:
            P["Y_orden"] = 0
        Xc = X.loc[idx, ids].astype(int).reset_index(drop=True)
        mod = es.ajustar(P, Xc, [dict(id=s, epos=next(m["epos"] for m in meta if m["id"] == s)) for s in ids], pl.CFG)
        out[casa] = {esc: mod[esc]["pts"] for esc in pl.UMBRALES}
    return out


def veredicto(med, partes, q):
    gan = med["prob_tarjeta"] - med["base_tarjeta"]
    d_ok = all(np.sign(p - b) == med["dir"] for p, b, n in partes if n >= 10)
    if gan < 0:
        return "no se cumple"
    if gan >= 0.05 and d_ok and q < 0.10:
        return "se confirma"
    return "débil"


def partes_DT(mask, y, Z, base_mask, corte):
    F = Z.F.to_numpy()
    out = []
    for m in (F < corte, F >= corte):
        mm, bm = mask & m, base_mask & m
        out.append((y[mm].mean() if mm.sum() else np.nan, y[bm].mean() if bm.sum() else np.nan, int(mm.sum())))
    return out


def fila(med, partes, extra):
    return dict(**extra, n=med["n"], casos_independientes=med["n_indep"], codigos=med["codigos"], fotos=med["fotos"],
                probabilidad=round(med["prob"], 3), tasa_base=round(med["base"], 3), lift=round(med["lift"], 2),
                direccion=("pasa" if med["dir"] > 0 else "NO pasa"),
                prob_tarjeta=round(med["prob_tarjeta"], 3), base_tarjeta=round(med["base_tarjeta"], 3),
                prob_prudente=round(med["prob_prudente"], 3),
                estabilidad_fotos=None if np.isnan(med["estab_fotos"]) else round(med["estab_fotos"], 2),
                estabilidad_casas=None if np.isnan(med["estab_casas"]) else round(med["estab_casas"], 2),
                puntuacion=round(med["puntuacion"], 1), clase=med["clase"],
                ganancia_pts=round(med["ganancia"], 1), clase_ganancia=med["clase_ganancia"],
                antiguo=f"{partes[0][0]:.0%} vs {partes[0][1]:.0%} (n={partes[0][2]})",
                reciente=f"{partes[1][0]:.0%} vs {partes[1][1]:.0%} (n={partes[1][2]})",
                por_casa="; ".join(f"{c} {p:.0%} vs {b:.0%} (n={n})" for c, (n, p, b) in med["por_casa"].items()))


def actuales():
    K = pd.read_parquet(CACHE / "casos_K.parquet")
    XK = pd.read_parquet(CACHE / "senales_K.parquet").astype(bool)
    mK = json.loads((CACHE / "senales_K.json").read_text(encoding="utf-8"))
    Y = pd.read_parquet(CACHE / "casos_Y.parquet")
    XY = pd.read_parquet(CACHE / "senales_Y.parquet").astype(bool)
    mY = json.loads((CACHE / "senales_Y.json").read_text(encoding="utf-8"))
    pts = puntos_motor(K, XK, mK)
    filas, pv = [], []
    todo = np.ones(len(K), bool)
    F = K.F.to_numpy()
    # ---- motor
    for m in [m for m in mK if m.get("origen") == "motor"]:
        x = XK[m["id"]].to_numpy()
        dice = {}
        for esc in pl.UMBRALES:
            p = {c: pts[c][esc].get(m["id"], 0) for c in pts}
            if any(p.values()):
                dice[esc] = p
        escs = list(dice) or [max(pl.UMBRALES, key=lambda e: abs(K[f"Y_{e}"][x].mean() - K[f"Y_{e}"].mean()))]
        for esc in escs:
            y = K[f"Y_{esc}"].to_numpy()
            s = sum(dice.get(esc, {}).values())
            dir_ = int(np.sign(s)) if s else None
            med = r3.medir(x, y, K, todo, dir_)
            partes = partes_DT(x, y, K, todo, r3.CORTE["K"])
            lado = med["dir"]
            pval = r3.p_binom(med["prob"] * med["n_indep"], med["n_indep"], med["base"], lado)
            pv.append(float(pval))
            contradice = len({np.sign(v) for v in dice.get(esc, {}).values() if v}) > 1
            dicho = ("sin puntos en el modelo (relación más fuerte)" if esc not in dice else
                     ("puntos de signo distinto según la casa" if contradice else
                      f"{'sube' if dir_ > 0 else 'baja'} la probabilidad de «{pl.NOMBRE_Y[esc]}»"))
            filas.append((med, partes, dict(fuente="motor (escenarios)", id=m["id"], tarjeta=m["txt"],
                                              tabla="K: frente al Consensus", escenario=pl.NOMBRE_Y[esc], lo_que_dice=dicho,
                                              puntos_modelo="; ".join(f"{c} {v:+d}" for c, v in dice.get(esc, {}).items()))))
    # ---- libro (tabla Y, frente a su propio evento)
    sano = (Y.last3_vs_rate >= .6) & (Y.zeros3 == 0)
    r = Y.A3 / Y.base_rob
    ev = {"C": ("CAÍDA: un código hoy sano vende < 0,5× lo esperable en 3 meses", sano & (Y.base_rob >= 30), r < .5),
          "M": ("MUERTE: un código hoy sano vende < 20 % de su ritmo en 6 meses", sano & Y.y6.notna(), Y.y6 < .2 * 6 * Y.mu12),
          "U": ("SUBIDA FUERTE: vende > 1,5× lo esperable en 3 meses", Y.base_rob >= 30, r > 1.5),
          "V": ("MES VACÍO: el mes siguiente vende < 25 % de su media", Y.a1.notna(), Y.a1 < .25 * Y.mu12)}
    for m in [m for m in mY if m.get("origen") == "libro"]:
        nom, pob, yy = ev[m["id"][0]]
        pob = pob.to_numpy()
        y = yy.fillna(False).to_numpy().astype(int)
        x = XY[m["id"]].to_numpy() & pob
        if x.sum() < 10:
            continue
        med = r3.medir(x, y, Y, pob, 1)
        partes = partes_DT(x, y, Y, pob, r3.CORTE["Y_epos" if m["epos"] else "Y"])
        pval = r3.p_binom(med["prob"] * med["n_indep"], med["n_indep"], med["base"], 1)
        pv.append(float(pval))
        filas.append((med, partes, dict(fuente="libro de señales", id=m["id"], tarjeta=m["txt"],
                                          tabla="Y: toda la historia", escenario=nom, lo_que_dice="sube la probabilidad del evento",
                                          puntos_modelo="")))
    q = r3.bh(np.array(pv))
    out = []
    for (med, partes, extra), qq in zip(filas, q):
        f = fila(med, partes, extra)
        f["q"] = round(float(qq), 4)
        f["veredicto"] = veredicto(med, partes, qq)
        out.append(f)
    T = pd.DataFrame(out)
    T.to_csv(SALIDA / "tarjetas_actuales.csv", sep=";", index=False, encoding="utf-8-sig")
    print("tarjetas actuales:", len(T), T.groupby(["fuente", "veredicto"]).size().to_dict())
    return T


# ------------------------------------------------------------------ tarjetas nuevas
def accion(tabla, esc, dir_, ratio):
    ref = "el Consensus" if tabla == "K" else "lo vendido en esos 3 meses del año pasado"
    if dir_ > 0 and esc in ("bajo", "muy_bajo"):
        return f"Bajar el forecast de 3 meses: lo vendido suele quedar en ~{ratio:.2f}× {ref} (mediana)."
    if dir_ > 0:
        return f"Subir el forecast de 3 meses y asegurar supply: lo vendido suele quedar en ~{ratio:.2f}× {ref} (mediana)."
    if esc in ("bajo", "muy_bajo"):
        return f"No recortar: aquí es raro vender por debajo de {ref} (mediana {ratio:.2f}×)."
    return f"No subir: aquí es raro vender por encima de {ref} (mediana {ratio:.2f}×)."


def frase(senal, tipo, grupo, tabla, esc, dir_, prob):
    donde = "" if tipo == "todo" else f"En {grupo} ({tipo.replace('×', ' × ')}), "
    ref = "su Consensus" if tabla == "K" else "esos meses del año pasado"
    s = senal[0].lower() + senal[1:]
    umb = pl.NOMBRE_Y[esc].split(" (")[1].rstrip(")")
    verbo = {"bajo": "venda menos de", "muy_bajo": "venda mucho menos de", "alto": "venda más de", "muy_alto": "venda mucho más de"}[esc]
    if dir_ > 0:
        return f"{donde}si {s}, entonces en 3 meses es probable ({prob:.0%}) que {verbo} {ref} ({umb})."
    return f"{donde}si {s}, entonces en 3 meses es poco probable ({1 - prob:.0%} de que no) que {verbo} {ref} ({umb})."


def nuevas(desc):
    filas = []
    actuales_ids = None
    for tabla in ("K", "Y"):
        ruta = CACHE / f"reglas_{tabla}.parquet"
        if not ruta.exists():
            continue
        R = pd.read_parquet(ruta)
        Z, X, meta = r3.cargar_tabla(tabla)
        origen = {m["id"]: m.get("origen") for m in meta}
        subs = {(t, v): m for t, v, m in r3.subconjuntos(Z)}
        for _, r in R.iterrows():
            # la tarjeta actual tal cual (una señal del motor o del libro, en todas las casas) no es nueva
            es_actual = r.tipo_grupo == "todo" and not r.s2 and origen.get(r.s1) in ("motor", "libro")
            if es_actual:
                continue
            m = subs[(r.tipo_grupo, r.grupo)] & X[r.s1].to_numpy()
            if r.s2:
                m &= X[r.s2].to_numpy()
            ratio = float(Z.ratio[m].median())
            ej = []
            y = Z[f"Y_{r.escenario}"].to_numpy()
            ok = m & ((y == 1) if r.dir > 0 else (y == 0))
            for e, n in Z.ean[ok].value_counts().head(3).items():
                ej.append(f"{e} {desc.get(e, '')} ({n} fotos)")
            filas.append(dict(
                regla=frase(r.senal, r.tipo_grupo, r.grupo, tabla, r.escenario, r.dir, r.prob),
                tabla="K: frente al Consensus" if tabla == "K" else "Y: frente al año pasado",
                escenario=pl.NOMBRE_Y[r.escenario], grupo=("Todas las casas" if r.tipo_grupo == "todo" else f"{r.tipo_grupo}: {r.grupo}"),
                senales=r.s1 + (f" + {r.s2}" if r.s2 else ""), origen_senales=r.origen, usa_epos=r.epos,
                n=r.n, casos_independientes=r.n_indep, codigos=r.codigos, fotos=r.fotos,
                probabilidad=round(r.prob, 3), tasa_base=round(r.base, 3), lift=round(r.lift, 2),
                direccion=("pasa" if r.dir > 0 else "NO pasa"), prob_tarjeta=round(r.prob_tarjeta, 3),
                base_tarjeta=round(r.base_tarjeta, 3), prob_prudente=round(r.prob_prudente, 3),
                estabilidad_fotos=r.estab_fotos, estabilidad_casas=r.estab_casas,
                puntuacion=round(r.puntuacion, 1), clase=r.clase, ganancia_pts=round(r.ganancia, 1), clase_ganancia=r.clase_ganancia,
                antiguo=r.antiguo, reciente=r.reciente, q_descubrimiento=r.q_descubrimiento, p_reciente=r.p_reciente,
                mediana_vendido_vs_ref=round(ratio, 2), accion=accion(tabla, r.escenario, r.dir, ratio),
                explicaciones_que_la_tumban=r.explicaciones_que_la_tumban, ejemplos=" | ".join(ej), por_casa=r.por_casa))
    T = pd.DataFrame(filas)
    if not len(T):
        return T
    T["sobrevive_aburridas"] = T.explicaciones_que_la_tumban.fillna("").eq("")
    T = T.sort_values(["sobrevive_aburridas", "ganancia_pts"], ascending=[False, False])
    T.to_csv(SALIDA / "tarjetas_nuevas_todas.csv", sep=";", index=False, encoding="utf-8-sig")
    prop = T[T.sobrevive_aburridas & (T.clase_ganancia.isin(["A", "B"]) | T.clase.isin(["A", "B"]))]
    prop.to_csv(SALIDA / "tarjetas_nuevas.csv", sep=";", index=False, encoding="utf-8-sig")
    print("tarjetas nuevas: validadas", len(T), "· sobreviven a las explicaciones aburridas", int(T.sobrevive_aburridas.sum()),
          "· propuestas (A/B)", len(prop))
    _ = actuales_ids
    return prop


if __name__ == "__main__":
    d = descripciones()
    actuales()
    nuevas(d)
