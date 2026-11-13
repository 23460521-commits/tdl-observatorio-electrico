"""Puerta de calidad automatica (Pandera) entre bronce y plata.

Un registro solo entra a plata si cumple el contrato de su tabla (esquema, tipos y
rangos). El que no cumple se manda a cuarentena con el nombre de la regla que
rompio; nunca se borra ni se corrige en silencio.

Ademas de las reglas por registro hay revisiones de conjunto (continuidad de las
series, base del indice, cobertura) que no rechazan filas: quedan en el reporte y,
si son graves, detienen el pipeline.
"""

import pandas as pd

try:  # pandera >= 0.24
    import pandera.pandas as pa
except ImportError:  # versiones anteriores
    import pandera as pa

from pipeline import catalogos

SALTO_MAXIMO_PCT = 60.0  # mayor a esto en un mes no es creible ni en la hiperinflacion de 1987
FIX_MIN, FIX_MAX = 5.0, 40.0  # pesos por dolar; fuera de esto es error de captura

ESQUEMA_INPP = pa.DataFrameSchema(
    {
        "serie": pa.Column(str, pa.Check.str_matches(r"^\d{4,9}$", error="serie_formato_invalido")),
        "fecha": pa.Column(
            "datetime64[ns]",
            [
                pa.Check(lambda s: s >= pd.Timestamp("1973-01-01"), error="fecha_anterior_a_1973"),
                pa.Check(lambda s: s <= pd.Timestamp.now().normalize(), error="fecha_futura"),
                pa.Check(lambda s: s.dt.day == 1, error="fecha_no_es_inicio_de_mes"),
            ],
            coerce=True,
        ),
        "ciudad_id": pa.Column(str, pa.Check.str_length(min_value=2, error="ciudad_id_vacio")),
        "ciudad": pa.Column(str),
        "estado": pa.Column(str),
        "region": pa.Column(
            str,
            pa.Check.isin([*catalogos.REGIONES, "Nacional"], error="region_fuera_de_catalogo"),
        ),
        "componente": pa.Column(
            str, pa.Check.isin(catalogos.COMPONENTES, error="componente_fuera_de_catalogo")
        ),
        "indice": pa.Column(
            float,
            [
                pa.Check.gt(0, error="indice_no_positivo"),
                pa.Check.le(1000, error="indice_fuera_de_rango (>1000)"),
            ],
            coerce=True,
        ),
        "archivo_bronce": pa.Column(str),
        "capturado_utc": pa.Column(str),
    },
    unique=["serie", "fecha"],
    strict=True,
    ordered=False,
)

ESQUEMA_FIX = pa.DataFrameSchema(
    {
        "fecha": pa.Column(
            "datetime64[ns]",
            [
                pa.Check(lambda s: s >= pd.Timestamp("1991-11-01"), error="fecha_anterior_al_fix"),
                pa.Check(lambda s: s <= pd.Timestamp.now().normalize(), error="fecha_futura"),
                pa.Check(lambda s: s.dt.dayofweek < 5, error="fix_en_fin_de_semana"),
            ],
            coerce=True,
        ),
        "fix": pa.Column(
            float,
            pa.Check.in_range(FIX_MIN, FIX_MAX, error=f"fix_fuera_de_rango ({FIX_MIN}-{FIX_MAX})"),
            coerce=True,
        ),
        "archivo_bronce": pa.Column(str),
        "capturado_utc": pa.Column(str),
    },
    unique=["fecha"],
    strict=True,
)


def validar(df, esquema):
    """Aplica el esquema completo (lazy). Devuelve (validos, rechazados con `motivo`)."""
    df = df.reset_index(drop=True)
    for col in ("fecha",):
        if col in df:
            df[col] = pd.to_datetime(df[col], errors="coerce").astype("datetime64[ns]")
    try:
        return esquema.validate(df, lazy=True), df.iloc[0:0].assign(motivo="")
    except pa.errors.SchemaErrors as e:
        casos = e.failure_cases
        sin_fila = casos[casos["index"].isna()]
        if len(sin_fila):  # falla de estructura (columna faltante o de mas): no hay fila que aislar
            raise ValueError(
                "La tabla no cumple la estructura del esquema: "
                + "; ".join(sorted(set(sin_fila["check"].astype(str))))
            ) from e
        motivos = (
            casos.assign(regla=casos["column"].astype(str) + ": " + casos["check"].astype(str))
            .groupby("index")["regla"]
            .agg(lambda r: " | ".join(sorted(set(r))))
        )
        malos = df.loc[motivos.index.astype(int)].assign(motivo=motivos.to_numpy())
        buenos = df.drop(index=motivos.index.astype(int)).reset_index(drop=True)
        return esquema.validate(buenos), malos


def saltos_implausibles(inpp):
    """Filas cuyo cambio mensual supera SALTO_MAXIMO_PCT (error de captura, no inflacion)."""
    d = inpp.sort_values(["serie", "fecha"])
    cambio = d.groupby("serie")["indice"].pct_change().abs() * 100
    return d.index[cambio > SALTO_MAXIMO_PCT]


def revisiones_de_conjunto(inpp, fix, series):
    """Revisiones que miran la tabla completa. Devuelve una lista de dicts para el reporte."""
    r = []

    def agregar(nombre, ok, detalle, grave=False):
        r.append({"revision": nombre, "ok": bool(ok), "grave": grave, "detalle": detalle})

    g = inpp.groupby("serie")["fecha"].agg(["min", "max", "count"])
    esperado = (
        (g["max"].dt.year - g["min"].dt.year) * 12 + g["max"].dt.month - g["min"].dt.month + 1
    )
    huecos = int((esperado - g["count"]).sum())
    agregar("continuidad_mensual", huecos == 0, f"{huecos} meses faltantes dentro de las series")

    faltan = sorted(set(s["serie"] for s in series) - set(inpp["serie"]))
    agregar(
        "cobertura_de_series",
        not faltan,
        f"{inpp['serie'].nunique()} de {len(series)} series con datos; faltan: {faltan[:10]}",
        grave=len(faltan) > len(series) * 0.1,
    )

    base = inpp[inpp["fecha"] == pd.Timestamp("2019-07-01")]
    desvio = (base["indice"] - 100).abs().max() if len(base) else float("nan")
    agregar(
        "base_julio_2019_igual_a_100",
        len(base) > 0 and desvio < 1e-6,
        f"{len(base)} series en julio 2019; desviacion maxima respecto a 100: {desvio:.2e}",
    )

    ciudades = inpp.groupby("ciudad_id")["componente"].nunique()
    incompletas = sorted(ciudades[ciudades < len(catalogos.COMPONENTES)].index)
    agregar(
        "ciudades_con_los_4_componentes",
        not incompletas,
        f"{len(ciudades)} ciudades; incompletas: {incompletas}",
    )

    if len(fix):
        dias = pd.bdate_range(fix["fecha"].min(), fix["fecha"].max())
        sin_fix = len(dias.difference(fix["fecha"]))
        agregar(
            "fix_dias_habiles_cubiertos",
            sin_fix / len(dias) < 0.06,
            f"{sin_fix} de {len(dias)} dias de lunes a viernes sin FIX "
            f"({sin_fix / len(dias):.1%}; los festivos bancarios no tienen FIX)",
        )
    agregar(
        "tablas_no_vacias",
        len(inpp) > 0 and len(fix) > 0,
        f"inpp={len(inpp)} filas, fix={len(fix)} filas",
        grave=True,
    )
    return r
