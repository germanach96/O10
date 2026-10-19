"""Página HTML de las tarjetas en el estilo de O10 (signals.html, en la raíz del repo).

Uso: python -m scripts.patrones_08_html   (después de los pasos 02-06)
Lee los CSV de tarjetas, las señales y la validación, traduce los textos al inglés (la página de O10 va en inglés)
y los incrusta en scripts/plantilla_tarjetas.html. La página no calcula nada: solo filtra, ordena y muestra.
"""
from __future__ import annotations

import ast
import json
import re

import pandas as pd

from scripts import patrones_lib as pl

CACHE = pl.RAIZ / "resultados" / "cache"
RES = pl.RAIZ / "resultados"

# textos en inglés de las señales del libro y de las nuevas (las del motor ya vienen en inglés)
EN = {
    "C1": "Erratic (CV ≥ 0.9), small (< 4,000 units a year) and last month under 30% of its average",
    "C2": "Grows 4× faster than its brand and is erratic (CV ≥ 0.9)",
    "C3": "Grows 6× faster than its line while the line falls 40% or more",
    "C4": "Its brand runs a One Shot campaign (≥ 70% of regular sell-in in 3 months) and the size is 150 ml or more",
    "C5": "Very erratic (CV ≥ 1.25) and small (< 4,000 units a year)",
    "M1": "Small, erratic (CV ≥ 1) and its line falls 30% or more",
    "M2": "Rabbit whose EPOS runs 25% or more below its brand's EPOS",
    "M3": "Very erratic (CV ≥ 1.25) with a large order in the last 3 months",
    "M4": "Size 150 ml or more with a large order in the last 2 months",
    "M5": "Small (< 4,000 units a year) and its line falls 30% or more",
    "U1": "3 or more large orders in 12 months and the last 3 months at 1.5× its pace or more",
    "U2": "Irregular (some month at zero) and reactivating: last 3 months ≥ 1.2× its pace, no One Shot campaign in its brand",
    "U3": "Channel filling: sell-through ≤ 0.69× normal with a large order in the last 3 months",
    "U4": "Cuts of 0.6 months of sales or more while its brand's EPOS falls 20% or more",
    "V1": "Last month under 10% of its average with no supply cuts",
    "V2": "Last month under 10% of its average and a negative 12-month trend",
    "V3": "Last month under 10% of its average with cuts above 1 month of sales",
    "N_anom_hi": "Last month is an upward anomaly (over 3 MAD above its 12-month median)",
    "N_anom_lo": "Last month is a downward anomaly (over 3 MAD below its 12-month median)",
    "N_anom_muchas": "3 or more anomalous months (over 3 MAD) in the last year",
    "N_sin_anom": "No anomalous month in the last year (a clean series)",
    "N_pend_up": "12-month slope clearly up (+3% a month or more)",
    "N_pend_dn": "12-month slope clearly down (−3% a month or less)",
    "N_ceros3": "Some month at zero in the last 3",
    "N_st_mejora": "Sell-through improves: over 3 months the retailer sells 20% more of what it buys than over 6",
    "N_st_empeora": "Sell-through worsens: over 3 months the retailer sells 20% less of what it buys than over 6",
    "N_stock3_alto": "Channel loaded over 3 months: over 1 month of sales too much came in",
    "N_stock3_bajo": "Channel emptied over 3 months: over 1 month of sales too little came in",
    "N_ep_ult_lo": "Last month's EPOS under 0.6× its average",
    "N_ep_ult_hi": "Last month's EPOS over 1.4× its average",
    "N_ep_parcial": "Partial EPOS: only 1 to 9 of the last 12 months reported",
    "N_kap_bajo": "Few retailers report: EPOS covers under 30% of sell-in",
    "N_kap_alto": "EPOS covers almost everything: over 80% of sell-in",
    "N_si_up_ep_plano": "Sell-in up (over +15%) with EPOS flat (±5%)",
    "N_si_dn_ep_plano": "Sell-in down (under −15%) with EPOS flat (±5%)",
    "N_lider_linea": "Leader of its line (50% or more of its 12-month sell-in)",
    "N_cola_linea": "Tail of its line (under 5% of its 12-month sell-in)",
    "N_linea_larga": "Its line has 8 or more active codes",
    "N_solo_linea": "The only active code in its line",
    "N_hermano_nuevo": "A sibling (same line and size) launched in the last 6 months",
    "N_corte_reciente": "Supply cut last month",
    "N_corte_viejo": "Cuts 4 to 12 months ago, none in the last 3",
    "N_disco12": "Product discontinuation date in the next 12 months (licence end not counted)",
    "N_k_vs_esp_hi": "The 3-month Consensus is over 1.3× expected (12-month level × its brand's seasonality)",
    "N_k_vs_esp_lo": "The 3-month Consensus is under 0.77× expected (12-month level × its brand's seasonality)",
    "N_k_rev1_up": "The Consensus for these months rose over 15% vs the previous snapshot",
    "N_k_rev1_dn": "The Consensus for these months fell over 15% vs the previous snapshot",
    "N_k_quieto": "Frozen Consensus: within ±3% of 1 and 3 snapshots ago",
    "N_k_quieto_mueve": "Frozen Consensus while 3-month sales drift over 30% from its pace",
    "N_k_paso_bajo": "Last time it was measured (snapshot F−4) it sold under 0.8× its Consensus",
    "N_k_paso_alto": "Last time it was measured (snapshot F−4) it sold over 1.2× its Consensus",
    "N_k_hist_bajo": "On average, in its measured snapshots it sold under 0.8× its Consensus",
    "N_k_hist_alto": "On average, in its measured snapshots it sold over 1.2× its Consensus",
    "N_k_sobre_rev_dn": "The Consensus was cut (−15% vs the previous snapshot) although 3-month sales run above its pace",
    "N_k_sube_ventas_dn": "The Consensus was raised (+15%) although 3-month sales run below its pace",
    "N_k_ep_vs": "The Consensus is over 1.3× its pace while EPOS falls (under −10%)",
    "N_k_sys_bajo": "System FC under 0.6× its pace (the statistical model sees a drop)",
    "N_k_sys_alto": "System FC over 1.5× its pace",
    "N_k_cerca_sys": "Consensus within ±5% of System FC + DA: not adjusted by hand",
}
# textos de las condiciones en las tarjetas: cortos y con los valores explícitos (qué cifra, frente a qué, umbral).
# Vocabulario (glosario de la página): 3M = 3 últimos meses cerrados · LY = mismos meses del año pasado ·
# pace = 12M ÷ 4 · expected = nivel 12M × estacionalidad de la brand · large order = mes ≥ 2× su mediana de 12M ·
# anomalous = mes a más de 3 MAD de su mediana · CV = variación mes a mes · «20 pts» = crecimiento 1,2× mayor
CLARO = {
    "K_3m_lo": "Consensus next 3M < 0.67 × sell-in last 3M", "K_3m_hi": "Consensus next 3M > 1.5 × sell-in last 3M",
    "K_ritmo_lo": "Consensus next 3M < 0.67 × pace", "K_ritmo_LO": "Consensus next 3M < 0.4 × pace",
    "K_ritmo_hi": "Consensus next 3M > 1.5 × pace", "K_ritmo_HI": "Consensus next 3M > 2.5 × pace",
    "K_rev_dn": "Consensus next 3M < 0.7 × the same months 3 snapshots ago",
    "N_k_rev1_dn": "Consensus next 3M < 0.85 × the previous snapshot",
    "K_tardio": "Consensus months 7–9 > 2 × months 1–3", "K_frontal": "Consensus months 7–9 < 0.5 × months 1–3",
    "K_ly_hi": "Consensus next 3M > 1.5 × sell-in LY", "K_ly_lo": "Consensus next 3M < 0.67 × sell-in LY",
    "K_ep_lo": "Growth in the Consensus vs LY 20 pts below EPOS 3M vs LY",
    "K_ep_hi": "Growth in the Consensus vs LY 50 pts above EPOS 3M vs LY",
    "K_si_lo": "Growth in the Consensus vs LY 20 pts below sell-in 3M vs LY",
    "K_si_hi": "Growth in the Consensus vs LY 50 pts above sell-in 3M vs LY",
    "N_k_vs_esp_lo": "Consensus next 3M < 0.77 × expected", "N_k_vs_esp_hi": "Consensus next 3M > 1.3 × expected",
    "N_k_sys_alto": "System FC next 3M > 1.5 × pace", "N_k_sys_bajo": "System FC next 3M < 0.6 × pace",
    "K_man_dn": "Consensus next 3M < 0.8 × (System FC + DA)", "N_k_cerca_sys": "Consensus next 3M = System FC + DA (±5%)",
    "K_pico_plan": "Some Consensus month in the next 3M ≥ 2 × the 12M median",
    "K_ultimo_cero": "Last month < 0.15 × 12M average · Consensus next 3M > 0.8 × pace",
    "N_k_sobre_rev_dn": "Consensus next 3M cut > 15% vs the previous snapshot · sell-in last 3M > pace",
    "N_k_sube_ventas_dn": "Consensus next 3M raised > 15% vs the previous snapshot · sell-in last 3M < pace",
    "N_k_ep_vs": "Consensus next 3M > 1.3 × pace · EPOS 3M vs LY < −10%",
    "N_k_paso_alto": "Snapshot of 4 months ago: sold > 1.2 × its Consensus",
    "SI_up3": "Sell-in 3M vs LY > +10%", "SI_UP3": "Sell-in 3M vs LY > +30%", "SI_dn12": "Sell-in 12M vs the 12M before < −10%",
    "SI_3m_hi": "Sell-in last 3M > 1.3 × pace", "SI_3m_lo": "Sell-in last 3M < 0.6 × pace",
    "SI_last_hi": "Sell-in last month > 1.5 × 12M average", "SI_last_lo": "Sell-in last month < 0.3 × 12M average",
    "SI_max": "Sell-in last 3M ≥ 90% of its best 3M in 12M", "SI_suelo": "Sell-in last 3M < 25% of its best 3M in 12M",
    "SI_racha_dn": "0 of the last 6 months above LY", "SI_racha_up": "5 or 6 of the last 6 months above LY",
    "SI_giro_up": "Sell-in vs LY: 12M < −10% · 3M > +10%",
    "SI_acel": "Sell-in vs LY: 3M growth 20 pts above 12M growth", "SI_frena": "Sell-in vs LY: 3M growth 20 pts below 12M growth",
    "N_pend_up": "Sell-in 12M trend ≥ +3% a month", "N_pend_dn": "Sell-in 12M trend ≤ −3% a month",
    "N_ceros3": "A month at 0 in the last 3M", "C_ceros": "2+ months at 0 in the last 12M",
    "N_sin_anom": "No anomalous month in the last 12M", "N_anom_muchas": "3+ anomalous months in the last 12M",
    "C_errático": "CV ≥ 1", "C_regular": "CV < 0.5",
    "C_big_reciente": "Large order in the last 2 months", "C_big_lejos": "Last large order 9–12 months ago",
    "C_sin_big": "No large order in the last 12M", "C_muchos_big": "3+ large orders in the last 12M",
    "C_ly_big3": "Large order in the same 3 months LY", "C_ly_pico": "Sell-in of the same 3 months LY > 1.3 × pace",
    "C_ly_valle": "Sell-in of the same 3 months LY < 0.7 × pace", "C_post_navidad": "Next 3M start in January or February",
    "EP_up3": "EPOS 3M vs LY > +10%", "EP_DN3": "EPOS 3M vs LY < −30%",
    "EP_last_lo": "EPOS last 3M < 0.7 × its 12M average", "N_ep_ult_lo": "EPOS last month < 0.6 × its 12M average",
    "N_ep_parcial": "EPOS reported in only 1–9 of the last 12 months", "N_kap_alto": "EPOS 12M > 80% of sell-in 12M",
    "X_ambos_DN": "Sell-in 3M vs LY < −30% · EPOS 3M vs LY < −30%",
    "X_si_up_ep_dn": "Sell-in 3M vs LY > +10% · EPOS 3M vs LY < −10%",
    "X_div_pos": "Sell-in 3M vs LY 30 pts above EPOS 3M vs LY", "X_div_neg": "Sell-in 3M vs LY 30 pts below EPOS 3M vs LY",
    "X_stock_alto": "Sell-in − EPOS over the last 6M > 1 month of sales",
    "X_stock_bajo": "EPOS − sell-in over the last 6M > 1 month of sales",
    "N_stock3_alto": "Sell-in − EPOS over the last 3M > 1 month of sales",
    "N_stock3_bajo": "EPOS − sell-in over the last 3M > 1 month of sales",
    "X_st_alto": "EPOS ÷ sell-in last 3M > 1.3 × its 12M ratio", "X_st_bajo": "EPOS ÷ sell-in last 3M < 0.7 × its 12M ratio",
    "N_st_empeora": "EPOS ÷ sell-in last 3M < 0.8 × last 6M",
    "G_brand_up": "Brand sell-in 3M vs LY > +10%", "G_brand_dn": "Brand sell-in 3M vs LY < −10%",
    "G_brand_DN": "Brand sell-in 3M vs LY < −30%", "G_linea_DN": "Line sell-in 3M vs LY < −30%",
    "G_casa_up": "House sell-in 3M vs LY > +10%", "G_brand_ep_dn": "Brand EPOS 3M vs LY < −10%",
    "G_brand_destock": "Brand sell-in 3M vs LY 20 pts below brand EPOS 3M vs LY",
    "G_rs_brand_lo": "Sell-in 3M vs LY < 0.5 × its brand's", "G_rs_brand_hi": "Sell-in 3M vs LY > 2 × its brand's",
    "G_rs_linea_lo": "Sell-in 3M vs LY < 0.5 × its line's", "G_rs_linea_hi": "Sell-in 3M vs LY > 2 × its line's",
    "G_rezagado": "Sell-in 3M vs LY < −10% · brand > +10%", "G_contra_linea": "Sell-in 3M vs LY > +10% · line < −10%",
    "G_contra_brand": "Sell-in 3M vs LY > +10% · brand < −10%",
    "G_cuota_up": "Share of its line: last 3M > 1.2 × last 12M", "G_cuota_dn": "Share of its line: last 3M < 0.8 × last 12M",
    "G_ep_brand_hi": "EPOS 3M vs LY 20 pts above its brand's EPOS",
    "O_cortes": "Supply cuts last 3M > 0.5 months of sales", "O_cortes_altos": "Supply cuts last 3M > 2 months of sales",
    "N_corte_reciente": "Supply cut last month", "N_corte_viejo": "Supply cuts 4–12 months ago, none in the last 3M",
    "O_pequeño": "Sell-in 12M < 4,000 units", "O_joven": "13–24 months since its first sale",
    "O_seg_Horses": "Segment: Horses", "O_seg_Rabbits": "Segment: Rabbits",
    "O_os_crece": "Brand One Shots 3M > 2 × LY", "O_os_campaña": "Brand One Shots 3M ≥ 50% of its regulars",
    "N_disco12": "Product discontinuation date in the next 12M", "N_linea_larga": "Its line has 8+ active codes",
    "N_cola_linea": "Its share of the line's 12M sell-in < 5%", "N_hermano_nuevo": "Sibling (same line and size) launched in the last 6M",
    "C1": "CV ≥ 0.9 · sell-in 12M < 4,000 units · last month < 0.3 × 12M average",
    "C5": "CV ≥ 1.25 · sell-in 12M < 4,000 units",
    "M1": "Sell-in 12M < 4,000 units · CV ≥ 1 · line 3M vs LY < −30%", "M5": "Sell-in 12M < 4,000 units · line 3M vs LY < −30%",
    "M2": "Rabbit · EPOS 3M vs LY 25 pts below its brand's EPOS",
    "U1": "3+ large orders in the last 12M · sell-in last 3M ≥ 1.5 × pace",
    "U2": "A month at 0 in the last 12M · sell-in last 3M ≥ 1.2 × pace · no brand One Shots",
    "V1": "Last month < 0.1 × 12M average · no supply cuts",
    "V2": "Last month < 0.1 × 12M average · sell-in 12M trend down",
}
GRUPO_EN = {"casa": "House", "brand": "Brand", "linea": "Line", "tamano": "Size", "seg": "Segment", "tramo_edad": "Age",
            "tramo_vol": "Volume", "lista": "List"}
