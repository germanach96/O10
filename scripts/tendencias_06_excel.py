"""Excel con todos los datos del Trend analysis (después de tendencias_04_matriz y tendencias_05_fiabilidad).

Uso: python -m scripts.tendencias_06_excel   → resultados/trend_analysis.xlsx

Hojas (en inglés, como las páginas):
- Read me: qué es cada medida y de dónde sale.
- Reliability: una fila por casa × trend × duración × plazo, con la mediana de las fotos, su rango y la cifra de todas
  las fotos juntas (fórmula sobre la hoja By snapshot).
- By snapshot: una fila por foto, con las sumas en unidades; la fiabilidad y el bias de cada foto son fórmulas.
- Matrix: la matriz de trend_matrix.html (trend × forma de aplicarlo × plazo) y sus referencias (sin trend, Consensus).
"""
from __future__ import annotations

import json

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from scripts.tendencias_01_calculo import RAIZ

SALIDA = RAIZ / "resultados" / "trend_analysis.xlsx"
FIAB = RAIZ / "resultados" / "cache" / "tendencias_fiabilidad.json"
MATRIZ = RAIZ / "resultados" / "cache" / "tendencias_matriz.json"

SENAL = {"ep": "Sell-out (EPOS)", "si": "Sell-in"}
NIVEL = {"cod": "EAN", "pl": "PL", "brand": "Brand", "house": "House", "cas": "Cascade"}
HORIZ = {"3": ("3M", "months 1–3"), "6": ("6M", "months 1–6"), "9": ("9M", "months 1–9"), "12": ("12M", "months 1–12"),
         "12h": ("12M (long history)", "months 1–12, every month of the latest file as a starting point")}
APLICA = {"full": "Common base × full trend", "half": "Common base × half trend",
          "time": "Common base × trend over time", "ly": "Last year × full trend"}
CASA = lambda c: "All houses" if c == "all" else c

FUENTE = "Arial"
F_NORMAL = Font(name=FUENTE, size=10)
F_CAB = Font(name=FUENTE, size=10, bold=True, color="FFFFFF")
F_TIT = Font(name=FUENTE, size=14, bold=True)
F_NEG = Font(name=FUENTE, size=10, bold=True)
RELLENO_CAB = PatternFill("solid", fgColor="1F2A44")
BORDE = Border(bottom=Side(style="thin", color="D0D4DA"))
PCT, PCT1, PTS, ENT = "0%", "0.0%", '+0.0;-0.0;0.0', "#,##0"


def hoja_tabla(ws, cabeceras, anchos):
    ws.append(cabeceras)
    for i, (c, w) in enumerate(zip(cabeceras, anchos), 1):
        celda = ws.cell(row=1, column=i)
        celda.font, celda.fill = F_CAB, RELLENO_CAB
        celda.alignment = Alignment(wrap_text=True, vertical="center")
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 32
    ws.freeze_panes = "A2"


def formatear(ws, formatos):
    """Fuente, borde y formato numérico de las columnas (formatos: {columna: formato})."""
    for fila in ws.iter_rows(min_row=2):
        for c in fila:
            c.font, c.border = F_NORMAL, BORDE
            f = formatos.get(c.column)
            if f:
                c.number_format = f
    ws.auto_filter.ref = ws.dimensions


def partes(clave):
    s, nv = clave.split("_", 1)
    return SENAL[s], NIVEL[nv]


