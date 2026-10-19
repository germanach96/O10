"""Validación escéptica de los candidatos a hallazgo (paso 5 de la búsqueda de patrones).

Uso: python -m scripts.patrones_06_validar   (después de los pasos 02-05)

Cada candidato se intenta tumbar con:
- partes antigua / reciente y por casa;
- explicaciones aburridas (un código, una brand, una foto, la ruptura de perímetro, una casa);
- solo casos con referencia grande (≥ 300 uds en 3 meses): un denominador pequeño infla el ratio;
- impacto en unidades: Σ vendido / Σ referencia con la señal frente a sin ella;
- permutación dentro de cada foto (500 veces): se baraja la señal entre los códigos de la misma foto. Si el efecto
  sale igual con la señal barajada, lo explica el mes, no la señal.
Y dos pruebas del EPOS: si el desfase del canal añade algo al propio vaivén del sell-in, y si la receta con EPOS le
gana al Consensus en Gucci (intervalo remuestreando códigos).
Guarda resultados/cache/validacion.json.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from scripts import patrones_lib as pl
from scripts import patrones_03_reglas as r3
from scripts import patrones_04_epos as ep

CACHE = pl.RAIZ / "resultados" / "cache"

# (id, tabla, grupo (columna, valor) o None, señales, escenario, dirección)
CANDIDATOS = [
    ("consensus_sube_epos_cae", "K", None, ["N_k_ep_vs"], "muy_bajo", 1),
    ("consensus_sube_epos_cae_bajo", "K", None, ["N_k_ep_vs"], "bajo", 1),
    ("recorte_excesivo", "K", None, ["N_k_sobre_rev_dn"], "bajo", -1),
    ("recorte_excesivo_doble", "K", None, ["K_rev_dn", "N_k_sobre_rev_dn"], "alto", 1),
    ("aplazado", "K", None, ["K_tardio"], "muy_alto", 1),
    ("aplazado_mu_pendiente", "K", ("casa", "Kylie MU"), ["K_tardio", "N_pend_up"], "muy_alto", 1),
    ("serie_anomala", "K", None, ["N_anom_muchas"], "muy_bajo", 1),
    ("pico_planificado_erratico", "K", ("tramo_edad", "37+ meses"), ["K_pico_plan", "C5"], "muy_bajo", 1),
    ("bajo_lo_esperable", "K", None, ["N_k_vs_esp_lo"], "alto", 1),
    ("sobre_lo_esperable_gucci", "K", ("casa", "Gucci"), ["N_k_vs_esp_hi"], "bajo", 1),
    ("sesgo_repite", "K", None, ["N_k_paso_alto"], "bajo", -1),
    ("cortes_consensus_bajo_gucci", "K", ("casa", "Gucci"), ["O_cortes", "K_ly_lo"], "alto", 1),
    ("ultimo_cero_consensus", "K", None, ["K_ultimo_cero"], "muy_bajo", 1),
    ("epos_ultimo_mes_cae", "K", ("casa", "Kylie MU"), ["N_ep_ult_lo"], "bajo", 1),
    ("canal_cargado_crece", "Y", None, ["N_stock3_alto"], "alto", 1),
    ("canal_cargado_pendiente_rabbits", "Y", ("seg", "Rabbits"), ["X_stock_alto", "N_pend_up"], "muy_alto", 1),
    ("sellin_sube_epos_plano", "Y", None, ["N_si_up_ep_plano"], "muy_bajo", -1),
]


def permutacion(x, y, F, base_mask, dir_, n=500, semilla=5):
    rng = np.random.default_rng(semilla)
    obs = dir_ * (y[x].mean() - y[base_mask].mean())
    idx_f = [np.where(base_mask & (F == f))[0] for f in np.unique(F[base_mask])]
    cuenta = 0
    for _ in range(n):
        xp = np.zeros_like(x)
        for idx in idx_f:
            xp[idx] = rng.permutation(x[idx])
        cuenta += dir_ * (y[xp].mean() - y[base_mask].mean()) >= obs
    return (cuenta + 1) / (n + 1)


def validar_candidato(c, tablas):
    cid, tabla, grupo, sen, esc, dir_ = c
    Z, X, _ = tablas[tabla]
    gm = np.ones(len(Z), bool) if grupo is None else (Z[grupo[0]].astype(str) == grupo[1]).to_numpy()
    x = gm.copy()
    for s in sen:
        x &= X[s].to_numpy()
    y = Z[f"Y_{esc}"].to_numpy()
    med = r3.medir(x, y, Z, gm, dir_)
    F = Z.F.to_numpy()
    corte = r3.CORTE["K"] if tabla == "K" else r3.CORTE["Y_epos" if any(s.startswith(("N_st", "N_stock", "N_ep", "N_kap", "X_", "EP_", "N_si_")) for s in sen) else "Y"]
    partes = {}
    for nom, m in (("antiguo", F < corte), ("reciente", F >= corte)):
        partes[nom] = dict(n=int((x & m).sum()), p=float(y[x & m].mean()) if (x & m).any() else None, base=float(y[gm & m].mean()))
    grande = (Z.ref >= 300).to_numpy()
    xg = x & grande
    vol = dict(n=int(xg.sum()), p=float(y[xg].mean()) if xg.sum() else None, base=float(y[gm & grande].mean()))
    A, R = Z.A3.to_numpy(), Z.ref.to_numpy()
    unidades = dict(con_senal=float(A[x].sum() / R[x].sum()), sin_senal=float(A[gm & ~x].sum() / R[gm & ~x].sum()),
                    referencia_uds=float(R[x].sum()), vendido_uds=float(A[x].sum()))
    caidas = r3.aburridas(x, y, Z, gm, dir_, tabla)
    p_perm = permutacion(x, y, F, gm, dir_)
    ok_vol = vol["p"] is not None and vol["n"] >= 15 and dir_ * (vol["p"] - vol["base"]) >= 0.5 * dir_ * (med["prob"] - med["base"])
    ok_part = all(v["p"] is not None and dir_ * (v["p"] - v["base"]) > 0 for v in partes.values() if v["n"] >= 10)
    return dict(id=cid, tabla=tabla, grupo=grupo, senales=sen, escenario=esc, dir=dir_,
                medidas={k: v for k, v in med.items() if k != "por_casa"}, por_casa=med["por_casa"], partes=partes,
                volumen_grande=vol, unidades=unidades, explicaciones_que_la_tumban=caidas, p_permutacion=float(p_perm),
                mediana_ratio=float(np.median(Z.ratio[x])),
                supera=bool(not caidas and p_perm < 0.05 and ok_vol and ok_part),
                motivo=("" if (not caidas and p_perm < 0.05 and ok_vol and ok_part) else
                        "; ".join([*caidas, *(["permutación por foto p ≥ 0,05"] if p_perm >= 0.05 else []),
                                   *(["no aguanta con referencias grandes (≥ 300 uds)"] if not ok_vol else []),
                                   *(["cambia de dirección en una de las dos partes"] if not ok_part else [])])))


def canal_mas_alla_del_sellin():
    """¿El desfase sell-in/EPOS predice el sell-in siguiente más allá del vaivén del propio sell-in?
    dsi = log(A3 / s3) frente a g0 (desfase del canal) y rev = log(s3 / (s12/4)) (3M frente a su ritmo)."""
    filas = []
    for casa in pl.CASAS:
        _, panel = pl.cargar(casa)
        reg = panel.atr["Article Type"].eq("Regular Item").to_numpy()
        SI, EP, T0, T1 = panel.ACT, panel.EPOS, panel.T0, panel.T1
        for F in range(T0 + 12, T1 - 2):
            k = F - T0
            E12, E3 = EP[:, k - 12:k], EP[:, k - 3:k]
            s12, s3, a3 = SI[:, k - 12:k].sum(1), SI[:, k - 3:k].sum(1), SI[:, k:k + 3].sum(1)
            ok = reg & ~np.isnan(E12).any(1) & (s12 >= 150) & (s3 > 0) & (a3 > 0)
            e12, e3 = E12.sum(1), E3.sum(1)
            ok &= (e12 >= 100) & (e3 > 0)
            for i in np.where(ok)[0]:
                filas.append(dict(casa=casa, F=F, ean=panel.eans[i], dsi=np.log(a3[i] / s3[i]),
                                  g0=np.log((s3[i] / e3[i]) / (s12[i] / e12[i])), rev=np.log(s3[i] / (s12[i] / 4))))
    D = pd.DataFrame(filas)
    D = D[np.isfinite(D[["dsi", "g0", "rev"]]).all(1) & (D.g0.abs() < 3)]
    out = {}
    for casa, g in [("Todas", D)] + list(D.groupby("casa")):
        if len(g) < 60:
            continue
        Xm = np.column_stack([np.ones(len(g)), g.rev, g.g0])
        b, *_ = np.linalg.lstsq(Xm, g.dsi.to_numpy(), rcond=None)
        # intervalo remuestreando códigos
        rng = np.random.default_rng(2)
        cods = g.ean.unique()
        gi = {c: np.where(g.ean.to_numpy() == c)[0] for c in cods}
        bs = []
        for _ in range(300):
            s = np.concatenate([gi[c] for c in rng.choice(cods, len(cods))])
            bb, *_ = np.linalg.lstsq(Xm[s], g.dsi.to_numpy()[s], rcond=None)
            bs.append(bb[2])
        b1, *_ = np.linalg.lstsq(Xm[:, :2], g.dsi.to_numpy(), rcond=None)
        res = g.dsi.to_numpy() - Xm @ b
        res1 = g.dsi.to_numpy() - Xm[:, :2] @ b1
        out[casa] = dict(casos=len(g), coef_desfase=float(b[2]), ic90=[float(np.percentile(bs, 5)), float(np.percentile(bs, 95))],
                         coef_vaiven_sellin=float(b[1]), mejora_error_mediano=float(np.median(np.abs(res1)) - np.median(np.abs(res))))
    return out


def epos_frente_consensus():
    K = pd.read_parquet(CACHE / "casos_K.parquet")
    Z = K.dropna(subset=["s_yoy3", "e_yoy3"]).reset_index(drop=True)
    Z = Z[Z.y3_ly > 0].reset_index(drop=True)
    out = {}
    for casa, g in [("Todas", Z)] + list(Z.groupby("casa")):
        if len(g) < 60:
            continue
        g = g.reset_index(drop=True)
        T = np.clip(g.e_yoy3, -ep.TOPE, ep.TOPE).to_numpy()
        rec = g.y3_ly.to_numpy() * np.exp(T)
        mix = .5 * g.c3.to_numpy() + .5 * rec
        a = g.A3.to_numpy()
        out[casa] = dict(casos=len(g), wape_consensus=ep.wape(a, g.c3.to_numpy()), wape_receta_epos=ep.wape(a, rec),
                         wape_mitad_y_mitad=ep.wape(a, mix),
                         ic90_receta_menos_consensus=ep.boot_dif(g, rec, g.c3.to_numpy()),
                         ic90_mitad_menos_consensus=ep.boot_dif(g, mix, g.c3.to_numpy()))
        # por mitad de fotos
        for nom, m in (("antiguo", g.F < r3.CORTE["K"]), ("reciente", g.F >= r3.CORTE["K"])):
            q = g[m]
            if len(q) >= 40:
                Tq = np.clip(q.e_yoy3, -ep.TOPE, ep.TOPE).to_numpy()
                out[casa][f"{nom}_consensus"] = ep.wape(q.A3.to_numpy(), q.c3.to_numpy())
                out[casa][f"{nom}_receta_epos"] = ep.wape(q.A3.to_numpy(), q.y3_ly.to_numpy() * np.exp(Tq))
    return out


def main():
    tablas = {t: r3.cargar_tabla(t) for t in ("K", "Y")}
    res = {"candidatos": [validar_candidato(c, tablas) for c in CANDIDATOS],
           "canal_mas_alla_del_sellin": canal_mas_alla_del_sellin(), "epos_frente_consensus": epos_frente_consensus()}
    (CACHE / "validacion.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    for c in res["candidatos"]:
        m = c["medidas"]
        print(f"{c['id']:34s} {'SUPERA' if c['supera'] else 'CAE   '} p={m['prob']:.0%} base={m['base']:.0%} n={m['n']} ind={m['n_indep']} "
              f"cod={m['codigos']} perm={c['p_permutacion']:.3f} vol={c['volumen_grande']} uds={c['unidades']['con_senal']:.2f} vs {c['unidades']['sin_senal']:.2f} "
              f"med={c['mediana_ratio']:.2f} partes={[(k, v['p'] and round(v['p'], 2), round(v['base'], 2), v['n']) for k, v in c['partes'].items()]} {c['motivo']}")
    print("CANAL", json.dumps(res["canal_mas_alla_del_sellin"], default=float))
    print("EPOS vs CONSENSUS", json.dumps(res["epos_frente_consensus"], default=float))


if __name__ == "__main__":
    main()
