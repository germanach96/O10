"""Tests del lector y del motor con casos pequeños calculados a mano."""
from pathlib import Path

import numpy as np
import pytest

from brujulas.lector import ErrorFoto, extraer_tamano, leer_foto
from brujulas.motor import CELDAS, EJES, MotorFoto, Rejilla
from brujulas.pipeline import cargar_config, kpis

RAIZ = Path(__file__).resolve().parent.parent
COLS = ("Sub-Division;House;Brand;Product Line;Article Type;Article Sub Type;EAN;Planning Item Description;"
        "Core Category;Sub-Category;Market Category;Fiscal Year;Fiscal Quarter;Month;Final Responsibility;"
        "Ignore System Forecast Flag;System FC - Final;Initiative Forecast;Prometheus Fcst Consensus;EPOS;"
        "Reasonability Adjustment;Total Demand Assumption;Consensus - Final;Actuals;Supply Cuts;Final Segment;Disco Date")


def escribir_csv(ruta, filas, foto="2025.M01"):
    """filas: lista de dicts con ean, mes y valores de columnas."""
    cab = COLS.split(";")
    lineas = [";" * 15 + ";".join([f"S&OP {foto}"] * 12), COLS]
    for f in filas:
        v = {c: "" for c in cab}
        v.update({"House": "Test", "Brand": "B1", "Product Line": "PL1", "Article Type": "Regular Item",
                  "Planning Item Description": f"TEST EDP {f['ean'][-2:]} ML", "Final Segment": "Horses",
                  "Disco Date": "23/12/2030"})
        v.update({k: str(x) for k, x in f.items() if k in cab})
        v["EAN"], v["Month"] = f["ean"], f["mes"]
        lineas.append(";".join(v[c] for c in cab))
    lineas.append(";" * 26)  # fila vacía final
    ruta.write_text("\n".join(lineas), encoding="utf-8-sig")
    return ruta


def mes(a, m):
    return f"{a}.M{m:02d}"


@pytest.fixture
def cfg():
    return cargar_config()


@pytest.fixture
def foto_simple(tmp_path, cfg):
    """Código 1: 100/mes en 2023, 110/mes en 2024, un corte de 12 en 2024.M06, DA de 5 en 2025.M02 (h=1).
    Código 2: 50/mes en 2023 y 2024 (mismo PL)."""
    filas = []
    for a in (2022, 2023, 2024):
        for m in range(1, 13):
            v1 = {2022: 100, 2023: 100, 2024: 110}[a]
            f1 = {"ean": "1000000000050", "mes": mes(a, m), "Actuals": v1, "Consensus - Final": v1}
            if (a, m) == (2024, 6):
                f1["Supply Cuts"] = 12
            filas.append(f1)
            filas.append({"ean": "2000000000030", "mes": mes(a, m), "Actuals": 50, "Consensus - Final": 50})
    for m in range(1, 11):
        filas.append({"ean": "1000000000050", "mes": mes(2025, m), "Consensus - Final": 120,
                      **({"Total Demand Assumption": 5} if m == 2 else {})})
        filas.append({"ean": "2000000000030", "mes": mes(2025, m), "Consensus - Final": 50})
    return leer_foto(escribir_csv(tmp_path / "Test_2025_01.csv", filas), cfg)


def indice(R, **v):
    ix = []
    for k in EJES:
        if k == "g":
            ix.append(CELDAS.index(v["g"]))
        else:
            ix.append(R.valores[k].index(v[k]))
    return int(np.ravel_multi_index(tuple(ix), R.forma))


def test_tamano():
    assert extraer_tamano("GUCCI BM EDP 100 ML IV") == "100 ML"
    assert extraer_tamano("GUCCI LUX SMLL EDP 50ml OSMANTHUS IV") == "50 ML"
    assert extraer_tamano("GUCCI BM FIOR RG EDP RB 7.4ml 18 IV") == "7.4 ML"
    assert extraer_tamano("GUCCI GUILT H EDT NS 200MLIV") == "200 ML"
    assert extraer_tamano("BLUSH 3.5 G") == "3.5 G"
    assert extraer_tamano("GUCCI LUX EDP100 GLOAMING NIGHT VP IV") == "100 ML"


def test_ean_cientifico(tmp_path, cfg):
    ruta = escribir_csv(tmp_path / "Test_2025_01.csv",
                        [{"ean": "3.61423E+12", "mes": "2024.M01", "Actuals": 1}])
    with pytest.raises(ErrorFoto, match="científica"):
        leer_foto(ruta, cfg)


