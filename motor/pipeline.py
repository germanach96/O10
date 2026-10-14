"""Pipeline: lee todas las fotos de una casa, calcula recetas, cubo, resúmenes, score y detector.

Uso:  python -m motor.pipeline [carpeta_datos] [carpeta_salida] [--sin-cubo]

Por defecto lee data/<Casa>/Consensus/<Casa>_AAAA_MM.csv y escribe el HTML en diseno/ejemplos/.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from .lector import Foto, int_a_mes, leer_foto
from .recetas import CELDAS, EJES, MotorFoto, Rejilla

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "data"                                   # data/<Casa>/Consensus/*.csv
HTML_EJEMPLO = RAIZ / "diseno" / "ejemplos" / "BRUJULAS_ejemplo.html"


def cargar_config(ruta: Path | None = None) -> dict:
    ruta = ruta or Path(__file__).with_name("config.json")
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


# ------------------------------------------------------------------ actuals
def actuals_futuros(foto: Foto, fotos: list[Foto], hz: int) -> np.ndarray:
    """Actuals de F+1..F+hz por código de `foto`, tomados de la foto posterior más reciente.
    NaN = todavía no se conoce (tramo abierto)."""
    out = np.full((len(foto.eans), hz), np.nan)
    for j in range(hz):
        t = foto.mes + 1 + j
        for P in sorted(fotos, key=lambda f: -f.mes):
            if P.mes <= t:          # el mes en curso de una foto nunca vale como actual
                continue
            if t < P.primer_mes_actuals:
                continue
            fila = {e: k for k, e in enumerate(P.eans)}
            k = P.col(t)
            for i, e in enumerate(foto.eans):
                if np.isnan(out[i, j]) and e in fila:
                    v = P.mat["Actuals"][fila[e], k]
                    out[i, j] = 0.0 if np.isnan(v) else v
            break
    return out


def epos_externo(foto: Foto, fotos: list[Foto], motor_t_hist: np.ndarray) -> np.ndarray | None:
    """EPOS de meses anteriores a la foto tomado de fotos posteriores (si la foto no trae EPOS)."""
    out = np.full((len(foto.eans), len(motor_t_hist)), np.nan)
    hay = False
    for P in sorted(fotos, key=lambda f: -f.mes):
        if P.mes <= foto.mes:
            continue
        fila = {e: k for k, e in enumerate(P.eans)}
        idx = np.array([fila.get(e, -1) for e in foto.eans])
        for j, t in enumerate(motor_t_hist):
            if t >= foto.mes:
                continue
            k = P.col(t)
            if 0 <= k < P.mat["EPOS"].shape[1]:
                v = np.where(idx >= 0, P.mat["EPOS"][np.maximum(idx, 0), k], np.nan)
                hueco = np.isnan(out[:, j])
                out[hueco, j] = v[hueco]
                hay = hay or (~np.isnan(v)).any()
    return out if hay else None


# ------------------------------------------------------------------ filtro general de tipos
TIPOS = ("Regular", "One Shot", "Central", "Local")


def clases(cod: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Tipo de artículo (Regular / One Shot) y responsable (Central / Local; vacío = Central)."""
    art = np.where(cod["Article Type"].eq("Regular Item"), "Regular", "One Shot")
    resp = np.where(cod["Final Responsibility"].isin(["Central", ""]), "Central", "Local")
    return art, resp


def mascara_cuenta(cod: pd.DataFrame, ignorar=()) -> np.ndarray:
    """True = el código cuenta en los cálculos (trends de grupo y scope)."""
    art, resp = clases(cod)
    ign = set(ignorar)
    return ~np.isin(art, list(ign)) & ~np.isin(resp, list(ign))


def variantes_tipos(cfg: dict) -> list[tuple[str, ...]]:
    """Combinaciones de tipos ignorados que se precalculan. Ignorar Regular o Central vacía el scope,
    así que solo cambian los cálculos las combinaciones de One Shot y Local."""
    ign = cfg.get("filtro_tipos", {}).get("precalcular", ["One Shot", "Local"])
    out = [()]
    for t in ign:
        out += [v + (t,) for v in out]
    return [tuple(sorted(v)) for v in out]


def clave_variante(ignorar) -> str:
    return ",".join(sorted(ignorar))


# ------------------------------------------------------------------ cálculo por foto
class ResultadoFoto:
    pass


