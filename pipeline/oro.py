"""Capa oro: tablas listas para analisis, tablero y chat de ObraPrecio.

Parte de las dos tablas de plata (indice de construccion por ciudad y tipo de cambio),
las integra por mes y agrega las variables derivadas de la limpieza estadistica.
"""

import numpy as np
import pandas as pd

from pipeline import limpieza

# Desde diciembre de 2003 las 188 series existen; antes solo una parte (ver limpieza.ipynb).
ANALISIS_DESDE = "2004-01-01"


def panel_mensual(inpp, fix):
    """Tabla larga: una fila por serie y mes, con variaciones, banderas y tipo de cambio."""
    d = inpp.drop(columns=["archivo_bronce", "capturado_utc"]).sort_values(["serie", "fecha"])
    g = d.groupby("serie")["indice"]
    d["var_mensual_pct"] = g.pct_change() * 100
    d["var_anual_pct"] = g.pct_change(12) * 100
    d = d[d["fecha"] >= ANALISIS_DESDE].reset_index(drop=True)
    d = pd.concat([d, limpieza.jerarquia_temporal(d["fecha"])], axis=1)

    # Brecha contra el indice nacional del mismo componente y mes
    nac = d[d["ciudad_id"] == "nacional"].set_index(["componente", "fecha"])["var_anual_pct"]
    d["var_anual_nacional_pct"] = nac.reindex(
        pd.MultiIndex.from_frame(d[["componente", "fecha"]])
    ).to_numpy()
    d["brecha_vs_nacional_pp"] = d["var_anual_pct"] - d["var_anual_nacional_pct"]

    # Atipicos: tres metodos sobre la variacion mensual, dentro de cada componente.
    # En series escalonadas (mano de obra, maquinaria) la referencia son los meses con cambio.
    for col in ("z_robusto", "var_mensual_tratada_pct"):
        d[col] = np.nan
    for col in ("atipico_iqr", "atipico_iforest"):
        d[col] = False
    d["serie_escalonada"] = False
    for _, idx in d.groupby("componente").groups.items():
        x = d.loc[idx, "var_mensual_pct"].to_numpy()
        ref = limpieza.referencia(x)
        escalonada = len(ref) < np.sum(~np.isnan(x))
        cambia = ~((x == 0) & escalonada)  # un mes sin cambio en serie escalonada no es atipico
        d.loc[idx, "serie_escalonada"] = escalonada
        d.loc[idx, "z_robusto"] = np.where(cambia, limpieza.z_robusto(x, ref), 0.0)
        d.loc[idx, "atipico_iqr"] = limpieza.atipico_iqr(x, k=3.0, ref=ref) & cambia
        d.loc[idx, "var_mensual_tratada_pct"] = np.where(cambia, limpieza.winsorizar(x, ref=ref), x)
        X = d.loc[idx, ["var_mensual_pct", "var_anual_pct", "brecha_vs_nacional_pp"]].to_numpy()
        d.loc[idx, "atipico_iforest"] = limpieza.atipico_iforest(X)
    d["atipico_z"] = d["z_robusto"].abs() > 3.5
    d["atipico_votos"] = d[["atipico_iqr", "atipico_z", "atipico_iforest"]].sum(axis=1)

    # Normalizacion: min-max del nivel por serie; z-score de la variacion por serie
    d["indice_minmax"] = d.groupby("serie")["indice"].transform(limpieza.minmax)
    d["var_mensual_z"] = d.groupby("serie")["var_mensual_pct"].transform(limpieza.zscore)

    # Discretizacion
    d["nivel_inflacion"] = limpieza.nivel_inflacion(d["var_anual_pct"]).astype("string")
    d["costo_relativo"] = (
        d.groupby(["componente", "fecha"])["var_anual_pct"]
        .transform(limpieza.terciles)
        .astype("string")
    )

    # Integracion con Banxico (mensual). Antes de 2017 no hay FIX en bronce: queda vacio.
    m = limpieza.fix_mensual(fix)
    d = d.merge(
        m[["fecha", "fix_promedio", "fix_cierre", "fix_var_mensual_pct"]], on="fecha", how="left"
    )
    orden = [
        "fecha",
        "anio",
        "trimestre",
        "mes",
        "ciudad_id",
        "ciudad",
        "estado",
        "region",
        "componente",
        "serie",
        "indice",
        "var_mensual_pct",
        "var_anual_pct",
        "var_anual_nacional_pct",
        "brecha_vs_nacional_pp",
        "nivel_inflacion",
        "costo_relativo",
        "indice_minmax",
        "var_mensual_z",
        "serie_escalonada",
        "z_robusto",
        "atipico_iqr",
        "atipico_z",
        "atipico_iforest",
        "atipico_votos",
        "var_mensual_tratada_pct",
        "fix_promedio",
        "fix_cierre",
        "fix_var_mensual_pct",
    ]
    return d[orden].sort_values(["ciudad_id", "componente", "fecha"]).reset_index(drop=True)