VALOR_EN = {"13-24 meses": "13–24 months", "25-36 meses": "25–36 months", "37+ meses": "37+ months", "Pre-disco": "Pre-disco",
            "vol bajo": "low volume", "vol medio": "mid volume", "vol alto": "high volume", "Todas las casas": "All houses"}
ESC_ES = {v: k for k, v in pl.NOMBRE_Y.items()}
EVENTO = {"C": ("drop", "Drop", "A healthy code sells under 0.5× expected in 3 months"),
          "M": ("death", "Death", "A healthy code sells under 20% of its pace in 6 months"),
          "U": ("rise", "Strong rise", "Sells over 1.5× expected in 3 months"),
          "V": ("empty", "Empty month", "Next month sells under 25% of its average")}
VEREDICTO = {"se confirma": "confirmed", "débil": "weak", "no se cumple": "contradicted"}


def textos_senal():
    t = {}
    for tabla in ("K", "Y"):
        for m in json.loads((CACHE / f"senales_{tabla}.json").read_text(encoding="utf-8")):
            t[m["id"]] = CLARO.get(m["id"], EN.get(m["id"], m["txt"]))
    return t


def grupo_en(tipo, valor):
    if tipo in ("todo", "Todas las casas") or valor == "Todas las casas":
        return ""
    tipos = tipo.split("×")
    vals = [v.strip() for v in valor.split(" × ")]
    if len(tipos) != len(vals):
        return valor
    return " · ".join(VALOR_EN.get(v, v) for v in vals)