def calcular_foto(foto: Foto, fotos: list[Foto], cfg: dict, R: Rejilla, ignorar=()) -> ResultadoFoto:
    hz = cfg["horizonte"]
    ext = None
    if cfg.get("epos_historico_de_foto_mas_reciente") and np.isnan(
            foto.mat["EPOS"][:, foto.meses < foto.mes]).all():
        t_hist = np.arange(foto.mes - 36, foto.mes)
        ext = epos_externo(foto, fotos, t_hist)
        aviso = "La foto no trae EPOS: el EPOS histórico se toma de la foto más reciente"
        if ext is not None and aviso not in foto.avisos:
            foto.avisos.append(aviso)
    cod = foto.codigos
    cuenta = mascara_cuenta(cod, ignorar)
    M = MotorFoto(foto, cfg, R, epos_externo=ext, cuenta=cuenta)
    A = actuals_futuros(foto, fotos, hz)
    scope = np.where(cod["scope"].to_numpy() & cuenta)[0]
    tramos = cfg["tramos"]
    nt = len(tramos)

    res = ResultadoFoto()
    res.foto, res.motor, res.scope, res.A = foto, M, scope, A
    n = len(scope)
    res.abs = np.zeros((n, R.n, nt), np.float32)
    res.sgn = np.zeros((n, R.n, nt), np.float32)
    res.act = np.zeros((n, nt), np.float64)
    res.cons_abs = np.zeros((n, nt))
    res.cons_sgn = np.zeros((n, nt))
    res.cerrado = np.zeros((n, nt), bool)
    res.valido = np.zeros((n, R.n), bool)
    res.log = []
    for a, i in enumerate(scope):
        Fc, val = M.forecasts(i)
        res.valido[a] = val
        for k, (h0, h1) in enumerate(tramos):
            sl = slice(h0 - 1, h1)
            act = A[i, sl]
            res.cerrado[a, k] = not np.isnan(act).any()
            if not res.cerrado[a, k]:
                continue
            d = Fc[:, sl] - act[None]
            res.abs[a, :, k] = np.abs(d).sum(1)
            res.sgn[a, :, k] = d.sum(1)
            res.act[a, k] = act.sum()
            dc = M.cons_fut[i, sl] - act
            res.cons_abs[a, k] = np.abs(dc).sum()
            res.cons_sgn[a, k] = dc.sum()
        mot = M.motivos_invalidez(i)
        if mot:
            res.log.append({"ean": foto.eans[i], "recetas_invalidas": int((~val).sum()), "motivos": mot})
    return res


# ------------------------------------------------------------------ selección
def pesos_tramo(res: ResultadoFoto, cfg: dict, criterio: str) -> np.ndarray:
    """Peso de cada tramo (solo tramos cerrados)."""
    w = np.array(cfg["peso_tramo"], float) if criterio == "ponderado" else np.ones(len(cfg["tramos"]))
    return w[None, :] * res.cerrado


def elegir(num: np.ndarray, sgn: np.ndarray, valido: np.ndarray) -> int:
    """Menor error; desempate menor |sesgo|; después la primera receta (orden canónico)."""
    x = np.where(valido, num, np.inf)
    best = x.min()
    if not np.isfinite(best):
        return -1
    cand = np.where(x <= best * (1 + 1e-9) + 1e-9)[0]
    return int(cand[np.argmin(np.abs(sgn[cand]))])


def kpis(abs_t, sgn_t, act_t, cfg) -> dict:
    """KPIs por ventana a partir de numeradores por tramo (tramos 1, 1-2, 1-3)."""
    out = {}
    for nombre, hasta in [("90", 1), ("180", 2), ("9M", 3)]:
        a = float(np.sum(act_t[:hasta]))
        if a <= 0:
            out[nombre] = None
            continue
        out[nombre] = {"wape": float(np.sum(abs_t[:hasta]) / a),
                       "spp": float(cfg["spp_signo"] * np.sum(sgn_t[:hasta]) / a), "act": a}
    return out


def mejores_por_eje(err: np.ndarray, valido: np.ndarray, R: Rejilla) -> dict:
    """Para cada eje, el mejor error alcanzable en cada valor del eje (min sobre el resto)."""
    x = np.where(valido, err, np.inf).reshape(R.forma)
    out = {}
    for ax, k in enumerate(EJES):
        otros = tuple(i for i in range(len(EJES)) if i != ax)
        v = x.min(axis=otros)
        out[k] = [None if not np.isfinite(z) else float(z) for z in v]
    return out