def ciudad_mensual(panel):
    """Tabla ancha (reduccion de 4 filas a 1): una fila por ciudad y mes."""
    llave = ["fecha", "ciudad_id", "ciudad", "estado", "region"]
    idx = panel.pivot(index=llave, columns="componente", values="indice").add_prefix("indice_")
    va = panel.pivot(index=llave, columns="componente", values="var_anual_pct").add_prefix(
        "var_anual_"
    )
    gen = panel[panel["componente"] == "general"].set_index(llave)[
        [
            "var_mensual_pct",
            "brecha_vs_nacional_pp",
            "nivel_inflacion",
            "costo_relativo",
            "fix_promedio",
            "fix_var_mensual_pct",
        ]
    ]
    return (
        idx.join(va)
        .join(gen)
        .reset_index()
        .sort_values(["ciudad_id", "fecha"])
        .reset_index(drop=True)
    )


def resumen_region_anual(panel):
    """Reduccion por agregacion subiendo la jerarquia: ciudad -> region, mes -> anio."""
    d = panel[panel["ciudad_id"] != "nacional"]
    r = (
        d.groupby(["anio", "region", "componente"])
        .agg(
            ciudades=("ciudad_id", "nunique"),
            meses=("fecha", "nunique"),
            indice_promedio=("indice", "mean"),
            var_mensual_media_pct=("var_mensual_pct", "mean"),
            var_mensual_desv_pct=("var_mensual_pct", "std"),
            var_anual_cierre_pct=("var_anual_pct", "last"),
            atipicos=("atipico_votos", lambda v: int((v >= 2).sum())),
        )
        .reset_index()
    )
    cierre = (
        d.sort_values("fecha")
        .groupby(["anio", "region", "componente", "ciudad_id"])["var_anual_pct"]
        .last()
        .groupby(["anio", "region", "componente"])
        .mean()
    )
    r["var_anual_cierre_pct"] = cierre.reindex(
        pd.MultiIndex.from_frame(r[["anio", "region", "componente"]])
    ).to_numpy()
    return r


def ranking_ciudades(panel):
    """Ultimo mes disponible: donde subio mas el costo de construir en 12 meses."""
    ultimo = panel["fecha"].max()
    d = panel[(panel["fecha"] == ultimo) & (panel["ciudad_id"] != "nacional")]
    t = (
        d.pivot(
            index=["ciudad_id", "ciudad", "estado", "region"],
            columns="componente",
            values="var_anual_pct",
        )
        .add_prefix("var_anual_")
        .reset_index()
    )
    t.insert(0, "fecha", ultimo)
    t["lugar"] = t["var_anual_general"].rank(ascending=False, method="min").astype(int)
    nac = panel[
        (panel["fecha"] == ultimo)
        & (panel["ciudad_id"] == "nacional")
        & (panel["componente"] == "general")
    ]["var_anual_pct"]
    t["var_anual_nacional"] = float(nac.iloc[0]) if len(nac) else np.nan
    t["supera_nacional"] = t["var_anual_general"] > t["var_anual_nacional"]
    return t.sort_values("lugar").reset_index(drop=True)


def redondear(df, decimales=6):
    cols = df.select_dtypes(include=[np.floating]).columns
    return df.assign(**{c: df[c].round(decimales) for c in cols})