def partes(s):
    """«79% vs 36% (n=53)» -> [0.79, 0.36, 53]."""
    m = re.match(r"\s*(nan|[\d.]+)%? vs (nan|[\d.]+)% \(n=(\d+)\)", str(s))
    if not m:
        return None
    a = None if m.group(1) == "nan" else float(m.group(1)) / 100
    return [a, float(m.group(2)) / 100, int(m.group(3))]


def casas(s):
    """«Gucci 55% vs 26% (n=67); …» o el dict {'Gucci': (n, p, base)} de las tarjetas nuevas -> [[casa, n, p, base]]."""
    if str(s).startswith("{"):
        d = ast.literal_eval(str(s))
        return [[k, int(v[0]), float(v[1]), float(v[2])] for k, v in d.items()]
    out = []
    for trozo in str(s).split("; "):
        m = re.match(r"(.+?) (nan|[\d.]+)% vs ([\d.]+)% \(n=(\d+)\)", trozo)
        if m:
            out.append([m.group(1), int(m.group(4)), None if m.group(2) == "nan" else float(m.group(2)) / 100, float(m.group(3)) / 100])
    return out


def ejemplos(s):
    out = []
    for e in str(s).split(" | "):
        m = re.match(r"(\d{8,14}) (.*) \((\d+) fotos\)", e.strip())
        if m:
            out.append([m.group(1), m.group(2).strip(), int(m.group(3))])
    return out


