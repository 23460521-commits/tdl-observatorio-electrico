"""Laboratorio estadistico: pronostico del indice de costo de construccion.

Funciones puras sobre una serie mensual (pd.Series con indice de fechas, frecuencia MS).
El cuaderno docs/E1/pronostico.ipynb las usa y muestra la evidencia.

Modelos comparados (los cuatro de la rubrica mas dos de referencia):
  ingenuo, deriva            referencias: un modelo que no les gana no sirve
  suavizamiento simple (SES) nivel
  Holt                       nivel + tendencia
  Holt-Winters               nivel + tendencia + estacionalidad (12 meses)
  SARIMA                     sobre el logaritmo; ordenes elegidos por AIC
"""

import itertools
import warnings

import numpy as np
import pandas as pd
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.stats.stattools import jarque_bera
from statsmodels.tools.sm_exceptions import ConvergenceWarning
from statsmodels.tsa.holtwinters import ExponentialSmoothing, SimpleExpSmoothing
from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller, kpss

PERIODO = 12
MODELOS = ["ingenuo", "deriva", "ses", "holt", "holt_winters", "sarima"]
ETIQUETA = {
    "ingenuo": "Ingenuo (último valor)",
    "deriva": "Deriva (referencia)",
    "ses": "Suavizamiento simple",
    "holt": "Holt",
    "holt_winters": "Holt-Winters",
    "sarima": "SARIMA",
}


def serie_mensual(tabla, ciudad_id, columna="indice_general"):
    """Extrae una serie de data/oro/obraprecio_ciudad_mensual.csv con frecuencia mensual."""
    d = tabla[tabla["ciudad_id"] == ciudad_id].sort_values("fecha")
    s = pd.Series(d[columna].to_numpy(), index=pd.DatetimeIndex(d["fecha"]), name=ciudad_id)
    s = s.asfreq("MS")
    if s.isna().any():
        raise ValueError(f"La serie {ciudad_id}/{columna} tiene meses faltantes")
    return s


# --- Caracterizacion -------------------------------------------------------------------
def descomponer(s):
    """STL robusta sobre el logaritmo (los cambios del indice son proporcionales)."""
    return STL(np.log(s), period=PERIODO, robust=True).fit()


def fuerza_tendencia_estacionalidad(stl):
    """Fuerzas de Wang, Smith y Hyndman (0 = nula, 1 = total)."""
    r, t, e = stl.resid, stl.trend, stl.seasonal
    ft = max(0.0, 1 - np.var(r) / np.var(t + r))
    fe = max(0.0, 1 - np.var(r) / np.var(e + r))
    return {"tendencia": float(ft), "estacionalidad": float(fe)}


# --- Estacionariedad ----------------------------------------------------------------------
def pruebas_estacionariedad(s, nombre):
    """ADF (H0: raiz unitaria) y KPSS (H0: estacionaria). Se leen juntas."""
    s = s.dropna()
    adf = adfuller(s, autolag="AIC")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # KPSS avisa cuando p queda fuera de su tabla
        kp = kpss(s, regression="c", nlags="auto")
    estacionaria_adf, estacionaria_kpss = adf[1] < 0.05, kp[1] >= 0.05
    if estacionaria_adf and estacionaria_kpss:
        lectura = "estacionaria"
    elif not estacionaria_adf and not estacionaria_kpss:
        lectura = "no estacionaria"
    else:
        lectura = "las pruebas no coinciden"
    return {
        "serie": nombre, "n": len(s), "ADF": adf[0], "p ADF": adf[1],
        "KPSS": kp[0], "p KPSS": kp[1], "lectura": lectura,
    }  # fmt: skip


