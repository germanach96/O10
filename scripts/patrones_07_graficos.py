"""Gráficos del informe de patrones (resultados/graficos/*.png).

Uso: python -m scripts.patrones_07_graficos   (después de los pasos 02-06)
Paleta: azul / naranja / aqua de la skill dataviz (validada: CVD y visión normal en los 3 pares) y gris para la base.
"""
from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts import patrones_04_epos as ep  # noqa: E402
from scripts import patrones_lib as pl  # noqa: E402
from scripts import patrones_03_reglas as r3  # noqa: E402

CACHE = pl.RAIZ / "resultados" / "cache"
SAL = pl.RAIZ / "resultados" / "graficos"
AZUL, NARANJA, AQUA, GRIS = "#2a78d6", "#eb6834", "#1baf7a", "#a3a29c"
TINTA, TINTA2, REJILLA, FONDO = "#0b0b0b", "#52514e", "#e7e6e2", "#fcfcfb"

# tarjetas del informe: (id de validacion.json, texto corto)
HALLAZGOS = [
    ("recorte_excesivo_doble", "2 · Se recortó el Consensus aunque vende por encima de su ritmo\n→ vende más de 1,2× el Consensus"),
    ("consensus_sube_epos_cae", "3 · Consensus > 1,3× su ritmo con el EPOS cayendo\n→ vende menos de la mitad del Consensus"),
    ("canal_cargado_crece", "5 · El canal se cargó en 3 meses\n→ vende más de 1,2× el año pasado"),
    ("serie_anomala", "6 · 3+ meses anómalos en el año\n→ vende menos de la mitad del Consensus"),
    ("bajo_lo_esperable", "7 · Consensus < 0,77× lo esperable\n→ vende más de 1,2× el Consensus"),
    ("aplazado", "8 · Consensus aplazado (meses 7-9 > 2× meses 1-3)\n→ vende más de 1,5× el Consensus"),
    ("cortes_consensus_bajo_gucci", "9 · Gucci: cortes y Consensus < 0,67× el año pasado\n→ vende más de 1,2× el Consensus"),
    ("epos_ultimo_mes_cae", "10 · Kylie MU: EPOS del último mes < 0,6× su media\n→ vende menos de 0,8× el Consensus"),
]


def estilo(ax):
    ax.set_facecolor(FONDO)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(REJILLA)
    ax.tick_params(colors=TINTA2, labelsize=9, length=0)
    ax.grid(axis="x", color=REJILLA, linewidth=0.8)
    ax.set_axisbelow(True)


def fig(w, h):
    f, ax = plt.subplots(figsize=(w, h), dpi=150)
    f.patch.set_facecolor(FONDO)
    estilo(ax)
    return f, ax


def titulo(f, t, sub):
    f.text(0.01, 0.98, t, fontsize=13, fontweight="bold", color=TINTA, va="top")
    f.text(0.01, 0.925, sub, fontsize=9.5, color=TINTA2, va="top")


def g1_trend():
    E = json.loads((CACHE / "epos.json").read_text(encoding="utf-8"))["trend"]
    casas = [c for c in ("Todas", "Gucci", "Kylie MU") if c in E]
    filas = [(c, E[c]["sin_trend"], E[c]["por_nivel"]["código"]["solo_sellin"], E[c]["por_nivel"]["código"]["solo_epos"]) for c in casas]
    f, ax = fig(8.6, 3.9)
    y = np.arange(len(filas))[::-1] * 1.0
    h = 0.24
    for k, (nom, col) in enumerate((("Sin trend (solo el año pasado)", GRIS), ("Trend de sell-in del código", NARANJA), ("Trend de EPOS del código", AZUL))):
        v = [r[k + 1] * 100 for r in filas]
        ax.barh(y + (1 - k) * h, v, height=h - 0.03, color=col, label=nom)
        for yy, vv in zip(y + (1 - k) * h, v):
            ax.text(vv + 0.6, yy, f"{vv:.0f} %", va="center", fontsize=8.5, color=TINTA)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{r[0]}\n({E[r[0]]['casos']:,} casos)".replace(",", ".") for r in filas], color=TINTA, fontsize=9.5)
    ax.set_xlim(0, max(max(r[1:]) for r in filas) * 100 * 1.15)
    ax.set_xlabel("WAPE de los 3 meses siguientes (menos es mejor)", color=TINTA2, fontsize=9)
    ax.legend(loc="lower left", frameon=False, fontsize=8.5, ncol=3, bbox_to_anchor=(-0.01, 1.0))
    titulo(f, "El EPOS del propio código predice el sell-in mejor que el propio sell-in",
           "Forecast = mismos 3 meses del año pasado × (1 + trend de 3 meses). Orígenes 2025.M10–2026.M06.")
    f.subplots_adjust(left=0.17, right=0.98, top=0.76, bottom=0.14)
    f.savefig(SAL / "g1_trend_epos.png", facecolor=FONDO)
    plt.close(f)