def accion(ref, esc, dir_, ratio):
    r = "the Consensus" if ref == "K" else "the same 3 months last year"
    if dir_ > 0 and esc in ("bajo", "muy_bajo"):
        return f"Lower the 3-month forecast: sales tend to land at about {ratio:.2f}× {r} (median)."
    if dir_ > 0:
        return f"Raise the 3-month forecast and secure supply: sales tend to land at about {ratio:.2f}× {r} (median)."
    if esc in ("bajo", "muy_bajo"):
        return f"Don't cut: selling below {r} is rare here (median {ratio:.2f}×)."
    return f"Don't raise: selling above {r} is rare here (median {ratio:.2f}×)."


def num(x, nd=3):
    return None if pd.isna(x) else round(float(x), nd)


def nuevas(T):
    df = pd.read_csv(RES / "tarjetas_nuevas.csv", sep=";", dtype={"ejemplos": str})
    out = []
    for i, r in df.reset_index(drop=True).iterrows():
        tipo, valor = r.grupo.split(": ", 1) if ": " in r.grupo else ("todo", r.grupo)
        s = [x.strip() for x in str(r.senales).split(" + ")]
        ref = "K" if r.tabla.startswith("K") else "Y"
        esc = ESC_ES[r.escenario]
        dir_ = 1 if r.direccion == "pasa" else -1
        if dir_ < 0:   # solo tarjetas de «va a pasar»: las de «no va a pasar» no cambian ninguna decisión
            continue
        out.append(dict(id=f"n{i}", coll="new", ref=ref, esc=esc, dir=dir_, sig=s, cond=[T[x] for x in s],
                        group=grupo_en(tipo, valor), gtype=GRUPO_EN.get(tipo.split("×")[0], ""),
                        origin=r.origen_senales, epos=bool(r.usa_epos), n=int(r.n), ind=int(r.casos_independientes),
                        cod=int(r.codigos), fotos=int(r.fotos), p=num(r.probabilidad), b=num(r.tasa_base), lift=num(r.lift, 2),
                        pc=num(r.prob_tarjeta), bc=num(r.base_tarjeta), lo=num(r.prob_prudente), estF=num(r.estabilidad_fotos, 2),
                        estC=num(r.estabilidad_casas, 2), score=num(r.puntuacion, 1), cls=r.clase, gain=num(r.ganancia_pts, 1),
                        clsG=r.clase_ganancia, old=partes(r.antiguo), rec=partes(r.reciente), houses=casas(r.por_casa),
                        ratio=num(r.mediana_vendido_vs_ref, 2), action=accion(ref, esc, dir_, r.mediana_vendido_vs_ref),
                        ex=ejemplos(r.ejemplos), q=num(r.q_descubrimiento, 4)))
    return out