# --- Modelos ------------------------------------------------------------------------------
def elegir_sarima(entrenamiento, max_pq=2):
    """Busca (p,1,q)(P,0,Q)12 sobre log(y) por AIC. Devuelve (orden, estacional, tabla).

    d = 1 y D = 0 se fijan con las pruebas de estacionariedad (la primera diferencia del
    logaritmo ya es estacionaria y la estacionalidad es debil), asi todos los candidatos
    usan la misma diferenciacion y su AIC es comparable.
    """
    y, filas = np.log(entrenamiento), []
    for p, q, P, Q in itertools.product(range(max_pq + 1), range(max_pq + 1), (0, 1), (0, 1)):
        orden, est = (p, 1, q), (P, 0, Q, PERIODO)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                m = SARIMAX(y, order=orden, seasonal_order=est, trend="c").fit(
                    disp=False, maxiter=200
                )
            if m.mle_retvals.get("converged", True):
                filas.append({"orden": orden, "estacional": est[:3], "AIC": m.aic, "BIC": m.bic})
        except (ValueError, np.linalg.LinAlgError):
            continue
    tabla = pd.DataFrame(filas).sort_values("AIC").reset_index(drop=True)
    return tabla.iloc[0]["orden"], (*tabla.iloc[0]["estacional"], PERIODO), tabla


def ajustar(nombre, entrenamiento, sarima=((1, 1, 0), (0, 0, 0, PERIODO))):
    """Ajusta un modelo. Devuelve dict con `pronosticar(h)`, residuos, parametros y n_param."""
    y = entrenamiento
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        warnings.simplefilter("ignore", UserWarning)
        if nombre == "ingenuo":
            return {
                "pronosticar": lambda h: _futuro(y, h, np.repeat(y.iloc[-1], h)),
                "residuos": y.diff().dropna(), "parametros": {}, "n_param": 0,
            }  # fmt: skip
        if nombre == "deriva":
            # crecimiento geometrico medio de los ultimos 5 anios
            g = (y.iloc[-1] / y.iloc[-61]) ** (1 / 60) if len(y) > 61 else 1.0
            ajustado = y.shift(1) * g
            return {
                "pronosticar": lambda h: _futuro(y, h, y.iloc[-1] * g ** np.arange(1, h + 1)),
                "residuos": (y - ajustado).dropna(), "parametros": {"g mensual": g}, "n_param": 1,
            }  # fmt: skip
        if nombre == "ses":
            m = SimpleExpSmoothing(y, initialization_method="estimated").fit()
            par = {"alfa": m.params["smoothing_level"]}
        elif nombre == "holt":
            m = ExponentialSmoothing(y, trend="add", initialization_method="estimated").fit()
            par = {"alfa": m.params["smoothing_level"], "beta": m.params["smoothing_trend"]}
        elif nombre == "holt_winters":
            m = ExponentialSmoothing(
                y, trend="add", seasonal="mul", seasonal_periods=PERIODO,
                initialization_method="estimated",
            ).fit()  # fmt: skip
            par = {
                "alfa": m.params["smoothing_level"], "beta": m.params["smoothing_trend"],
                "gamma": m.params["smoothing_seasonal"],
            }  # fmt: skip
        elif nombre == "sarima":
            orden, est = sarima
            m = SARIMAX(
                np.log(y), order=orden, seasonal_order=est, trend="c" if est[1] == 0 else "n"
            ).fit(disp=False, maxiter=200)
            quemar = orden[1] + est[1] * PERIODO + 1  # los primeros residuos son de arranque
            return {
                "pronosticar": lambda h: np.exp(m.forecast(h)),
                "intervalo": lambda h, a=0.05: np.exp(m.get_forecast(h).conf_int(alpha=a)),
                "residuos": m.resid.iloc[quemar:], "n_param": len(m.params) - 1,
                "parametros": {"orden": orden, "estacional": est[:3], "AIC": m.aic},
            }  # fmt: skip
        else:
            raise ValueError(f"Modelo desconocido: {nombre}")
    return {
        "pronosticar": lambda h: m.forecast(h), "residuos": m.resid.iloc[PERIODO:],
        "parametros": par, "n_param": len(par),
    }  # fmt: skip