def con_respaldo(arr: np.ndarray, valido: np.ndarray, R: Rejilla) -> np.ndarray:
    """Para agregar recetas en grupos: receta inválida en un código -> la misma sin trend (w=0)."""
    forma = (arr.shape[0],) + R.forma + arr.shape[2:]
    a = arr.reshape(forma)
    v = valido.reshape((valido.shape[0],) + R.forma)
    sin_trend = a[:, :, :1, :1, :1, :, :, :, :1]  # (s, w=0, m0, N0, c, p, g0)
    sin_trend = np.broadcast_to(sin_trend, a.shape)
    vv = v.reshape(v.shape + (1,) * (a.ndim - v.ndim))
    return np.where(vv, a, sin_trend).reshape(arr.shape)


# ------------------------------------------------------------------ resumen por foto
def resumen_foto(res: ResultadoFoto, cfg: dict, R: Rejilla) -> dict:
    foto, M = res.foto, res.motor
    cod = foto.codigos
    crit = cfg["criterio_oraculo"]
    W = pesos_tramo(res, cfg, crit)
    out_cod = {}
    hay_cerrados = bool(res.cerrado.any())
    for a, i in enumerate(res.scope):
        e = foto.eans[i]
        info = {
            "tam_grupos": [int(M.tam_grupo[g, i]) for g in range(len(CELDAS))],
            "tramo_edad": cod["tramo_edad"].iat[i],
            "historia_corta": bool(M.historia_corta[i]),
            "cerrados": [bool(x) for x in res.cerrado[a]],
            "consensus_fut": [float(x) for x in M.cons_fut[i]],
            "actual_fut": [None if np.isnan(x) else float(x) for x in res.A[i]],
        }
        if res.cerrado[a].any():
            num = (res.abs[a] * W[a]).sum(1)
            den = float((res.act[a] * W[a]).sum())
            sg = (res.sgn[a] * W[a]).sum(1)
            r = elegir(num, sg, res.valido[a])
            err = num / den if den > 0 else None
            info["oraculo"] = r
            info["oraculo_receta"] = R.receta(r)
            info["kpi_receta"] = kpis(res.abs[a, r], res.sgn[a, r], res.act[a], cfg)
            info["kpi_consensus"] = kpis(res.cons_abs[a], res.cons_sgn[a], res.act[a], cfg)
            if err is not None:
                info["ejes"] = mejores_por_eje(err, res.valido[a], R)
            Fc, _ = M.forecasts(i)
            info["fc_oraculo"] = [float(x) for x in Fc[r]]
            info["desglose"] = M.desglose(i, r)
        out_cod[e] = info

    # Regla por grupos (casa, brand, product line): recetas sumadas sobre los códigos del grupo
    reglas = {}
    if hay_cerrados:
        absR = con_respaldo(res.abs, res.valido, R)
        sgnR = con_respaldo(res.sgn, res.valido, R)
        eans_scope = [foto.eans[i] for i in res.scope]
        sc = cod.iloc[res.scope]
        grupos = {"Casa: " + foto.casa: np.ones(len(res.scope), bool)}
        for b in sorted(sc["Brand"].unique()):
            grupos["Brand: " + b] = (sc["Brand"] == b).to_numpy()
        for pl in sorted(sc["Product Line"].unique()):
            grupos["PL: " + pl] = (sc["Product Line"] == pl).to_numpy()
        for nombre, msk in grupos.items():
            Wm = W[msk]
            num = (absR[msk] * Wm[:, None, :]).sum((0, 2))
            sg = (sgnR[msk] * Wm[:, None, :]).sum((0, 2))
            den = float((res.act[msk] * Wm).sum())
            if den <= 0:
                continue
            todos = np.ones(R.n, bool)
            r = elegir(num, sg, todos)
            reglas[nombre] = {
                "receta": r, "receta_txt": R.receta(r), "n_codigos": int(msk.sum()),
                "eans": [e for e, mm in zip(eans_scope, msk) if mm],
                "kpi_receta": kpis(absR[msk, r].sum(0), sgnR[msk, r].sum(0), res.act[msk].sum(0), cfg),
                "kpi_consensus": kpis(res.cons_abs[msk].sum(0), res.cons_sgn[msk].sum(0), res.act[msk].sum(0), cfg),
                "kpi_oraculo": kpis(
                    sum(res.abs[a, out_cod[eans_scope[a]]["oraculo"]] for a in np.where(msk)[0]
                        if "oraculo" in out_cod[eans_scope[a]]),
                    sum(res.sgn[a, out_cod[eans_scope[a]]["oraculo"]] for a in np.where(msk)[0]
                        if "oraculo" in out_cod[eans_scope[a]]),
                    res.act[msk].sum(0), cfg),
                "ejes": mejores_por_eje(num / den, todos, R),
                "tam_grupos_medio": [float(np.mean([M.tam_grupo[g, i] for i in res.scope[msk]])) for g in range(len(CELDAS))],
            }
    return {
        "foto": foto.etiqueta, "casa": foto.casa, "archivo": foto.archivo,
        "meses_fut": [int_a_mes(t) for t in M.t_fut],
        "hay_tramos_cerrados": hay_cerrados,
        "tramos_cerrados": [bool(res.cerrado[:, k].any()) for k in range(res.cerrado.shape[1])],
        "n_scope": int(len(res.scope)), "codigos": out_cod, "reglas": reglas,
        "avisos": foto.avisos, "n_log": len(res.log),
    }