def main():
    fi = json.loads(FIAB.read_text(encoding="utf-8"))
    mx = json.loads(MATRIZ.read_text(encoding="utf-8"))
    wb = Workbook()

    # ------------------------------------------------------------ Read me
    ws = wb.active
    ws.title = "Read me"
    filas = [
        ("Trend analysis", ""),
        ("Scope", "Regular items only (One Shots are out of the cases and out of every group sum). Houses: "
                  + ", ".join(fi["casas"]) + "."),
        ("Trend", "Sold over the last N closed months (6M or 12M) against the same months a year earlier. Sell-in = "
                  "Actuals (empty = 0). Sell-out = EPOS, 0 or empty = no data, paired code by code (a month counts only "
                  "with EPOS > 0 that month and 12 months before). Levels: the code (EAN), its product line (PL), its "
                  "brand, its house; Cascade = the EAN's sell-out, else its PL's, else its brand's, else its house's. "
                  "Trend capped at ±50%."),
        ("Horizon", "Months counted from the snapshot, cumulative: 3M = months 1–3 (WAPE90), 6M = 1–6, 9M = 1–9, "
                    "12M = 1–12. Only snapshots whose months have all closed."),
        ("Moved", "Sold − same months last year, in units, per code."),
        ("Anticipated", "Last year × trend, in units, per code."),
        ("Reliability (like WAPE)", "1 − Σ|moved − anticipated| ÷ Σ|moved|. 100% = the trend saw all of the movement; "
                                    "0% = same as assuming no change; below 0 = it misleads. In units, so big codes "
                                    "weigh more."),
        ("Bias (pts, like SPP)", "Σ sign(trend) × (moved − anticipated) ÷ Σ last year, in growth points. Positive = "
                                 "reality went further than the trend in its direction (−5% → −7% is +2; +15% → +20% "
                                 "is +5); negative = it fell short (−5% → −4% is −1; +15% → +10% is −5). Cases with a "
                                 "trend of 0 don't count."),
        ("Median of the snapshots", "Reliability and bias are computed in each snapshot and the sheet 'Reliability' "
                                    "shows their median, min and max. 'Pooled' adds up every snapshot first (formula "
                                    "on 'By snapshot')."),
        ("Snapshots", "A snapshot counts with at least 5 codes having the trend. Under 20 codes per snapshot (median) "
                      "the row is flagged as indicative (Kylie Frag)."),
        ("12M (long history)", "Sell-in only: only one snapshot (2025.M09) has 12 months closed, so every month of the "
                               "latest file is also used as a starting point (2024–25)."),
        ("Perimeter", "Sold and last year come from the latest snapshot that has the code (same perimeter, after the "
                      "2026.M02 restatement); the trend comes from what each snapshot showed."),
        ("Matrix", "Same trends applied to a forecast. Common base = last 12 months' volume ÷ 12 × the House seasonal "
                   "index (2 years). Full = base × (1 + T); Half = base × (1 + T/2); Over time = each month grows from "
                   "the centre of the mean (6.5 months back) to that month; Last year = same months LY × (1 + T). "
                   "WAPE change = WAPE with trend − WAPE of the same base without trend, same cases (negative = better). "
                   "% met = cases where sold landed between 0.8× and 1.2× of the forecast. 50/50 rows: trend = "
                   "0.5 × sell-in + 0.5 × sell-out."),
        ("Source", "O10 repo, scripts/tendencias_05_fiabilidad.py and scripts/tendencias_04_matriz.py, from the "
                   "Consensus CSV snapshots in data/<House>/Consensus/."),
    ]
    for i, (a, b) in enumerate(filas, 1):
        ws.cell(row=i, column=1, value=a).font = F_TIT if i == 1 else F_NEG
        c = ws.cell(row=i, column=2, value=b)
        c.font, c.alignment = F_NORMAL, Alignment(wrap_text=True, vertical="top")
        ws.cell(row=i, column=1).alignment = Alignment(vertical="top")
    ws.column_dimensions["A"].width = 26
    ws.column_dimensions["B"].width = 110

    # ------------------------------------------------------------ By snapshot (sumas y fórmulas)
    wsS = wb.create_sheet("By snapshot")
    cabS = ["House", "Signal", "Level", "Trend length", "Horizon", "Snapshot", "Codes", "Sold (units)",
            "Last year (units)", "Σ|moved − anticipated|", "Σ|moved|", "Bias numerator", "Bias denominator (LY)",
            "Reliability", "Bias (pts)"]
    hoja_tabla(wsS, cabS, [14, 16, 10, 12, 18, 11, 8, 14, 14, 18, 14, 15, 17, 12, 11])
    # orden: todas las casas primero, sell-out antes que sell-in, EAN → PL → Brand → House → Cascade, 6M antes que
    # 12M y los plazos en orden; sin las combinaciones que no tienen ningún dato
    O_S, O_N, O_H = ["ep", "si"], ["cod", "pl", "brand", "house", "cas"], ["3", "6", "9", "12", "12h"]
    def orden(k):
        casa, N, tr, h = k.split("|")
        s_, nv = tr.split("_")
        return (casa != "all", casa, O_S.index(s_), O_N.index(nv), int(N), O_H.index(h))
    claves = sorted((k for k in fi["r"] if fi["r"][k].get("fotos")), key=orden)
    for k in claves:
        casa, N, tr, h = k.split("|")
        m = fi["r"][k]
        for F, _, _, n, err, mov, bn, bd, A, LY in m.get("detalle", []):
            r = wsS.max_row + 1
            wsS.append([CASA(casa), *partes(tr), f"{N}M", HORIZ[h][0], F, n, A, LY, err, mov, bn, bd,
                        f"=IF(K{r}=0,\"\",1-J{r}/K{r})", f"=IF(M{r}=0,\"\",L{r}/M{r}*100)"])
    formatear(wsS, {7: ENT, 8: ENT, 9: ENT, 10: ENT, 11: ENT, 12: "#,##0;-#,##0", 13: ENT, 14: PCT, 15: PTS})
    nS = wsS.max_row

    # ------------------------------------------------------------ Reliability (resumen)
    wsR = wb.create_sheet("Reliability", 1)
    cabR = ["House", "Signal", "Level", "Trend length", "Horizon", "Months", "Reliability (median)", "Reliability min",
            "Reliability max", "Reliability pooled", "Bias pts (median)", "Bias min", "Bias max", "Bias pooled",
            "Snapshots", "Codes", "Cases", "Indicative"]
    hoja_tabla(wsR, cabR, [14, 16, 10, 12, 18, 30, 13, 12, 12, 13, 13, 10, 10, 11, 10, 9, 10, 11])
    rng = lambda col: f"'By snapshot'!${col}$2:${col}${nS}"
    crit = lambda r: (f"{rng('A')},$A{r},{rng('B')},$B{r},{rng('C')},$C{r},{rng('D')},$D{r},{rng('E')},$E{r}")
    for k in claves:
        casa, N, tr, h = k.split("|")
        m = fi["r"][k]
        r = wsR.max_row + 1
        wsR.append([CASA(casa), *partes(tr), f"{N}M", HORIZ[h][0], HORIZ[h][1],
                    m["fiab"], m["fiab_min"], m["fiab_max"],
                    f"=IFERROR(1-SUMIFS({rng('J')},{crit(r)})/SUMIFS({rng('K')},{crit(r)}),\"\")",
                    m["bias"] * 100, m["bias_min"] * 100, m["bias_max"] * 100,
                    f"=IFERROR(SUMIFS({rng('L')},{crit(r)})/SUMIFS({rng('M')},{crit(r)})*100,\"\")",
                    m["fotos"], m["codigos"], m["n"], "yes" if m.get("pocos") else ""])
    formatear(wsR, {7: PCT, 8: PCT, 9: PCT, 10: PCT, 11: PTS, 12: PTS, 13: PTS, 14: PTS, 15: ENT, 16: ENT, 17: ENT})
    wsR["J1"].comment = Comment("All snapshots added up first, from the sheet 'By snapshot'.", "Trend analysis")
    wsR["G1"].comment = Comment("Median of the per-snapshot reliability (computed in Python from the same sums "
                                "shown in 'By snapshot').", "Trend analysis")

    # ------------------------------------------------------------ Matrix
    wsM = wb.create_sheet("Matrix")
    cabM = ["House", "Trend length", "Trend", "Applied as", "Horizon", "Cases", "Codes", "Coverage (cases)",
            "Coverage (volume)", "WAPE no trend", "WAPE with trend", "WAPE change (pts)", "% met no trend",
            "% met with trend", "Helps in (snapshots)", "Snapshots"]
    hoja_tabla(wsM, cabM, [14, 12, 40, 30, 9, 9, 8, 12, 12, 12, 12, 12, 12, 12, 12, 10])

    def nombre_fila(cl):
        if cl.startswith("mx_"):
            _, e, s_ = cl.split("_")
            return f"50/50 · sell-out {NIVEL[e]} + sell-in {NIVEL[s_]}"
        s_, nv = cl.split("_")
        return f"{'Sell-out' if s_ == 'ep' else 'Sell-in'} · {NIVEL[nv]}"
    def orden_m(k):
        casa, h, N, cl = k.split("|")
        partes_ = cl.split("_")
        clase = ["si", "ep", "mx"].index(partes_[0])
        niv = [O_N.index(x) for x in partes_[1:]]
        return (casa != "all", casa, int(N), clase, niv, int(h))
    for k in sorted(mx["t"], key=orden_m):
        casa, h, N, cl = k.split("|")
        c = mx["t"][k]
        for b, nb in APLICA.items():
            m = c.get(b)
            r = wsM.max_row + 1
            if not m:                                       # sin casos con ese trend en ese plazo
                continue
            wsM.append([CASA(casa), f"{N}M", nombre_fila(cl), nb, f"{h}M", c["n"], c["cod"], c["cov"], c["cov_vol"],
                        m["w0"], m["w1"], f"=IF(OR(J{r}=\"\",K{r}=\"\"),\"\",(K{r}-J{r})*100)", m["ok0"], m["ok1"],
                        m["ayuda"], m["fotos"]])
    formatear(wsM, {6: ENT, 7: ENT, 8: PCT, 9: PCT, 10: PCT1, 11: PCT1, 12: PTS, 13: PCT, 14: PCT, 15: ENT, 16: ENT})

    wsMR = wb.create_sheet("Matrix references")
    hoja_tabla(wsMR, ["House", "Horizon", "Reference", "Cases", "WAPE", "% met"], [14, 9, 34, 10, 10, 10])
    for k, ref in mx["ref"].items():
        casa, h = k.split("|")
        for b, nb in (("full", "Common base, no trend"), ("ly", "Last year, no trend")):
            wsMR.append([CASA(casa), f"{h}M", nb, ref["n"], ref[b]["w1"], ref[b]["ok1"]])
        if ref.get("cons"):
            wsMR.append([CASA(casa), f"{h}M", "Consensus (scaled to the new perimeter)", ref["n"], ref["cons"]["w1"],
                         ref["cons"]["ok1"]])
    formatear(wsMR, {4: ENT, 5: PCT1, 6: PCT})

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    wb.save(SALIDA)
    print(f"→ {SALIDA.relative_to(RAIZ)}: Reliability {wsR.max_row - 1} filas, By snapshot {nS - 1}, "
          f"Matrix {wsM.max_row - 1}, Matrix references {wsMR.max_row - 1}")


if __name__ == "__main__":
    main()
