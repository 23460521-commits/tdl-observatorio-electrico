"""Pruebas del laboratorio de pronostico. Series sinteticas, sin archivos."""

import numpy as np
import pandas as pd
import pytest

from laboratorio import modelos as M


@pytest.fixture
def serie():
    rng = np.random.default_rng(7)
    t = np.arange(132)
    y = 80 * 1.004**t * (1 + 0.02 * np.sin(2 * np.pi * t / 12)) * np.exp(rng.normal(0, 0.003, 132))
    return pd.Series(y, index=pd.date_range("2010-01-01", periods=132, freq="MS"), name="x")


def test_metricas_valores_conocidos():
    m = M.metricas([100, 200], [110, 180])
    assert m["MAE"] == pytest.approx(15) and m["RMSE"] == pytest.approx(np.sqrt(250))
    assert m["MAPE_pct"] == pytest.approx(10)


def test_serie_mensual_exige_meses_completos():
    fechas = pd.to_datetime(["2020-01-01", "2020-02-01", "2020-04-01"])
    t = pd.DataFrame({"ciudad_id": "a", "fecha": fechas, "indice_general": [1.0, 2.0, 3.0]})
    with pytest.raises(ValueError, match="faltantes"):
        M.serie_mensual(t, "a")
    assert len(M.serie_mensual(t.iloc[:2], "a")) == 2


def test_estacionariedad_distingue_caminata_de_ruido():
    rng = np.random.default_rng(3)
    ruido = pd.Series(rng.normal(size=300))
    assert M.pruebas_estacionariedad(ruido, "ruido")["lectura"] == "estacionaria"
    assert M.pruebas_estacionariedad(ruido.cumsum(), "caminata")["lectura"] == "no estacionaria"


def test_fuerza_de_tendencia_y_estacionalidad(serie):
    f = M.fuerza_tendencia_estacionalidad(M.descomponer(serie))
    assert f["tendencia"] > 0.95 and f["estacionalidad"] > 0.8


@pytest.mark.parametrize("nombre", M.MODELOS)
def test_cada_modelo_pronostica_h_meses_futuros(serie, nombre):
    m = M.ajustar(nombre, serie)
    p = m["pronosticar"](6)
    assert len(p) == 6 and np.isfinite(np.asarray(p)).all()
    assert p.index[0] == pd.Timestamp("2021-01-01")
    assert len(m["residuos"]) > 100


def test_modelos_con_tendencia_ganan_al_ingenuo_en_serie_con_tendencia(serie):
    r, _ = M.evaluar_retencion(serie, h=12)
    mape = r.set_index("modelo")["MAPE_pct"]
    assert mape["holt"] < mape["ingenuo"] and mape["holt_winters"] < mape["holt"]
    assert mape["ses"] == pytest.approx(mape["ingenuo"], abs=0.5)


def test_validacion_origen_movil_no_usa_el_futuro(serie):
    vc = M.validacion_origen_movil(serie, horizontes=(1, 3), origenes=4, modelos=["ingenuo"])
    assert len(vc) == 8
    fila = vc[(vc["h"] == 3)].iloc[0]
    assert fila["pronostico"] == pytest.approx(serie[fila["origen"]])  # ultimo valor conocido
    assert fila["real"] == pytest.approx(serie[fila["origen"] + pd.DateOffset(months=3)])
    assert set(M.resumen_validacion(vc).columns) >= {"MAE", "RMSE", "MAPE_pct", "sesgo"}


def test_diagnostico_residuos_ruido_blanco_y_autocorrelacion():
    rng = np.random.default_rng(11)
    e = rng.normal(size=400)
    assert M.diagnostico_residuos(e)["ruido blanco"]
    ar = np.zeros(400)
    for i in range(1, 400):
        ar[i] = 0.8 * ar[i - 1] + e[i]
    assert not M.diagnostico_residuos(ar)["ruido blanco"]


def test_elegir_sarima_devuelve_orden_con_d1_y_sin_diferencia_estacional(serie):
    orden, est, tabla = M.elegir_sarima(serie, max_pq=1)
    assert orden[1] == 1 and est[1] == 0 and est[3] == 12
    assert tabla["AIC"].is_monotonic_increasing
