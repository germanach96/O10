"""Página HTML de la relevancia de los trends en el estilo de O10 (trends.html, en la raíz del repo).

Uso: python -m scripts.tendencias_03_html   (después de tendencias_01_calculo y tendencias_02_metricas)
Lee resultados/tendencias.json, redacta los hallazgos (en inglés, como la página de O10) con las cifras medidas y lo
incrusta todo en scripts/plantilla_tendencias.html. La página no calcula nada: solo filtra y dibuja.
"""
from __future__ import annotations

import json
import math

from scripts.tendencias_02_metricas import RAIZ, SALIDA as METRICAS

PLANTILLA = RAIZ / "scripts" / "plantilla_tendencias.html"
PAGINA = RAIZ / "trends.html"

NOMBRE = {"si": "Sell-in", "ep": "Sell-out", "cod": "Own code", "pl": "Product line", "brand": "Brand",
          "house": "House"}


def redondear(o):
    if isinstance(o, float):
        return None if math.isnan(o) else round(o, 4)
    if isinstance(o, dict):
        return {k: redondear(v) for k, v in o.items()}
    if isinstance(o, list):
        return [redondear(v) for v in o]
    return o


def p(x, dec=0):
    return f"{x * 100:.{dec}f}%"


def pts(a, b):
    """Diferencia de WAPE en puntos (a − b), con signo explícito."""
    v = (a - b) * 100
    return f"{'−' if v > 0 else '+'}{abs(v):.1f} pts"


def nom(col):
    s, nv, N = col.split("_")
    return f"{NOMBRE[s]} · {NOMBRE[nv].lower()} · {N}M"


def nom_min(col):
    """El nombre dentro de una frase: en minúscula salvo la duración (6M)."""
    s, nv, N = col.split("_")
    return f"{NOMBRE[s].lower()} · {NOMBRE[nv].lower()} · {N}M"