# ------------------------------------------------------------------ score multi-foto
def peso_foto(res: ResultadoFoto, ultima: int, cfg: dict) -> float:
    pf = cfg["peso_foto"]
    if pf.get("tipo") == "exponencial":
        return pf["base"] ** ((ultima - res.foto.mes) / pf["semivida_meses"])
    return 1.0


def score_multifoto(resultados: list[ResultadoFoto], cfg: dict, R: Rejilla):
    """Receta elegida por código y por grupo, sumando todas las fotos con tramos cerrados."""
    ultima = max(r.foto.mes for r in resultados)
    num, sgn, den, val, fotos_usadas = {}, {}, {}, {}, {}
    for res in resultados:
        if not res.cerrado.any():
            continue
        d = peso_foto(res, ultima, cfg)
        W = pesos_tramo(res, cfg, "ponderado") * d
        absR = con_respaldo(res.abs, res.valido, R)
        sgnR = con_respaldo(res.sgn, res.valido, R)
        for a, i in enumerate(res.scope):
            e = res.foto.eans[i]
            if not res.cerrado[a].any():
                continue
            num[e] = num.get(e, 0) + (res.abs[a] * W[a]).sum(1)
            sgn[e] = sgn.get(e, 0) + (res.sgn[a] * W[a]).sum(1)
            den[e] = den.get(e, 0) + float((res.act[a] * W[a]).sum())
            val[e] = val.get(e, True) & res.valido[a]
            fotos_usadas.setdefault(e, []).append(res.foto.etiqueta)
            # versión con respaldo para reglas de grupo
            num.setdefault(("R", e), 0)
            num[("R", e)] = num[("R", e)] + (absR[a] * W[a]).sum(1)
            sgn[("R", e)] = sgn.get(("R", e), 0) + (sgnR[a] * W[a]).sum(1)
    elegida = {}
    for e in den:
        r = elegir(num[e], sgn[e], val[e])
        elegida[e] = {"receta": r, "score": (float(np.where(val[e], num[e], np.inf)[r] / den[e]) if den[e] > 0 else None),
                      "fotos": fotos_usadas[e], "txt": R.receta(r) if r >= 0 else None}
    return elegida, num, sgn, den