def g2_tarjetas():
    V = {c["id"]: c for c in json.loads((CACHE / "validacion.json").read_text(encoding="utf-8"))["candidatos"]}
    filas = [(t, V[i]["medidas"]["base"], V[i]["medidas"]["prob"], V[i]["medidas"]["n"]) for i, t in HALLAZGOS if i in V]
    f, ax = fig(9.4, 6.4)
    y = np.arange(len(filas))[::-1]
    for yy, (t, b, p, n) in zip(y, filas):
        ax.plot([b * 100, p * 100], [yy, yy], color=REJILLA, linewidth=3, solid_capstyle="round", zorder=1)
        ax.scatter([b * 100], [yy], s=60, color=GRIS, zorder=2, edgecolor=FONDO, linewidth=2)
        ax.scatter([p * 100], [yy], s=70, color=AZUL, zorder=3, edgecolor=FONDO, linewidth=2)
        ax.text(p * 100 + (3 if p > b else -3), yy, f"{p:.0%}".replace("%", " %"), va="center",
                ha="left" if p > b else "right", fontsize=9, color=TINTA, fontweight="bold")
        ax.text(b * 100 + (-3 if p > b else 3), yy, f"{b:.0%}".replace("%", " %"), va="center",
                ha="right" if p > b else "left", fontsize=8.5, color=TINTA2)
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] + f"  (n={r[3]})" for r in filas], fontsize=8.6, color=TINTA)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0 %", "25 %", "50 %", "75 %", "100 %"])
    ax.scatter([], [], s=60, color=GRIS, label="Tasa base (sin mirar la señal)")
    ax.scatter([], [], s=70, color=AZUL, label="Con la señal")
    ax.legend(loc="lower right", frameon=False, fontsize=8.5, bbox_to_anchor=(1, -0.12), ncol=2)
    titulo(f, "Con la señal, el escenario pasa entre 1,4 y 3 veces más a menudo",
           "Probabilidad de que en los 3 meses siguientes se cumpla lo que dice la tarjeta. Fotos 2025.M09–2026.M06.")
    f.subplots_adjust(left=0.47, right=0.97, top=0.86, bottom=0.1)
    f.savefig(SAL / "g2_tarjetas.png", facecolor=FONDO)
    plt.close(f)