# tarjetas de antes que siguen en clase A (por ganancia): entran como una tarjeta más, sin distinguir su origen
EVENTO_ESC = {"drop": ("muy_bajo", "vs expected"), "death": ("muy_bajo", "vs its pace"), "rise": ("muy_alto", "vs expected"),
              "empty": ("muy_bajo", "next month vs its average")}
ACCION_EVENTO = {"drop": "Lower the 3-month forecast to about half of expected (12-month level × brand seasonality).",
                 "death": "Don't replenish: plan the phase-out and move the volume to a healthy sibling.",
                 "rise": "Raise the 3-month forecast and secure supply.",
                 "empty": "Plan next month close to zero: with no supply cuts, it is demand, not supply."}


def aburrida_vieja(sid, esc):
    """Las mismas explicaciones aburridas que a las tarjetas nuevas: si alguna la tumba, la tarjeta no entra."""
    import numpy as np
    from scripts import patrones_03_reglas as r3
    if esc:   # tarjeta del motor, frente al Consensus
        K, XK, _ = r3.cargar_tabla("K")
        return bool(r3.aburridas(XK[sid].to_numpy(), K[f"Y_{esc}"].to_numpy(), K, np.ones(len(K), bool), 1, "K"))
    Y = pd.read_parquet(CACHE / "casos_Y.parquet")
    XY = pd.read_parquet(CACHE / "senales_Y.parquet").astype(bool)
    sano = (Y.last3_vs_rate >= .6) & (Y.zeros3 == 0)
    r = Y.A3 / Y.base_rob
    ev = {"C": (sano & (Y.base_rob >= 30), r < .5), "M": (sano & Y.y6.notna(), Y.y6 < .2 * 6 * Y.mu12),
          "U": (Y.base_rob >= 30, r > 1.5), "V": (Y.a1.notna(), Y.a1 < .25 * Y.mu12)}
    pob, y = ev[sid[0]]
    pob = pob.to_numpy()
    return bool(r3.aburridas(XY[sid].to_numpy() & pob, y.fillna(False).to_numpy().astype(int), Y, pob, 1, "Y"))