def _futuro(y, h, valores):
    idx = pd.date_range(y.index[-1] + pd.offsets.MonthBegin(1), periods=h, freq="MS")
    return pd.Series(valores, index=idx)


# --- Metricas -------------------------------------------------------------------------------
def metricas(real, pronostico):
    e = np.asarray(real, dtype=float) - np.asarray(pronostico, dtype=float)
    return {
        "MAE": float(np.mean(np.abs(e))),
        "RMSE": float(np.sqrt(np.mean(e**2))),
        "MAPE_pct": float(np.mean(np.abs(e) / np.abs(real)) * 100),
    }


def evaluar_retencion(s, h=12, sarima=None, modelos=MODELOS):
    """Entrena con todo menos los ultimos h meses y mide el error en esos h meses."""
    entrenamiento, prueba = s.iloc[:-h], s.iloc[-h:]
    filas, pronos = [], {}
    for nombre in modelos:
        m = ajustar(nombre, entrenamiento, sarima) if sarima else ajustar(nombre, entrenamiento)
        p = m["pronosticar"](h)
        pronos[nombre] = pd.Series(np.asarray(p), index=prueba.index)
        filas.append({"modelo": nombre, **metricas(prueba, pronos[nombre])})
    return pd.DataFrame(filas), pronos


def validacion_origen_movil(s, horizontes=(1, 3, 6, 12), origenes=36, sarima=None, modelos=MODELOS):
    """Validacion cruzada temporal: se repite el pronostico desde `origenes` fechas distintas.

    En cada origen se reajusta el modelo solo con lo conocido hasta ese mes. Devuelve una
    fila por modelo, origen y horizonte con el error. Es mas confiable que una sola retencion.
    """
    hmax, filas = max(horizontes), []
    for k in range(origenes):
        corte = len(s) - hmax - k
        entrenamiento = s.iloc[:corte]
        for nombre in modelos:
            m = ajustar(nombre, entrenamiento, sarima) if sarima else ajustar(nombre, entrenamiento)
            p = np.asarray(m["pronosticar"](hmax))
            for h in horizontes:
                real = s.iloc[corte + h - 1]
                filas.append({
                    "modelo": nombre, "origen": entrenamiento.index[-1], "h": h,
                    "real": real, "pronostico": p[h - 1], "error": real - p[h - 1],
                    "ape": abs(real - p[h - 1]) / real * 100,
                })  # fmt: skip
    return pd.DataFrame(filas)


def resumen_validacion(vc):
    g = vc.groupby(["modelo", "h"])
    return pd.DataFrame({
        "MAE": g["error"].apply(lambda e: np.mean(np.abs(e))),
        "RMSE": g["error"].apply(lambda e: np.sqrt(np.mean(e**2))),
        "MAPE_pct": g["ape"].mean(),
        "sesgo": g["error"].mean(),
    }).reset_index()  # fmt: skip


# --- Residuos ----------------------------------------------------------------------------------
def diagnostico_residuos(residuos, n_param=0, rezagos=(12, 24)):
    """Ljung-Box (H0: residuos sin autocorrelacion), media y normalidad (Jarque-Bera)."""
    r = pd.Series(residuos).dropna()
    fila = {"n": len(r), "media": float(r.mean()), "desv": float(r.std())}
    for k in rezagos:
        lb = acorr_ljungbox(r, lags=[k], model_df=min(n_param, k - 1))
        fila[f"LB({k})"] = float(lb["lb_stat"].iloc[0])
        fila[f"p LB({k})"] = float(lb["lb_pvalue"].iloc[0])
    jb = jarque_bera(r)
    fila["p Jarque-Bera"] = float(jb[1])
    fila["ruido blanco"] = all(fila[f"p LB({k})"] >= 0.05 for k in rezagos)
    return fila
