"""Tests del lector y del motor con casos pequeños calculados a mano."""
from pathlib import Path

import numpy as np
import pytest

from motor.lector import ErrorFoto, agregar_desaparecidos, extraer_tamano, leer_foto, leer_listas, mes_a_int
from motor.recetas import CELDAS, EJES, MotorFoto, Rejilla
from motor.pipeline import actuals_futuros, cargar_config, kpis, mascara_cuenta, variantes_tipos

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
            ix.append(R.valores[k].index(v.get(k, R.valores[k][0])))
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
    # sin trend, 100% estacional de 1 año: H(2024.M02) = 110 (+5 de DA en h1)
    r = indice(R, s=1, e=1, w=0, m=0, N=6, c=0, p=0, g=("Propio", "Jerarquía"))
    np.testing.assert_allclose(Fc[r][:2], [115, 110])
    # de 2 años: (H(2024.M02) + H(2023.M02)) / 2 = (110 + 100) / 2 = 105
    r = indice(R, s=1, e=2, w=0, m=0, N=6, c=0, p=0, g=("Propio", "Jerarquía"))
    np.testing.assert_allclose(Fc[r][:2], [110, 105])
    # 50% estacional de 2 años: 0.5·110 + 0.5·105
    r = indice(R, s=0.5, e=2, w=0, m=0, N=6, c=0, p=0, g=("Propio", "Jerarquía"))
    np.testing.assert_allclose(Fc[r][1], 107.5)
    # trend de la Product Line (ambos códigos), N=12: (1320+600)/(1200+600) − 1 = 6.67%
    r = indice(R, s=0, w=1, m=0, N=12, c=0, p=0, g=("Product Line", "Jerarquía"))
    np.testing.assert_allclose(Fc[r][1], 110 * (1 + 120 / 1800))
    # sin EPOS: m>0 con trend no es válida; con w=0 sí
    assert not val[indice(R, s=0, w=1, m=0.5, N=12, c=0, p=0, g=("Propio", "Jerarquía"))]
    assert val[indice(R, s=0, w=0, m=0.5, N=12, c=0, p=0, g=("Propio", "Jerarquía"))]


def test_filtro_tipos(foto_simple, cfg):
    """Un tipo ignorado no suma en el trend de grupo: sin el código 2 (Local), la PL vale lo mismo que el propio."""
    f = foto_simple
    f.codigos.loc["2000000000030", "Final Responsibility"] = "Local"
    assert mascara_cuenta(f.codigos).all()
    cuenta = mascara_cuenta(f.codigos, ["Local"])
    assert cuenta.tolist() == [f.eans[k] != "2000000000030" for k in range(2)]
    assert not mascara_cuenta(f.codigos, ["Regular"]).any()
    R = Rejilla(cfg)
    M = MotorFoto(f, cfg, R, cuenta=cuenta)
    i = f.eans.index("1000000000050")
    Fc, _ = M.forecasts(i)
    r = indice(R, s=0, w=1, m=0, N=12, c=0, p=0, g=("Product Line", "Jerarquía"))
    np.testing.assert_allclose(Fc[r][1], 110 * 1.10)
    assert M.tam_grupo[CELDAS.index(("Product Line", "Jerarquía")), i] == 1
    assert len(variantes_tipos(cfg)) == 4


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


CSV_GUCCI = RAIZ / "data" / "Gucci" / "Consensus" / "Gucci_2025_11.csv"


def test_actuals_de_codigos_que_salen_del_export(tmp_path, foto_simple, cfg):
    """Foto 2025.M01. La foto 2025.M03 trae los dos códigos; la 2025.M05 ya no trae el código 1.
    Código 1: feb sale de 2025.M03 (la más reciente que lo tiene); mar y abr = 0 (fuera del export);
    may en adelante sigue abierto. Código 2: feb–abr de 2025.M05."""
    def foto_posterior(nombre, mes_foto, eans):
        filas = []
        for e in eans:
            for a in (2022, 2023, 2024, 2025):
                for m in range(1, 13):
                    if (a, m) < (2025, mes_foto):
                        v = 30 + m if e.startswith("1") else 50 + m
                        filas.append({"ean": e, "mes": mes(a, m), "Actuals": v, "Consensus - Final": v})
                    else:
                        filas.append({"ean": e, "mes": mes(a, m), "Consensus - Final": 40})
        d = tmp_path / nombre
        d.mkdir()
        return leer_foto(escribir_csv(d / f"Test_2025_{mes_foto:02d}.csv", filas, f"2025.M{mes_foto:02d}"), cfg)
    p3 = foto_posterior("p3", 3, ["1000000000050", "2000000000030"])
    p5 = foto_posterior("p5", 5, ["2000000000030"])
    A = actuals_futuros(foto_simple, [foto_simple, p3, p5], cfg["horizonte"])
    i1, i2 = foto_simple.eans.index("1000000000050"), foto_simple.eans.index("2000000000030")
    np.testing.assert_array_equal(A[i1, :3], [32, 0, 0])
    np.testing.assert_array_equal(A[i2, :3], [52, 53, 54])
    assert np.isnan(A[:, 3:]).all()


