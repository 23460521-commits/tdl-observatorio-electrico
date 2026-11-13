"""Limpieza estadistica: faltantes, atipicos, normalizacion, discretizacion y reduccion.

Son funciones puras (reciben y devuelven tablas) para poder probarlas sin archivos.
El cuaderno docs/E1/limpieza.ipynb las usa y muestra la evidencia de cada decision.
"""

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest

from pipeline import catalogos

SEMILLA = 20261113


# --- 1. Valores faltantes ---------------------------------------------------------
def rejilla_completa(inpp):
    """Todas las combinaciones serie x mes del periodo; `falta` marca las que no existen."""
    meses = pd.date_range(inpp["fecha"].min(), inpp["fecha"].max(), freq="MS")
    attrs = inpp.drop_duplicates("serie")[["serie", "ciudad_id", "region", "componente"]]
    rejilla = attrs.merge(pd.DataFrame({"fecha": meses}), how="cross")
    rejilla = rejilla.merge(inpp[["serie", "fecha", "indice"]], on=["serie", "fecha"], how="left")
    rejilla["falta"] = rejilla["indice"].isna()
    return rejilla


def diagnostico_faltantes(rejilla):
    """Diagnostica el mecanismo (MCAR / MAR / MNAR) con evidencia.

    MCAR exige que faltar no dependa de nada. Se contrasta con ji-cuadrada la
    independencia entre `falta` y variables que si se observan (decada, componente,
    region). Si depende de ellas, no es MCAR. Se revisa tambien si los faltantes
    estan solo al inicio de cada serie (faltante estructural: la serie aun no existia).
    """
    r = rejilla.assign(decada=(rejilla["fecha"].dt.year // 10 * 10).astype(str))
    pruebas = {}
    for var in ("decada", "componente", "region"):
        tabla = pd.crosstab(r[var], r["falta"])
        if min(tabla.shape) < 2:
            pruebas[var] = {"chi2": 0.0, "p": 1.0, "v_cramer": 0.0}
            continue
        chi2, p, _, _ = stats.chi2_contingency(tabla)
        v = float(np.sqrt(chi2 / (tabla.to_numpy().sum() * (min(tabla.shape) - 1))))
        pruebas[var] = {"chi2": float(chi2), "p": float(p), "v_cramer": v}
    inicio = r[~r["falta"]].groupby("serie")["fecha"].min()
    interiores = int((r["falta"] & (r["fecha"] > r["serie"].map(inicio))).sum())
    total = int(r["falta"].sum())
    depende = any(t["p"] < 0.01 and t["v_cramer"] > 0.1 for t in pruebas.values())
    if total == 0:
        mecanismo = "sin faltantes"
    elif interiores == 0 and depende:
        mecanismo = "MAR estructural (por diseno): la serie aun no existia en ese periodo"
    elif depende:
        mecanismo = "MAR: depende de variables observadas"
    else:
        mecanismo = "compatible con MCAR"
    return {
        "celdas": len(r),
        "faltantes": total,
        "pct_faltante": total / len(r) * 100,
        "faltantes_interiores": interiores,
        "pruebas": pruebas,
        "mecanismo": mecanismo,
        "inicio_por_serie": inicio,
    }


def evaluar_imputacion(ancho, fraccion=0.05, semilla=SEMILLA):
    """Oculta al azar valores conocidos y mide que metodo los recupera mejor.

    `ancho`: tabla fecha x serie sin faltantes. Devuelve MAE y MAPE por metodo.
    Sirve para justificar con datos el metodo que se usara si aparece un hueco corto.
    """
    rng = np.random.default_rng(semilla)
    mascara = rng.random(ancho.shape) < fraccion
    mascara[0, :] = mascara[-1, :] = False  # los extremos no se pueden interpolar
    oculto = ancho.mask(mascara)
    promedio_ciudades = oculto.mean(axis=1)
    metodos = {
        "media_de_la_serie": oculto.fillna(oculto.mean()),
        "ultimo_valor (LOCF)": oculto.ffill(),
        "interpolacion_lineal": oculto.interpolate(method="linear"),
        "interpolacion_log (geometrica)": np.exp(np.log(oculto).interpolate(method="linear")),
        "razon_con_promedio_de_series": oculto.fillna(
            oculto.div(promedio_ciudades, axis=0).interpolate().mul(promedio_ciudades, axis=0)
        ),
    }
    real = ancho.to_numpy()[mascara]
    filas = []
    for nombre, t in metodos.items():
        est = t.to_numpy()[mascara]
        filas.append(
            {
                "metodo": nombre,
                "n_ocultos": int(mascara.sum()),
                "MAE": float(np.mean(np.abs(est - real))),
                "MAPE_pct": float(np.mean(np.abs(est - real) / real) * 100),
            }
        )
    return pd.DataFrame(filas).sort_values("MAE").reset_index(drop=True)


def completar_calendario_fix(fix):
    """FIX para todos los dias naturales.

    Banxico solo determina el FIX en dias habiles bancarios. El faltante de sabados,
    domingos y festivos es MAR (depende del calendario, que si se observa) y la regla
    es de negocio, no estadistica: el ultimo FIX publicado sigue vigente hasta el
    siguiente. Por eso se imputa con el ultimo valor (LOCF) y se marca `imputado`.
    """
    dias = pd.date_range(fix["fecha"].min(), fix["fecha"].max(), freq="D")
    d = fix.set_index("fecha")[["fix"]].reindex(dias)
    d["imputado"] = d["fix"].isna()
    d["fix"] = d["fix"].ffill()
    return d.rename_axis("fecha").reset_index()


def fix_mensual(fix):
    """Agrega el FIX diario a mes: promedio de los dias con dato y cierre de mes (con LOCF)."""
    diario = completar_calendario_fix(fix)
    oficial = fix.assign(mes=fix["fecha"].dt.to_period("M").dt.to_timestamp())
    m = oficial.groupby("mes")["fix"].agg(fix_promedio="mean", fix_dias_con_dato="count")
    cierre = diario.assign(mes=diario["fecha"].dt.to_period("M").dt.to_timestamp())
    m["fix_cierre"] = cierre.groupby("mes")["fix"].last()
    m["fix_var_mensual_pct"] = m["fix_promedio"].pct_change() * 100
    completo = cierre.groupby("mes")["fecha"].max().dt.is_month_end
    m["fix_mes_completo"] = completo
    return m.rename_axis("fecha").reset_index()


# --- 2. Atipicos y ruido ------------------------------------------------------------
def referencia(x, umbral_ceros=0.5):
    """Muestra contra la que se mide lo "normal".

    Mano de obra y alquiler de maquinaria son series escalonadas: la mayoria de los
    meses no cambian (variacion = 0) y de pronto dan un salto (revision salarial).
    Con mas de la mitad de ceros el IQR y el MAD valen 0 y cualquier ajuste se
    marcaria como atipico. En ese caso la referencia son solo los meses con cambio.
    """
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if len(x) and np.mean(x == 0) > umbral_ceros:
        return x[x != 0]
    return x


def limites_iqr(x, k=1.5, ref=None):
    q1, q3 = np.nanpercentile(x if ref is None else ref, [25, 75])
    return q1 - k * (q3 - q1), q3 + k * (q3 - q1)


def atipico_iqr(x, k=1.5, ref=None):
    lo, hi = limites_iqr(x, k, ref)
    return (x < lo) | (x > hi)


def _centro_y_escala(ref):
    ref = np.asarray(ref, dtype=float)
    mediana = np.nanmedian(ref)
    mad = np.nanmedian(np.abs(ref - mediana))
    if mad == 0:  # respaldo: desviacion media absoluta, en la misma escala que el MAD
        mad = np.nanmean(np.abs(ref - mediana)) * 0.8453
    return mediana, (mad / 0.6745 if mad > 0 else np.nan)


def z_robusto(x, ref=None):
    """Z modificado de Iglewicz y Hoaglin: 0.6745 (x - mediana) / MAD. Resiste a los extremos."""
    x = np.asarray(x, dtype=float)
    mediana, escala = _centro_y_escala(x if ref is None else ref)
    return (x - mediana) / escala


def atipico_iforest(X, contaminacion=0.01, semilla=SEMILLA):
    """Isolation Forest multivariado. Las filas con NaN no se evaluan (devuelven False)."""
    X = np.asarray(X, dtype=float)
    completos = ~np.isnan(X).any(axis=1)
    marca = np.zeros(len(X), dtype=bool)
    if completos.sum() >= 50:
        modelo = IsolationForest(
            n_estimators=200, contamination=contaminacion, random_state=semilla
        )
        marca[completos] = modelo.fit_predict(X[completos]) == -1
    return marca


def winsorizar(x, z_max=3.5, ref=None):
    """Recorta a mediana +- z_max * escala robusta. Atenua el extremo sin borrar la observacion."""
    x = np.asarray(x, dtype=float)
    mediana, escala = _centro_y_escala(x if ref is None else ref)
    if not np.isfinite(escala):
        return x
    return np.clip(x, mediana - z_max * escala, mediana + z_max * escala)


# --- 3. Normalizacion y estandarizacion ---------------------------------------------
def minmax(x):
    lo, hi = np.nanmin(x), np.nanmax(x)
    return (x - lo) / (hi - lo) if hi > lo else x * 0.0


def zscore(x):
    s = np.nanstd(x, ddof=0)
    return (x - np.nanmean(x)) / s if s > 0 else x * 0.0


# --- 4. Discretizacion y jerarquias conceptuales --------------------------------------
def nivel_inflacion(var_anual_pct):
    """Variacion anual (%) -> categoria ordenada. Cortes de negocio (meta de Banxico)."""
    return pd.cut(
        var_anual_pct,
        bins=catalogos.CORTES_INFLACION,
        labels=catalogos.NIVELES_INFLACION,
        right=False,
    )


def terciles(x, etiquetas=("bajo", "medio", "alto")):
    """Discretizacion por igual frecuencia (cuantiles)."""
    try:
        return pd.qcut(x, q=len(etiquetas), labels=list(etiquetas), duplicates="drop")
    except ValueError:
        return pd.Series(pd.Categorical([None] * len(x), categories=list(etiquetas)), index=x.index)


def jerarquia_temporal(fecha):
    f = pd.to_datetime(fecha)
    return pd.DataFrame(
        {
            "anio": f.dt.year,
            "trimestre": f.dt.year.astype(str) + "-T" + f.dt.quarter.astype(str),
            "mes": f.dt.month,
        }
    )


# --- 5. Reduccion de datos --------------------------------------------------------------
def muestreo_estratificado(df, estrato, fraccion, semilla=SEMILLA):
    return df.groupby(estrato, group_keys=False).sample(frac=fraccion, random_state=semilla)


def componentes_principales(ancho, n=3):
    """PCA sobre columnas estandarizadas. Devuelve (varianza explicada, cargas)."""
    X = ancho.dropna()
    Z = (X - X.mean()) / X.std(ddof=0)
    pca = PCA(n_components=min(n, Z.shape[1]), random_state=SEMILLA).fit(Z)
    nombres = [f"CP{i + 1}" for i in range(pca.n_components_)]
    cargas = pd.DataFrame(pca.components_.T, index=X.columns, columns=nombres)
    return pd.Series(pca.explained_variance_ratio_, index=nombres), cargas