def g3_canal():
    E = json.loads((CACHE / "epos.json").read_text(encoding="utf-8"))["canal"]
    casa = "Kylie MU"
    T = pd.DataFrame(E[casa]["tramos"])
    f, ax = fig(8.6, 3.8)
    ax.grid(axis="x", visible=False)
    ax.grid(axis="y", color=REJILLA, linewidth=0.8)
    x = np.arange(len(T))
    v = T.sellin_siguiente_vs_ultimo * 100
    ax.bar(x, v, width=0.62, color=[AZUL if a >= 0 else NARANJA for a in v])
    ax.axhline(0, color=TINTA2, linewidth=0.8)
    for xx, vv, n in zip(x, v, T.n):
        ax.text(xx, vv + (1.2 if vv >= 0 else -1.2), f"{vv:+.0f} %", ha="center", va="bottom" if vv >= 0 else "top", fontsize=9, color=TINTA, fontweight="bold")
        ax.text(xx, ax.get_ylim()[0] if False else -44, f"n={n}", ha="center", fontsize=7.5, color=TINTA2)
    ax.set_xticks(x)
    ax.set_xticklabels([t.replace(" de lo que vendió", "\nde lo que vendió").replace("a la par (±10 %)", "a la par\n(±10 %)")
                        .replace("algo más", "algo más\n(+10 a +35 %)").replace("algo menos", "algo menos\n(−10 a −26 %)") for t in T.tramo], fontsize=8.3, color=TINTA)
    ax.set_ylim(-48, max(v) + 10)
    ax.set_ylabel("Sell-in de los 3 meses siguientes\nfrente a los 3 últimos", color=TINTA2, fontsize=8.5)
    ax.spines["left"].set_visible(False)
    titulo(f, f"{casa}: lo que el retailer compra de más se devuelve en el trimestre siguiente",
           "En los últimos 3 meses, el retailer compró (sell-in) frente a lo que vendió (EPOS), comparado con lo normal en 12 meses.")
    f.subplots_adjust(left=0.12, right=0.98, top=0.8, bottom=0.22)
    f.savefig(SAL / "g3_canal.png", facecolor=FONDO)
    plt.close(f)


def g4_gucci():
    K = pd.read_parquet(CACHE / "casos_K.parquet").dropna(subset=["e_yoy3"])
    K = K[(K.casa == "Gucci") & (K.y3_ly > 0)]
    filas = []
    for F, q in K.groupby("F"):
        rec = q.y3_ly * np.exp(np.clip(q.e_yoy3, -ep.TOPE, ep.TOPE))
        a = q.A3.to_numpy()
        filas.append((pl.int_a_mes(int(F)), ep.wape(a, q.c3.to_numpy()) * 100, ep.wape(a, (.5 * q.c3 + .5 * rec).to_numpy()) * 100))
    D = pd.DataFrame(filas, columns=["foto", "cons", "mix"])
    f, ax = fig(8.6, 3.8)
    ax.grid(axis="x", visible=False)
    ax.grid(axis="y", color=REJILLA, linewidth=0.8)
    x = np.arange(len(D))
    ax.plot(x, D.cons, color=GRIS, linewidth=2, linestyle=(0, (4, 3)), marker="o", markersize=6, label="Consensus - Final")
    ax.plot(x, D.mix, color=AZUL, linewidth=2, marker="o", markersize=6, label="Mitad Consensus, mitad receta EPOS")
    ax.axhline(40, color=AQUA, linewidth=1, linestyle=":")
    ax.text(len(D) - 0.6, 41, "meta WAPE 40 %", color=TINTA2, fontsize=8, ha="right")
    for xx, a, b in zip(x, D.cons, D.mix):
        if abs(a - b) >= 3:
            ax.text(xx, b - 7, f"{b - a:+.0f} pts", ha="center", fontsize=8, color=AZUL, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(D.foto, fontsize=8.5, color=TINTA)
    ax.set_ylim(0, max(D.cons.max(), D.mix.max()) * 1.12)
    ax.set_ylabel("WAPE90 (menos es mejor)", color=TINTA2, fontsize=9)
    ax.spines["left"].set_visible(False)
    ax.legend(loc="upper right", frameon=False, fontsize=8.5)
    titulo(f, "Gucci: mezclar el Consensus con la receta de EPOS baja el error en 7 de 9 fotos",
           "WAPE de los 3 meses siguientes a cada foto, regulares puntuables. Receta = mismos meses del año pasado × (1 + trend EPOS 3M).")
    f.subplots_adjust(left=0.09, right=0.98, top=0.8, bottom=0.12)
    f.savefig(SAL / "g4_gucci_mezcla.png", facecolor=FONDO)
    plt.close(f)


if __name__ == "__main__":
    SAL.mkdir(parents=True, exist_ok=True)
    _ = r3
    g1_trend()
    g2_tarjetas()
    g3_canal()
    g4_gucci()
    print("gráficos en", SAL)