def viejas_a(T):
    df = pd.read_csv(RES / "tarjetas_actuales.csv", sep=";")
    df = df[df.clase_ganancia == "A"].copy()
    df["esc"] = [None if f.startswith("libro") else ESC_ES[e] for f, e in zip(df.fuente, df.escenario)]
    # misma señal en «más» y «mucho más» (o «menos» y «mucho menos»): queda la extrema si gana casi lo mismo
    pares = {"alto": "muy_alto", "bajo": "muy_bajo"}
    quitar = set()
    for i, r in df[df.esc.isin(pares)].iterrows():
        j = df[(df.id == r.id) & (df.esc == pares[r.esc])]
        if len(j):
            quitar.add(i if j.ganancia_pts.iloc[0] >= r.ganancia_pts - 5 else j.index[0])
    df = df.drop(index=list(quitar))
    df = df[[not aburrida_vieja(r.id, r.esc if isinstance(r.esc, str) else None) for r in df.itertuples()]]
    out = []
    for i, r in df.reset_index(drop=True).iterrows():
        libro = r.fuente.startswith("libro")
        if libro:
            esc = EVENTO[r.id[0]][0]
            escF, refTxt = EVENTO_ESC[esc]
            ref, dir_, action = "Y", 1, ACCION_EVENTO[esc]
        else:
            esc = escF = r.esc
            refTxt, ref = None, "K"
            dir_ = 1 if r.direccion == "pasa" else -1
            if dir_ < 0:
                continue
            v = {"bajo": "under 0.8×", "muy_bajo": "under half", "alto": "over 1.2×", "muy_alto": "over 1.5×"}[esc]
            action = (f"{'Lower' if esc in ('bajo', 'muy_bajo') else 'Raise'} the 3-month forecast: "
                      f"{r.probabilidad:.0%} of these codes sold {v} their Consensus.")
        out.append(dict(id=f"v{i}", coll="new", ref=ref, refTxt=refTxt, esc=esc, escF=escF, dir=dir_,
                        sig=[r.id], cond=[T.get(r.id, r.tarjeta)], group="", action=action,
                        n=int(r.n), ind=int(r.casos_independientes), cod=int(r.codigos),
                        fotos=int(r.fotos), p=num(r.probabilidad), b=num(r.tasa_base), lift=num(r.lift, 2), pc=num(r.prob_tarjeta),
                        bc=num(r.base_tarjeta), lo=num(r.prob_prudente), estF=num(r.estabilidad_fotos, 2),
                        estC=num(r.estabilidad_casas, 2), score=num(r.puntuacion, 1), cls=r.clase, gain=num(r.ganancia_pts, 1),
                        clsG=r.clase_ganancia, old=partes(r.antiguo), rec=partes(r.reciente), houses=casas(r.por_casa),
                        q=num(r.q, 4)))
    return out


