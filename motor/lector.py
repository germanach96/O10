"""Lector y validador de fotos S&OP (un CSV por casa y foto mensual)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

COLUMNAS_NUM = [
    "System FC - Final", "Initiative Forecast", "Prometheus Fcst Consensus", "EPOS",
    "Reasonability Adjustment", "Total Demand Assumption", "Consensus - Final",
    "Actuals", "Supply Cuts",
]
COLUMNAS_OBLIGATORIAS = [
    "House", "Brand", "Product Line", "Article Type", "EAN", "Planning Item Description",
    "Month", "Final Responsibility", "Ignore System Forecast Flag", "EPOS",
    "Total Demand Assumption", "Consensus - Final", "Actuals", "Supply Cuts",
    "Final Segment", "Disco Date",
]
TRAMOS_EDAD = ["A1 1-6", "A1 7-12", "Año 2", "Año 3+", "Pre-disco"]


class ErrorFoto(ValueError):
    pass


def mes_a_int(m: str) -> int:
    """'2026.M04' -> índice entero de mes (año*12 + mes-1)."""
    mm = re.fullmatch(r"\s*(\d{4})\.M(\d{2})\s*", str(m))
    if not mm:
        raise ErrorFoto(f"Mes con formato inesperado: {m!r}")
    return int(mm.group(1)) * 12 + int(mm.group(2)) - 1


def int_a_mes(i: int) -> str:
    return f"{i // 12}.M{i % 12 + 1:02d}"


def extraer_tamano(desc: str) -> str:
    """Tamaño normalizado desde la descripción: '50 ML', '7.4 ML', '3.5 G'. 'N/D' si no hay."""
    d = str(desc).upper().replace(",", ".")
    m = re.search(r"(\d+(?:\.\d+)?)\s*(ML|GR|G)(?:\b|(?=IV\b))", d)
    if not m:
        # 'EDP100', 'EDP30' sin unidad: en fragancias es ml
        m2 = re.search(r"\b(?:EDP|EDT|EDC|PRM)\s?(\d{2,3})\b", d)
        if m2:
            return f"{int(m2.group(1))} ML"
        return "N/D"
    num = float(m.group(1))
    num_txt = f"{num:g}"
    unidad = "G" if m.group(2) in ("G", "GR") else "ML"
    return f"{num_txt} {unidad}"


@dataclass
class Foto:
    casa: str
    mes: int                      # mes de la foto (índice entero)
    archivo: str
    df: pd.DataFrame              # filas limpias
    codigos: pd.DataFrame         # una fila por EAN con atributos
    meses: np.ndarray             # rango de meses de las matrices
    mat: dict = field(default_factory=dict)   # columna -> matriz (códigos × meses), NaN = sin dato
    primer_mes_actuals: int = 0   # primer mes con Actuals en el archivo (ventana de actuals)
    avisos: list = field(default_factory=list)

    @property
    def etiqueta(self) -> str:
        return int_a_mes(self.mes)

    def col(self, t: int) -> int:
        return t - int(self.meses[0])


def leer_foto(ruta: str | Path, cfg: dict) -> Foto:
    ruta = Path(ruta)
    m = re.fullmatch(r"(.+)_(\d{4})_(\d{2})\.csv", ruta.name)
    if not m:
        raise ErrorFoto(f"Nombre de archivo inesperado (Casa_AAAA_MM.csv): {ruta.name}")
    casa = m.group(1).replace("_", " ")  # 'Kylie_MU_2026_04.csv' -> casa 'Kylie MU' (como su carpeta)
    mes_nombre = int(m.group(2)) * 12 + int(m.group(3)) - 1

    with open(ruta, encoding="utf-8-sig") as fh:
        cab1 = fh.readline()
    sop = re.findall(r"S&OP (\d{4}\.M\d{2})", cab1)
    if sop:
        mes_cab = mes_a_int(sop[0])
        if mes_cab != mes_nombre:
            raise ErrorFoto(f"{ruta.name}: el mes de la cabecera ({sop[0]}) no coincide con el del nombre")
    df = pd.read_csv(ruta, sep=";", encoding="utf-8-sig", skiprows=1, dtype=str, keep_default_na=False)
    df = df.replace("", np.nan)
    df = df.dropna(how="all")  # filas vacías del final
    faltan = [c for c in COLUMNAS_OBLIGATORIAS if c not in df.columns]
    if faltan:
        raise ErrorFoto(f"{ruta.name}: faltan columnas {faltan}")
    df = df[df["EAN"].notna()].copy()

    # --- validación del EAN (texto) ---
    df["EAN"] = df["EAN"].str.strip()
    cient = df["EAN"].str.contains(r"[eE]\+|\.", regex=True)
    if cient.any():
        raise ErrorFoto(
            f"{ruta.name}: hay EANs en notación científica (p. ej. {df.loc[cient, 'EAN'].iloc[0]}). "
            "Reexportar con el EAN como texto.")
    n_ean, n_desc = df["EAN"].nunique(), df["Planning Item Description"].nunique()
    if n_ean < n_desc:
        raise ErrorFoto(f"{ruta.name}: {n_ean} EANs distintos para {n_desc} descripciones; el EAN no sirve como clave.")
    if df.duplicated(["EAN", "Month"]).any():
        raise ErrorFoto(f"{ruta.name}: filas duplicadas EAN × mes")

    for c in COLUMNAS_NUM:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="raise")
    df["t"] = df["Month"].map(mes_a_int)

    foto = Foto(casa=casa, mes=mes_nombre, archivo=ruta.name, df=df, codigos=None, meses=None)
    _matrices(foto, cfg)
    _atributos(foto, cfg)
    return foto


def _matrices(foto: Foto, cfg: dict) -> None:
    df = foto.df
    eans = sorted(df["EAN"].unique())
    t0, t1 = int(df["t"].min()), int(df["t"].max())
    foto.meses = np.arange(t0, t1 + 1)
    fila = {e: i for i, e in enumerate(eans)}
    r = df["EAN"].map(fila).to_numpy()
    k = (df["t"] - t0).to_numpy()
    for c in ["Actuals", "Supply Cuts", "Total Demand Assumption", "EPOS", "Consensus - Final"]:
        M = np.full((len(eans), len(foto.meses)), np.nan)
        M[r, k] = df[c].to_numpy(dtype=float)
        foto.mat[c] = M
    foto.eans = eans

    act = df.loc[df["Actuals"].notna(), "t"]
    if act.empty:
        raise ErrorFoto(f"{foto.archivo}: no hay Actuals")
    foto.primer_mes_actuals = int(act.min())

    # Historia de sell-in: Actuals (vacío dentro de la ventana de actuals = 0 ventas).
    A = foto.mat["Actuals"].copy()
    ventana = (foto.meses >= foto.primer_mes_actuals) & (foto.meses < foto.mes)
    A[:, ventana] = np.nan_to_num(A[:, ventana])
    if cfg.get("historia_desde_consensus_pasado", True):
        # Antes del primer mes con Actuals: Consensus pasado = Actuals (demand control)
        antes = foto.meses < foto.primer_mes_actuals
        C = foto.mat["Consensus - Final"][:, antes]
        A[:, antes] = C
        hay = ~np.isnan(foto.mat["Consensus - Final"][:, antes]).all(axis=0)
        if hay.any():
            foto.inicio_historia = int(foto.meses[antes][hay.argmax()])
        else:
            foto.inicio_historia = foto.primer_mes_actuals
    else:
        foto.inicio_historia = foto.primer_mes_actuals
    hist = foto.meses >= foto.inicio_historia
    A[:, hist & (foto.meses < foto.mes)] = np.nan_to_num(A[:, hist & (foto.meses < foto.mes)])
    foto.mat["hist"] = A  # NaN fuera de la historia útil


def _atributos(foto: Foto, cfg: dict) -> None:
    df = foto.df
    attrs = (df.sort_values("t").groupby("EAN", sort=True)
             .agg({"Brand": "first", "Product Line": "first", "House": "first", "Article Type": "first",
                   "Planning Item Description": "first", "Final Responsibility": "first",
                   "Ignore System Forecast Flag": "first", "Final Segment": "first", "Disco Date": "first"}))
    attrs = attrs.reindex(foto.eans)
    attrs["Final Segment"] = attrs["Final Segment"].fillna("")
    attrs["Final Responsibility"] = attrs["Final Responsibility"].fillna("")
    attrs["Ignore System Forecast Flag"] = attrs["Ignore System Forecast Flag"].fillna("")
    attrs["tamano"] = attrs["Planning Item Description"].map(extraer_tamano)
    # Maquillaje: va por shade, no por tamaño; por ahora todos sus códigos en un solo grupo
    tm = cfg.get("tamano_maquillaje", {})
    if tm and foto.casa.endswith(tm.get("sufijo_casa", " MU")):
        attrs["tamano"] = tm.get("etiqueta", "Make up")

    # --- Disco Date real o por defecto ---
    defecto = set(cfg.get("fechas_disco_por_defecto", []))
    frac = attrs["Disco Date"].value_counts(normalize=True)
    umbral = cfg.get("disco_por_defecto_si_cubre_mas_de", 1.0)
    for fecha, f in frac.items():
        if f > umbral and fecha not in defecto:
            defecto.add(fecha)
            foto.avisos.append(f"Disco Date {fecha} is used by {f:.0%} of the codes: treated as the default value")
    def disco_mes(d):
        if not isinstance(d, str) or d in defecto:
            return np.nan
        dd, mm, aa = d.split("/")
        return int(aa) * 12 + int(mm) - 1
    attrs["disco_mes"] = attrs["Disco Date"].map(disco_mes)

    # --- Edad: desde el primer mes con historia > 0 ---
    H = foto.mat["hist"]
    pasado = foto.meses < foto.mes
    Hp = np.nan_to_num(H[:, pasado])
    vende = Hp > 0
    primer = np.where(vende.any(axis=1), foto.meses[pasado][vende.argmax(axis=1)], -1)
    attrs["primer_mes_venta"] = primer
    edad = np.where(primer >= 0, foto.mes - primer + 1, 0)
    desconocida = primer == foto.inicio_historia
    attrs["edad_meses"] = edad
    attrs["edad_desconocida"] = desconocida

    def tramo(i):
        dm = attrs["disco_mes"].iat[i]
        if not np.isnan(dm) and foto.mes >= dm - 12:
            return "Pre-disco"
        if desconocida[i]:
            return "Año 3+"
        e = edad[i]
        if e <= 0:
            return "Sin ventas"
        if e <= 6:
            return "A1 1-6"
        if e <= 12:
            return "A1 7-12"
        if e <= 24:
            return "Año 2"
        return "Año 3+"
    attrs["tramo_edad"] = [tramo(i) for i in range(len(attrs))]

    # --- Scope ---
    reg = attrs["Article Type"].eq("Regular Item")
    central = attrs["Final Responsibility"].isin(["Central", ""])
    edad_ok = ~attrs["tramo_edad"].isin(["A1 1-6", "Sin ventas"])
    ult12 = (foto.meses >= foto.mes - 12) & (foto.meses < foto.mes)
    vivo_hist = np.nansum(H[:, ult12], axis=1) > 0
    fut = (foto.meses > foto.mes) & (foto.meses <= foto.mes + cfg["horizonte"])
    vivo_fut = np.nansum(foto.mat["Consensus - Final"][:, fut], axis=1) > 0
    attrs["activo"] = vivo_hist | vivo_fut
    attrs["scope"] = reg & central & edad_ok & attrs["activo"]
    motivo = np.select(
        [~reg, ~central, attrs["tramo_edad"].eq("A1 1-6").to_numpy(), attrs["tramo_edad"].eq("Sin ventas").to_numpy(), ~attrs["activo"]],
        ["One Shot/Promo", "Local", "Innovación meses 1-6", "Sin ventas aún", "Inactivo (sin ventas 12M ni forecast)"],
        default="")
    attrs["fuera_scope_motivo"] = motivo
    foto.codigos = attrs


def leer_listas(ruta: Path) -> list[dict]:
    """Listas de EANs para los filtros de selección de la página (data/filters.csv).

    Una columna = una lista: la cabecera es el nombre y debajo van sus EANs, como texto. Separador ";" y UTF-8 con BOM,
    igual que las fotos. Las columnas pueden tener largos distintos (celdas vacías al final). Los EANs que no estén en
    ninguna casa no molestan: la página solo usa los que encuentra.
    """
    ruta = Path(ruta)
    if not ruta.exists():
        return []
    df = pd.read_csv(ruta, sep=";", dtype=str, encoding="utf-8-sig", keep_default_na=False)
    listas = []
    for col in df.columns:
        nombre = " ".join(str(col).split())
        if not nombre or nombre.lower().startswith("unnamed"):
            continue
        eans = [e.strip() for e in df[col] if e.strip()]
        malos = [e for e in eans if re.search(r"[eE]\+|\.", e)]
        if malos:
            raise ErrorFoto(f"{ruta.name}: la lista «{nombre}» tiene EANs en notación científica (p. ej. {malos[0]}). "
                            "Reexportar con el EAN como texto.")
        listas.append({"nombre": nombre, "eans": list(dict.fromkeys(eans))})
    return listas


def agregar_desaparecidos(fotos: list[Foto]) -> None:
    """Añade a cada foto, como «fantasmas», los códigos de fotos anteriores que ya no salen en ella.

    Un código que sale del export (por ejemplo, una línea de Flora discontinuada) sigue contando en los trends de
    sus grupos: su historia se copia de la foto anterior y los meses desde que desapareció hasta la foto valen 0.
    No tiene forecast futuro, no entra en el scope ni en el mapa, y no suma en el nº de códigos de los grupos.
    Las fotos se procesan en orden: la foto anterior ya trae todos los códigos vistos hasta entonces.
    """
    fotos = sorted(fotos, key=lambda f: f.mes)
    for prev, P in zip(fotos, fotos[1:]):
        presentes = set(P.eans)
        fant = [e for e in prev.eans if e not in presentes]
        if not fant:
            continue
        fila_prev = {e: k for k, e in enumerate(prev.eans)}
        rp = np.array([fila_prev[e] for e in fant])
        n = len(fant)
        # meses de P: < prev.mes -> dato de la foto anterior; [prev.mes, P.mes) -> 0; >= P.mes -> sin dato
        k_prev = P.meses - int(prev.meses[0])
        en_prev = (P.meses < prev.mes) & (k_prev >= 0) & (k_prev < len(prev.meses))
        hueco = (P.meses >= prev.mes) & (P.meses < P.mes)
        for c, M in P.mat.items():
            G = np.full((n, len(P.meses)), np.nan)
            G[:, en_prev] = prev.mat[c][rp][:, k_prev[en_prev]]
            G[:, hueco] = 0.0
            if c == "EPOS":   # 0 solo en los meses en que la foto tiene EPOS cargado
                G[:, hueco & np.isnan(M).all(axis=0)] = np.nan
            if c == "hist":   # misma regla que los códigos reales: dentro de la historia útil, vacío = 0
                util = (P.meses >= P.inicio_historia) & (P.meses < P.mes)
                G[:, util] = np.nan_to_num(G[:, util])
                G[:, ~util] = np.nan
            P.mat[c] = np.vstack([M, G])
        filas = prev.codigos.loc[fant].copy()
        filas["scope"] = False
        filas["activo"] = False
        filas["fuera_scope_motivo"] = "Fuera del export"
        filas["fantasma"] = True
        cod = P.codigos.copy()
        cod["fantasma"] = cod.get("fantasma", False)
        P.codigos = pd.concat([cod, filas])
        P.eans = list(P.eans) + fant
        P.avisos.append(f"{n} codes no longer in the export count in group trends with their past history (0 after they left)")
    for f in fotos:
        if "fantasma" not in f.codigos:
            f.codigos["fantasma"] = False
        f.codigos["fantasma"] = f.codigos["fantasma"].fillna(False).astype(bool)