def test_codigo_desaparecido_cuenta_en_el_trend(tmp_path, foto_simple, cfg):
    """El código 1 (100/mes en 2023, 110/mes en 2024) sale del export en la foto 2026.M01; el código 2 (mismo PL)
    vende 50/mes siempre. En 2026.M01 el código 1 sigue en el grupo con su historia y 0 en 2025:
    T(PL, N=12) = (0 + 600) / (1320 + 600) − 1 = −0.6875. No entra en el scope ni en el nº de códigos."""
    filas = [{"ean": "2000000000030", "mes": mes(a, m), "Actuals": 50, "Consensus - Final": 50}
             for a in (2022, 2023, 2024, 2025) for m in range(1, 13)]
    filas += [{"ean": "2000000000030", "mes": mes(2026, m), "Consensus - Final": 50} for m in range(1, 11)]
    d = tmp_path / "b"
    d.mkdir()
    b = leer_foto(escribir_csv(d / "Test_2026_01.csv", filas, "2026.M01"), cfg)
    agregar_desaparecidos([foto_simple, b])
    assert b.eans == ["2000000000030", "1000000000050"]
    assert b.codigos["fantasma"].tolist() == [False, True] and not b.codigos["scope"].iat[1]
    h = b.mat["hist"][1]
    assert h[b.col(mes_a_int("2024.M06"))] == 110 and h[b.col(mes_a_int("2025.M06"))] == 0
    assert np.isnan(b.mat["Consensus - Final"][1, b.col(mes_a_int("2026.M03"))])
    R = Rejilla(cfg)
    M = MotorFoto(b, cfg, R)
    gi, ni = CELDAS.index(("Product Line", "Jerarquía")), R.valores["N"].index(12)
    assert M.T_si[gi, ni, 0, 0, 0] == pytest.approx(600 / 1920 - 1)
    assert M.tam_grupo[gi, 0] == 1


def test_trend_sellout_por_meses_del_grupo(tmp_path, cfg):
    """Foto 2025.M01, PL con dos códigos. A: EPOS 100 en 2023 (salvo M08) y en 2024 (salvo M12, aún no cargado).
    B (nuevo): EPOS 50 solo en 2024 (salvo M12). N=6 (2024.M07–M12): M12 fuera (sin EPOS), M08 fuera (sin EPOS
    hace un año). Quedan M07, M09, M10, M11: (4·150) / (4·100) − 1 = +50%."""
    filas = []
    for a in (2022, 2023, 2024):
        for m in range(1, 13):
            fa = {"ean": "1000000000050", "mes": mes(a, m), "Actuals": 100, "Consensus - Final": 100}
            fb = {"ean": "2000000000050", "mes": mes(a, m), "Actuals": 50, "Consensus - Final": 50}
            if (a == 2023 and m != 8) or (a == 2024 and m != 12):
                fa["EPOS"] = 100
            if a == 2024 and m != 12:
                fb["EPOS"] = 50
            filas += [fa, fb]
    for m in range(1, 11):
        filas += [{"ean": e, "mes": mes(2025, m), "Consensus - Final": 80} for e in ("1000000000050", "2000000000050")]
    f = leer_foto(escribir_csv(tmp_path / "Test_2025_01.csv", filas), cfg)
    R = Rejilla(cfg)
    M = MotorFoto(f, cfg, R)
    gi, ni = CELDAS.index(("Product Line", "Jerarquía")), R.valores["N"].index(6)
    assert M.T_so[gi, ni, 0] == pytest.approx(0.5)


@pytest.mark.skipif(not CSV_GUCCI.exists(), reason="sin CSV de ejemplo")
def test_csv_gucci(cfg):
    f = leer_foto(CSV_GUCCI, cfg)
    assert f.etiqueta == "2025.M11"
    assert f.codigos["scope"].sum() > 100
    assert not f.codigos.loc[f.codigos["Article Type"] == "One Shot/Promo", "scope"].any()


def test_listas_de_filtros(tmp_path):
    ruta = tmp_path / "filters.csv"
    ruta.write_text("\ufeffRevenue Leaders;GUMU  Selected ;Vacía\r\n0001;0101;\r\n0002;0102;\r\n0001;;\r\n;0103;\r\n",
                    encoding="utf-8")
    listas = leer_listas(ruta)
    assert [l["nombre"] for l in listas] == ["Revenue Leaders", "GUMU Selected", "Vacía"]
    # EAN como texto (conserva los ceros a la izquierda), sin vacíos ni repetidos
    assert listas[0]["eans"] == ["0001", "0002"]
    assert listas[1]["eans"] == ["0101", "0102", "0103"]
    assert listas[2]["eans"] == []
    assert leer_listas(tmp_path / "no_existe.csv") == []
    ruta.write_text("L1\n3.61423E+12\n", encoding="utf-8")
    with pytest.raises(ErrorFoto, match="notación científica"):
        leer_listas(ruta)


def test_listas_del_repo():
    listas = leer_listas(RAIZ / "data" / "filters.csv")
    assert len(listas) == 5 and all(l["eans"] for l in listas)