# los 10 hallazgos del informe: textos en inglés y, cuando es una tarjeta, el candidato validado
HALLAZGOS = [
    dict(k=1, kind="metric", title="The code's own EPOS predicts sell-in better than sell-in itself",
         why="EPOS is incomplete (not every retailer reports), so it is usually kept as a cross-check. Direction does not need completeness: 3-month sell-in carries order noise and EPOS does not. The sell-in trend often makes the forecast worse than no trend at all.",
         action="Compass 2: try mix m = 100% sell-out with the Own group (only the 3-month trend could be measured; EPOS starts in 2024.M07).",
         bars=[["No trend", .611], ["Sell-in trend", .588], ["EPOS trend", .540]], metric="WAPE, next 3 months",
         note="Gucci 48 → 45 → 39% · Kylie MU 67 → 65 → 62% · 90% interval of the gain −6.2 to −3.3 points · 2,402 cases"),
    dict(k=2, kind="card", cand="recorte_excesivo_doble", title="Cutting the Consensus while the code sells above its pace backfires",
         why="The cut looks prudent, but sales gave no reason for it: the near term is then under-forecast by about 2×.",
         action="Flag “Consensus cut with sales above pace”. Undo the cut or at least go back to the 12-month pace.",
         ex=[["4064941155874", "KJ MU PLMP LIN LINPEN 1.1G 808 KYLIE", "2.3×"], ["4064941078128", "KJ MU PLMP GLS 818BUB", "5.8×"], ["3616301976134", "GG PF21 EDT NS 30 ML", "1.9×"]]),
    dict(k=3, kind="card", cand="consensus_sube_epos_cae", title="Consensus above its pace while EPOS falls: half sell under half the Consensus",
         why="The recovery plan leans on sell-in or the commercial plan while the shopper is already going down. EPOS warns first.",
         action="Alarm in the detector. Without a concrete reason (launch, signed promo), cap the 3-month Consensus at the 12-month pace.",
         ex=[["4064941033622", "KJ MU LSE PWD FACE ML 5G 200ST", "0.08×"], ["4064941007197", "KJ MU M LIQ LIQLPK 500KRISTEN", "0.20×"], ["4064941049227", "KJ MU CCLER PWR PLUSH 6.5N", "0.03×"]]),
    dict(k=4, kind="metric", title="Gucci: averaging the Consensus with an EPOS recipe beats the Consensus alone",
         why="The EPOS recipe alone does not beat the Consensus (38% vs 40%), but they miss in different places, so their average is better than either.",
         action="In Gucci, use “last year × (1 + EPOS trend)” as a second opinion; where it differs a lot, split the difference or review the code. Not in Kylie MU, where the Consensus alone is better.",
         bars=[["Consensus", .402], ["EPOS recipe", .379], ["Half and half", .334]], metric="WAPE90, Gucci",
         note="90% interval of the gain −11.4 to −1.1 points · better in 7 of 9 snapshots; the edge narrowed in 2026 (0–6 points)"),
    dict(k=5, kind="card", cand="canal_cargado_crece", title="A loaded channel is not a slowdown against last year",
         why="“Loaded channel = destocking ahead” is the usual reading; loading signals growth (more doors). What does correct is the loading quarter itself: in Kylie MU, after buying 35% more than it sold, next quarter's sell-in drops 32% vs the last one. In Gucci the gap is seasonal pre-loading and adds nothing.",
         action="Don't cut against last year a code that is loading; plan the next quarter with the EPOS pace, not the loading quarter's sell-in (make-up).",
         ex=[["4064941049128", "KJ MU CCLER PWR PLUSH 5N", "2.7×"], ["4064941049043", "KJ MU CCLER PWR PLUSH 4W", "4.4×"], ["4064941049005", "KJ MU CCLER PWR PLUSH 3C", "2.0×"]]),
    dict(k=6, kind="card", cand="serie_anomala", title="Jumpy series: the Consensus over-forecasts",
         why="The Consensus seems built on averages inflated by spikes; in these codes the planned spike does not come. Extreme case: small, very erratic 3-year-old codes with a planned large-order month sell under half 95% of the time (16 codes).",
         action="In jumpy codes plan on the median, not the mean; don't plan spikes in small erratic codes.",
         ex=[["3616303470845", "GUCCI FL G MAG RG EDP 150 ML JUMBO", "0.08×"], ["4064941130697", "KJ MU SPP GLZ 002LIKE MAGIC", "0.27×"]]),
    dict(k=7, kind="card", cand="bajo_lo_esperable", title="A plain baseline is a good guard-rail for the Consensus",
         why="With everything the planner knows, the Consensus should beat “12-month level × brand seasonality”. When it strays far from it, the plain baseline tends to be right. In Gucci, above 1.3× expected, 63% sell under 0.8× (base 47%).",
         action="Flag every Consensus outside 0.77–1.3× expected.",
         ex=[["4064941139454", "KJ MU POUT LIN PEN 356SUL", "2.1×"], ["3616304249716", "GUCCI BM EDPIN EDP 100 ML", "0.45× (above)"]]),
    dict(k=8, kind="card", cand="aplazado", title="Deferred Consensus: pushing volume to months 7–9 leaves months 1–3 short",
         why="Holds in every house and is stronger in Kylie MU: with a rising 12-month slope, 85% sell over 1.5× (26% without the signal).",
         action="Don't defer volume without a concrete supply reason; plan the near term at pace.",
         ex=[["4064941049104", "KJ MU CCLER PWR PLUSH 4.5C", "4.1×"], ["4064941155874", "KJ MU PLMP LIN 808 KYLIE", "2.8×"]]),
    dict(k=9, kind="card", cand="cortes_consensus_bajo_gucci", title="Gucci: after cuts, keep the Consensus at least at last year",
         why="Cuts come back as orders (≈ 40% per unit cut); what is new is that the Consensus also cuts the plan after the cut, and that is when it misses most. Only 12 recent cases: re-measure.",
         action="After a supply cut, keep the Consensus at least at last year's level.",
         ex=[["3614227912274", "GUCCI GUILT H EDT 200ML", "6.7×"], ["3616302514274", "GUCCI BM EDT 30 ML", "2.3×"], ["3614227758063", "GUCCI G PF EDP 30 ML", "2.0×"]]),
    dict(k=10, kind="card", cand="epos_ultimo_mes_cae", title="Kylie MU: one bad month of EPOS already warns",
         why="One month usually looks like noise, but in EPOS (no orders in between) a bad month is already information. Weaker in recent snapshots (54% vs 38%).",
         action="Quick review of the code's Consensus when its last-month EPOS falls under 0.6× its average.",
         ex=[["4064941008514", "KJ MU PWD BL 335BDNBLK", "0.11×"], ["4064941011163", "KJ MU HIGH GLS ALWSHN002", "0.55×"]]),
]