def hallazgos(r):
    m1, m2 = r["m"]["fotos|all|1"], r["m"]["fotos|all|2"]
    d1, d2 = r["duelo"]["fotos|all|1"], r["duelo"]["fotos|all|2"]
    per = r["periodo"]
    out = []

    # 1. EPOS se mantiene, sell-in se pasa
    e, s = m1["ep_cod_3"], m1["si_cod_3"]
    ep_pl, si_pl = m1["ep_pl_3"], m1["si_pl_3"]
    out.append({
        "title": "Sell-out trends carry on. Sell-in trends overshoot.",
        "why": (f"Of every 10 points of a code's 3-month sell-out trend, about {e['beta'] * 10:.0f} show up in the next "
                f"3 months. Of its sell-in trend, only {s['beta'] * 10:.0f}: sell-in is lumpy (one big order moves it), and "
                f"{p(s['cap'])} of code sell-in trends go beyond the ±50% cap, against {p(e['cap'])} for sell-out."),
        "action": "<b>Sell-out can be applied in full.</b> A sell-in trend, at most at half weight.",
        "bars": [["Sell-out · own code · 3M", e["beta"]], ["Sell-out · product line · 3M", ep_pl["beta"]],
                 ["Sell-in · own code · 3M", s["beta"]], ["Sell-in · product line · 3M", si_pl["beta"]]],
        "barsTitle": "Share of the trend that shows up (months 1–3)", "fmt": "pct", "best": 0,
        "note": f"{e['n']:,} cases with sell-out, {s['n']:,} with sell-in · 10 snapshots, 3 houses."})

    # 2. duelo meses 1-3
    cols = [c for c in d1 if c.endswith("_m") and c[:2] in ("si", "ep")]
    best_ep = min((c for c in cols if c.startswith("ep")), key=lambda c: d1[c])
    best_si = min((c for c in cols if c.startswith("si")), key=lambda c: d1[c])
    peor_si = max((c for c in cols if c.startswith("si")), key=lambda c: d1[c])
    out.append({
        "title": f"On the same codes, a sell-out trend takes {abs(d1['w0_m'] - d1[best_ep]) * 100:.0f} points off the WAPE",
        "why": (f"Same {d1['n']:,} cases ({d1['codigos']} codes with sell-out), months 1–3: the 12-month base on its own "
                f"misses by {p(d1['w0_m'], 1)}. Times the best sell-out trend ({nom_min(best_ep[:-2])}) it misses by "
                f"{p(d1[best_ep], 1)}. Times the best sell-in trend it misses by {p(d1[best_si], 1)}, and the worst sell-in "
                f"trend ({nom_min(peor_si[:-2])}) makes it worse: {p(d1[peor_si], 1)}."),
        "action": f"Every sell-out trend beats every sell-in trend on these codes. The Consensus misses by {p(d1['cons'], 1)}.",
        "bars": [["No trend (12M base)", d1["w0_m"]], [nom(best_ep[:-2]), d1[best_ep]], [nom(best_si[:-2]), d1[best_si]],
                 ["Consensus", d1["cons"]]],
        "barsTitle": "WAPE, months 1–3 (lower is better)", "fmt": "pct1", "best": 1, "cons": 3})

    # 3. meses 4-6: le gana al Consensus
    best_ep2 = min((c for c in d2 if c.endswith("_m") and c.startswith("ep")), key=lambda c: d2[c])
    out.append({
        "title": "From month 4, the 12-month base × the sell-out trend beats the Consensus",
        "why": (f"Months 4–6, same {d2['n']:,} cases: the Consensus misses by {p(d2['cons'], 1)}, the plain base by "
                f"{p(d2['w0_m'], 1)} and the base × {nom_min(best_ep2[:-2])} by {p(d2[best_ep2], 1)}. In months 1–3 the "
                f"Consensus still wins ({p(d1['cons'], 1)} against {p(d1[best_ep], 1)}): the near months carry information the "
                f"trend can't see (orders, launches, promotions)."),
        "action": "<b>Beyond month 3, trust the sell-out trend</b> over a Consensus that departs from it.",
        "bars": [["No trend (12M base)", d2["w0_m"]], [nom(best_ep2[:-2]), d2[best_ep2]], ["Consensus", d2["cons"]]],
        "barsTitle": "WAPE, months 4–6 (lower is better)", "fmt": "pct1", "best": 1, "cons": 2})

    # 4. el Consensus no recoge el trend de EPOS
    a, b = m1["ep_cod_3"], m2["ep_cod_3"]
    out.append({
        "title": "The Consensus doesn't take in the sell-out trend",
        "why": (f"When a code's 3-month sell-out trend is up more than 10%, it sold {a['cons_sube']:.2f}× its Consensus in "
                f"months 1–3 and {b['cons_sube']:.2f}× in months 4–6. When it's down more than 10%, {a['cons_baja']:.2f}× and "
                f"{b['cons_baja']:.2f}×. Moving the Consensus halfway towards the trend lowers its WAPE from "
                f"{p(a['w_cons'], 1)} to {p(a['w_cons_mix'], 1)} (months 1–3) and from {p(b['w_cons'], 1)} to "
                f"{p(b['w_cons_mix'], 1)} (months 4–6)."),
        "action": "<b>A Consensus that goes against the sell-out trend</b> is a good candidate for the detector.",
        "bars": [["Trend up · months 1–3", a["cons_sube"]], ["Trend down · months 1–3", a["cons_baja"]],
                 ["Trend up · months 4–6", b["cons_sube"]], ["Trend down · months 4–6", b["cons_baja"]]],
        "barsTitle": "Sold ÷ Consensus (1.00× = on target)", "fmt": "x", "ref1": True})

    # 5. la PL rellena los huecos
    c3, l3 = m1["ep_cod_3"], m1["ep_pl_3"]
    out.append({
        "title": "The product line's sell-out covers the codes without their own",
        "why": (f"A code's own sell-out trend exists in {p(c3['cov'])} of the cases (its retailers must report the month and "
                f"the same month last year). Its product line's exists in {p(l3['cov'])}, and moves the WAPE about the same: "
                f"{pts(c3['w0_m'], c3['w1_m'])} for the code, {pts(l3['w0_m'], l3['w1_m'])} for the line."),
        "action": "<b>Own sell-out when there is one; the line's when there isn't.</b>",
        "bars": [["Own code · coverage", c3["cov"]], ["Product line · coverage", l3["cov"]],
                 ["Brand · coverage", m1["ep_brand_3"]["cov"]]],
        "barsTitle": "Cases with a 3-month sell-out trend (months 1–3)", "fmt": "pct", "best": 1})

    # 6. brand y casa: nivel, no orden
    g, k = r["m"]["fotos|Gucci|1"]["ep_house_3"], r["m"]["fotos|Kylie MU|1"]["ep_house_3"]
    out.append({
        "title": "Brand and house trends set the level, not which code grows",
        "why": (f"Every code of a house gets the same house trend, so it can't tell codes apart (rank correlation "
                f"{m1['ep_house_3']['rho']:.2f}). It only helps when the whole house moves: in Gucci, falling all through "
                f"2025–26, the 3-month sell-out house trend lowers the WAPE by {(g['w0_m'] - g['w1_m']) * 100:.1f} points and "
                f"helps in {round(g['helps_m'] * g['n_origenes'])} of {g['n_origenes']} snapshots; in Kylie MU it changes "
                f"{(k['w0_m'] - k['w1_m']) * 100:+.1f} points and helps in {round(k['helps_m'] * k['n_origenes'])} of "
                f"{k['n_origenes']}."),
        "action": "Use them as a tide on top of the code's own trend, not instead of it.",
        "bars": [["Gucci · house sell-out 3M", g["w0_m"] - g["w1_m"]], ["Kylie MU · house sell-out 3M", k["w0_m"] - k["w1_m"]],
                 ["Gucci · own sell-out 3M", r["m"]["fotos|Gucci|1"]["ep_cod_3"]["w0_m"] - r["m"]["fotos|Gucci|1"]["ep_cod_3"]["w1_m"]],
                 ["Kylie MU · own sell-out 3M", r["m"]["fotos|Kylie MU|1"]["ep_cod_3"]["w0_m"] - r["m"]["fotos|Kylie MU|1"]["ep_cod_3"]["w1_m"]]],
        "barsTitle": "WAPE points gained, months 1–3", "fmt": "pts", "best": -1})

    # 7. duración
    cov = [m1[f"ep_cod_{N}"]["cov"] for N in (3, 6, 9, 12)]
    gan = [m1[f"ep_cod_{N}"]["w0_m"] - m1[f"ep_cod_{N}"]["w1_m"] for N in (3, 6, 9, 12)]
    sw = [m1[f"si_cod_{N}"]["wbest_m"] for N in (3, 6, 9, 12)]
    out.append({
        "title": "3 to 6 months of sell-out are enough. Longer only loses codes",
        "why": (f"A code's sell-out trend of 3, 6, 9 and 12 months gains {', '.join(f'{x * 100:.1f}' for x in gan)} WAPE points, "
                f"but the share of cases where it exists drops from {p(cov[0])} to {p(cov[3])}: sell-out goes back to "
                f"2024.M07, so a 12-month trend needs data from 2024. For sell-in, the best weight is "
                f"{', '.join(p(x) for x in sw)} by duration: never the full trend."),
        "action": "<b>Sell-out: 3 or 6 months.</b> Sell-in: 6 to 12 months, at half weight.",
        "bars": [[f"Own sell-out · {N}M · coverage", c] for N, c in zip((3, 6, 9, 12), cov)],
        "barsTitle": "Cases with a code sell-out trend (months 1–3)", "fmt": "pct", "best": 0})

    # 8. depende del periodo
    pc, pp = per["1|completado"]["m"]["ep_cod_3"], per["1|propio"]["m"]["ep_cod_3"]
    out.append({
        "title": "How much a trend gains depends on the period",
        "why": (f"In the 2025.M09–M12 snapshots (sales falling hard, sell-out filled in from the next snapshot), the code's "
                f"sell-out trend gains {(pc['w0_m'] - pc['w1_m']) * 100:.1f} WAPE points; in 2026.M01–M06, "
                f"{(pp['w0_m'] - pp['w1_m']) * 100:.1f}. It still helps, but a falling market flatters any downward "
                f"trend. Only 10 snapshots are measured, and sell-out trends exist from 2025.M07."),
        "action": "Read the gains as an order of magnitude. Each card shows its snapshots one by one.",
        "bars": [["2025.M09–M12 · no trend", pc["w0_m"]], ["2025.M09–M12 · own sell-out 3M", pc["w1_m"]],
                 ["2026.M01–M06 · no trend", pp["w0_m"]], ["2026.M01–M06 · own sell-out 3M", pp["w1_m"]]],
        "barsTitle": "WAPE, months 1–3", "fmt": "pct1", "best": -1})
    for i, h in enumerate(out, 1):
        h["k"] = i
    return out


def main():
    r = json.loads(METRICAS.read_text(encoding="utf-8"))
    datos = redondear({"meta": r["meta"], "m": r["m"], "duelo": r["duelo"], "hall": hallazgos(r),
                       "version": (RAIZ / "VERSION").read_text(encoding="utf-8").strip()})
    html = PLANTILLA.read_text(encoding="utf-8").replace(
        "/*__DATOS__*/null", json.dumps(datos, ensure_ascii=False, separators=(",", ":")))
    PAGINA.write_text(html, encoding="utf-8")
    print(f"→ {PAGINA.relative_to(RAIZ)} ({len(html) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