def test_lectura_y_scope(foto_simple):
    f = foto_simple
    assert f.etiqueta == "2025.M01"
    assert len(f.eans) == 2
    c = f.codigos
    assert c["scope"].all()
    assert set(c["tramo_edad"]) == {"Año 3+"}       # vendía desde el primer mes de la historia
    assert c.loc["1000000000050", "tamano"] == "50 ML"


def test_forecast_a_mano(foto_simple, cfg):
    R = Rejilla(cfg)
    M = MotorFoto(foto_simple, cfg, R)
    i = foto_simple.eans.index("1000000000050")
    Fc, val = M.forecasts(i)
    # media plana 110, trend propio 12M = 1320/1200 − 1 = +10%, DA 5 en el mes 1 (2025.M02)
    r = indice(R, s=0, w=1, m=0, N=12, c=0, p=0, g=("Propio", "Jerarquía"))
    assert val[r]
    np.testing.assert_allclose(Fc[r][:3], [126, 121, 121])  # 2025.M02 = h1
    # cortes: c=1 suma 12 a 2024.M06 -> media (1320+12)/12 = 111, trend (1332/1200 − 1) = 11%
    r = indice(R, s=0, w=1, m=0, N=12, c=1, p=0, g=("Propio", "Jerarquía"))
    np.testing.assert_allclose(Fc[r][1], 111 * 1.11)
    # sin trend, 100% estacional: H(2024.M02) = 110 (+5 de DA en el mes 1)
    r = indice(R, s=1, w=0, m=0, N=6, c=0, p=0, g=("Propio", "Jerarquía"))
    np.testing.assert_allclose(Fc[r][:2], [115, 110])
    # trend de la Product Line (ambos códigos), N=12: (1320+600)/(1200+600) − 1 = 6.67%
    r = indice(R, s=0, w=1, m=0, N=12, c=0, p=0, g=("Product Line", "Jerarquía"))
    np.testing.assert_allclose(Fc[r][1], 110 * (1 + 120 / 1800))
    # sin EPOS: m>0 con trend no es válida; con w=0 sí
    assert not val[indice(R, s=0, w=1, m=0.5, N=12, c=0, p=0, g=("Propio", "Jerarquía"))]
    assert val[indice(R, s=0, w=0, m=0.5, N=12, c=0, p=0, g=("Propio", "Jerarquía"))]


def test_tope_trend(tmp_path, cfg):
    filas = []
    for a in (2023, 2024):
        for m in range(1, 13):
            v = 100 if a == 2023 else 200       # +100% -> recortado a +30%
            filas.append({"ean": "1000000000050", "mes": mes(a, m), "Actuals": v})
    filas.append({"ean": "1000000000050", "mes": "2025.M05", "Consensus - Final": 1})
    f = leer_foto(escribir_csv(tmp_path / "Test_2025_01.csv", filas), cfg)
    R = Rejilla(cfg)
    Fc, _ = MotorFoto(f, cfg, R).forecasts(0)
    r = indice(R, s=0, w=1, m=0, N=12, c=0, p=0, g=("Propio", "Jerarquía"))
    np.testing.assert_allclose(Fc[r][0], 200 * 1.3)


def test_kpis_grupo(cfg):
    # dos códigos a −5% y +5% (100 de actual cada uno): Σ|e| = 10, ΣA = 200 -> WAPE 5%, SPP 0
    abs_t = np.array([10.0, 0, 0]); sgn_t = np.array([0.0, 0, 0]); act = np.array([200.0, 0, 0])
    k = kpis(abs_t, sgn_t, act, cfg)
    assert k["90"]["wape"] == pytest.approx(0.05) and k["90"]["spp"] == 0
    # signo: forecast por encima del actual = sobre-forecast = SPP negativo
    k = kpis(np.array([20.0, 0, 0]), np.array([20.0, 0, 0]), np.array([100.0, 0, 0]), cfg)
    assert k["90"]["spp"] == pytest.approx(-0.2)


@pytest.mark.skipif(not (RAIZ / "Gucci_2025_11.csv").exists(), reason="sin CSV de ejemplo")
def test_csv_gucci(cfg):
    f = leer_foto(RAIZ / "Gucci_2025_11.csv", cfg)
    assert f.etiqueta == "2025.M11"
    assert f.codigos["scope"].sum() > 100
    assert not f.codigos.loc[f.codigos["Article Type"] == "One Shot/Promo", "scope"].any()