def hallazgos(T):
    V = {c["id"]: c for c in json.loads((CACHE / "validacion.json").read_text(encoding="utf-8"))["candidatos"]}
    out = []
    for h in HALLAZGOS:
        d = dict(id=f"f{h['k']}", coll="finding", k=h["k"], kind=h["kind"], title=h["title"], why=h["why"], action=h["action"])
        if h["kind"] == "metric":
            d.update(bars=h["bars"], metric=h["metric"], note=h["note"])
        else:
            c = V[h["cand"]]
            m = c["medidas"]
            g = c["grupo"]
            d.update(ref=c["tabla"], esc=c["escenario"], dir=c["dir"], sig=c["senales"], cond=[T[s] for s in c["senales"]],
                     group="" if not g else VALOR_EN.get(g[1], g[1]), n=m["n"], ind=m["n_indep"], cod=m["codigos"],
                     fotos=m["fotos"], p=round(m["prob"], 3), b=round(m["base"], 3), lift=round(m["lift"], 2),
                     pc=round(m["prob_tarjeta"], 3), bc=round(m["base_tarjeta"], 3), lo=round(m["prob_prudente"], 3),
                     estF=m["estab_fotos"], estC=m["estab_casas"], score=round(m["puntuacion"], 1), cls=m["clase"],
                     gain=round(m["ganancia"], 1), clsG=m["clase_ganancia"],
                     old=[c["partes"]["antiguo"]["p"], c["partes"]["antiguo"]["base"], c["partes"]["antiguo"]["n"]],
                     rec=[c["partes"]["reciente"]["p"], c["partes"]["reciente"]["base"], c["partes"]["reciente"]["n"]],
                     houses=[[k, v[0], v[1], v[2]] for k, v in c["por_casa"].items()],
                     units=[round(c["unidades"]["con_senal"], 2), round(c["unidades"]["sin_senal"], 2)],
                     big=[c["volumen_grande"]["p"], c["volumen_grande"]["base"], c["volumen_grande"]["n"]],
                     perm=c["p_permutacion"], ratio=round(c["mediana_ratio"], 2), exf=h["ex"])
        out.append(d)
    return out


def main():
    T = textos_senal()
    datos = dict(version=(pl.RAIZ / "VERSION").read_text().strip(), through="2026.M10",
                 meta=dict(tested=635396, survived=637, casesK=2528, casesY=5346, photosK="2025.M09–2026.M06"),
                 cards=hallazgos(T) + nuevas(T) + viejas_a(T))
    plantilla = (pl.RAIZ / "scripts" / "plantilla_tarjetas.html").read_text(encoding="utf-8")
    js = json.dumps(datos, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    salida = pl.RAIZ / "signals.html"
    salida.write_text(plantilla.replace("/*__DATOS__*/null", js), encoding="utf-8")
    print(salida, f"{salida.stat().st_size / 1024:.0f} KB", len(datos["cards"]), "tarjetas")


if __name__ == "__main__":
    main()