# ------------------------------------------------------------------ detector
def detector(res_ult: ResultadoFoto, elegida: dict, num: dict, sgn: dict, den: dict, cfg: dict, R: Rejilla) -> dict:
    foto, M = res_ult.foto, res_ult.motor
    cod = foto.codigos
    # recetas de regla con la composición de la foto más actual
    def regla(eans):
        eans = [e for e in eans if ("R", e) in num]
        if not eans:
            return None
        n_ = sum(num[("R", e)] for e in eans)
        s_ = sum(sgn[("R", e)] for e in eans)
        return elegir(n_, s_, np.ones(R.n, bool))
    sc = cod.iloc[res_ult.scope]
    cache = {}
    def regla_de(clave, valor):
        if (clave, valor) not in cache:
            cache[(clave, valor)] = regla(list(sc.index[sc[clave] == valor]) if clave else list(sc.index))
        return cache[(clave, valor)]

    filas = []
    for i in res_ult.scope:
        e = foto.eans[i]
        Fc, val = M.forecasts(i)
        fuentes = {
            "codigo": elegida.get(e, {}).get("receta", -1) if e in elegida else -1,
            "pl": regla_de("Product Line", cod["Product Line"].iat[i]),
            "brand": regla_de("Brand", cod["Brand"].iat[i]),
            "casa": regla_de(None, None),
        }
        fila = {"ean": e, "desc": cod["Planning Item Description"].iat[i], "brand": cod["Brand"].iat[i],
                "pl": cod["Product Line"].iat[i], "segmento": cod["Final Segment"].iat[i],
                "edad": cod["tramo_edad"].iat[i], "flag": cod["Ignore System Forecast Flag"].iat[i],
                "consensus": [round(float(x), 1) for x in M.cons_fut[i]], "recetas": {}}
        for nombre, r in fuentes.items():
            if r is None or r < 0:
                fila["recetas"][nombre] = None
                continue
            rr = r
            respaldo = False
            if not val[r]:   # trend no calculable hoy para este código -> misma receta sin trend
                ix = {k: R.idx[k][r] for k in EJES}
                ix["w"], ix["m"], ix["N"], ix["g"] = 0, 0, 0, 0
                rr = int(np.ravel_multi_index(tuple(ix[k] for k in EJES), R.forma))
                respaldo = True
            fila["recetas"][nombre] = {"receta": int(r), "txt": R.receta(r),
                                       "fc": [round(float(x), 1) for x in Fc[rr]], "sin_trend": respaldo}
        filas.append(fila)
    return {"foto": foto.etiqueta, "meses": [int_a_mes(t) for t in M.t_fut], "filas": filas}


# ------------------------------------------------------------------ cubo parquet
def escribir_cubo(res: ResultadoFoto, R: Rejilla, carpeta: Path) -> Path:
    import pyarrow as pa
    import pyarrow.parquet as pq
    foto = res.foto
    d = carpeta / f"casa={foto.casa}" / f"foto={foto.etiqueta}"
    d.mkdir(parents=True, exist_ok=True)
    n, nr, nt = res.abs.shape
    eans = np.array([foto.eans[i] for i in res.scope])
    tabla = pa.table({
        "ean": pa.array(np.repeat(eans, nr * nt)).dictionary_encode(),
        "receta": np.tile(np.repeat(np.arange(nr, dtype=np.int32), nt), n),
        "tramo": np.tile(np.arange(1, nt + 1, dtype=np.int8), n * nr),
        "abs_err": res.abs.reshape(-1),
        "sgn_err": res.sgn.reshape(-1),
        "act": np.broadcast_to(res.act.astype(np.float32)[:, None, :], (n, nr, nt)).reshape(-1),
        "cerrado": np.broadcast_to(res.cerrado[:, None, :], (n, nr, nt)).reshape(-1),
        "valida": np.repeat(res.valido.reshape(-1), nt),
    })
    pq.write_table(tabla, d / "recetas.parquet", compression="zstd")
    pd.DataFrame({"ean": np.repeat(eans, nt), "tramo": np.tile(np.arange(1, nt + 1), n),
                  "cons_abs": res.cons_abs.reshape(-1), "cons_sgn": res.cons_sgn.reshape(-1),
                  "act": res.act.reshape(-1), "cerrado": res.cerrado.reshape(-1)}
                 ).to_parquet(d / "consensus.parquet")
    return d


def tabla_recetas(R: Rejilla) -> pd.DataFrame:
    df = pd.DataFrame({k: np.array(R.valores[k])[R.idx[k]] for k in EJES})
    df["grupo"] = [f"{CELDAS[g][0]} · {CELDAS[g][1]}" for g in df["g"]]
    df.index.name = "receta"
    return df


# ------------------------------------------------------------------ main
def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    sin_cubo = "--sin-cubo" in argv
    argv = [a for a in argv if not a.startswith("--")]
    carpeta = Path(argv[0]) if argv else DATOS
    salida = Path(argv[1]) if len(argv) > 1 else RAIZ / "salida"
    salida.mkdir(parents=True, exist_ok=True)
    cfg = cargar_config()
    R = Rejilla(cfg)
    t0 = time.time()
    archivos = sorted(carpeta.rglob("*_[0-9][0-9][0-9][0-9]_[0-9][0-9].csv"))
    casas = {}
    for a in archivos:
        f = leer_foto(a, cfg)
        casas.setdefault(f.casa, []).append(f)
        print(f"  leída {a.name}: {len(f.eans)} códigos, {int(f.codigos['scope'].sum())} en scope ({time.time()-t0:.1f}s)")
    datos = {"config": cfg, "celdas": CELDAS, "ejes": {k: R.valores[k] for k in EJES if k != "g"},
             "casas": {}}
    for casa, fotos in casas.items():
        fotos.sort(key=lambda f: f.mes)
        # una variante por combinación de tipos ignorados (filtro general de la página);
        # el cubo, los logs y los resúmenes en disco son los de la variante base (no se ignora nada)
        variantes = {}
        for ignorar in variantes_tipos(cfg):
            base = not ignorar
            resultados = []
            for f in fotos:
                res = calcular_foto(f, fotos, cfg, R, ignorar)
                resultados.append(res)
                print(f"  {casa} {f.etiqueta} [{clave_variante(ignorar) or 'todos'}]: {len(res.scope)} códigos × {R.n} recetas; "
                      f"tramos cerrados {res.cerrado.any(0).tolist()} ({time.time()-t0:.1f}s)")
                if base and not sin_cubo:
                    escribir_cubo(res, R, salida / "cubo")
                if base:
                    (salida / "logs").mkdir(exist_ok=True)
                    (salida / "logs" / f"{casa}_{f.etiqueta}_invalidas.json").write_text(
                        json.dumps(res.log, ensure_ascii=False, indent=1), encoding="utf-8")
            resumenes = [resumen_foto(r, cfg, R) for r in resultados]
            elegida, num, sgn, den = score_multifoto(resultados, cfg, R)
            det = detector(resultados[-1], elegida, num, sgn, den, cfg, R)
            variantes[clave_variante(ignorar)] = {"fotos": resumenes, "elegida": elegida, "detector": det}
            if base:
                for rsm in resumenes:
                    (salida / f"resumen_{casa}_{rsm['foto']}.json").write_text(
                        json.dumps(rsm, ensure_ascii=False), encoding="utf-8")
        atributos = {}
        for f in fotos:
            for e, row in f.codigos.iterrows():
                atributos[e] = {"desc": row["Planning Item Description"], "brand": row["Brand"],
                                "pl": row["Product Line"], "segmento": row["Final Segment"],
                                "tamano": row["tamano"], "flag": row["Ignore System Forecast Flag"],
                                "fr": row["Final Responsibility"]}
        # página de inicio: volumen y scope de cada EAN en la foto más actual (incluye los local)
        fu = fotos[-1]
        ult12 = (fu.meses >= fu.mes - 12) & (fu.meses < fu.mes)
        fut = (fu.meses > fu.mes) & (fu.meses <= fu.mes + cfg["horizonte"])
        vol12 = np.nansum(fu.mat["Actuals"][:, ult12], axis=1)
        cons9 = np.nansum(fu.mat["Consensus - Final"][:, fut], axis=1)
        art, resp = clases(fu.codigos)
        inicio = {}
        for i, (e, row) in enumerate(fu.codigos.iterrows()):
            inicio[e] = {"vol12": round(float(vol12[i]), 1), "cons9": round(float(cons9[i]), 1),
                         "scope": bool(row["scope"]), "motivo": row["fuera_scope_motivo"],
                         "edad": row["tramo_edad"], "tipo": row["Article Type"],
                         "art": str(art[i]), "resp": str(resp[i])}
        datos["casas"][casa] = {
            **variantes[""], "variantes": {k: v for k, v in variantes.items() if k},
            "atributos": atributos, "inicio": {"foto": fu.etiqueta, "codigos": inicio},
        }
        print(f"  {casa}: score multi-foto con {len(variantes['']['elegida'])} códigos, "
              f"{len(variantes)} variantes de tipos ({time.time()-t0:.1f}s)")
    tabla_recetas(R).to_csv(salida / "recetas.csv")
    (salida / "datos.json").write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    from interfaz.html import generar_html
    HTML_EJEMPLO.parent.mkdir(parents=True, exist_ok=True)
    ruta = generar_html(datos, HTML_EJEMPLO)
    print(f"HTML: {ruta} ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()
