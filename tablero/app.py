"""Tablero publico de ObraPrecio.

Local:   streamlit run tablero/app.py
Publico: Streamlit Community Cloud, archivo principal tablero/app.py

Solo lee la capa oro y los reportes de calidad del repositorio: no calcula nada que no
este ya validado por el pipeline.
"""

import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
COLOR = {
    "General": "#2a78d6", "Materiales": "#eb6834",
    "Alquiler de maquinaria": "#1baf7a", "Mano de obra": "#eda100",
}  # fmt: skip
COMPONENTE = {
    "general": "General", "materiales": "Materiales",
    "maquinaria": "Alquiler de maquinaria", "mano_obra": "Mano de obra",
}  # fmt: skip

st.set_page_config(page_title="ObraPrecio", page_icon="🏗️", layout="wide")


@st.cache_data
def cargar():
    oro = RAIZ / "data" / "oro"
    panel = pd.read_csv(oro / "obraprecio_ciudad_mensual.csv", parse_dates=["fecha"])
    ranking = pd.read_csv(oro / "ranking_ciudades.csv", parse_dates=["fecha"])
    ruta = oro / "pronostico_mensual.csv"
    pron = pd.read_csv(ruta, parse_dates=["fecha", "ultimo_dato"]) if ruta.exists() else None
    puerta = json.loads((RAIZ / "calidad" / "reporte-puerta.json").read_text(encoding="utf-8"))
    return panel, ranking, pron, puerta


def frase_cliente(f):
    cambio = "suba" if f["var_vs_ultimo_dato_pct"] >= 0 else "baje"
    inf = (f["ic80_inf"] / f["indice_ultimo_dato"] - 1) * 100
    sup = (f["ic80_sup"] / f["indice_ultimo_dato"] - 1) * 100
    return (
        f"Para **{f['fecha']:%m/%Y}** esperamos que construir en {f['ciudad']} {cambio} alrededor "
        f"de **{abs(f['var_vs_ultimo_dato_pct']):.1f} %** respecto a {f['ultimo_dato']:%m/%Y}. "
        f"No es un número exacto: en unos 8 de cada 10 casos el cambio quedaría entre "
        f"**{inf:+.1f} %** y **{sup:+.1f} %**. Un presupuesto que deja ese margen queda cubierto "
        "en la mayoría de los casos."
    )


panel, ranking, pron, puerta = cargar()
ultimo = panel["fecha"].max()

st.title("ObraPrecio")
st.caption(
    "¿Cuánto ha subido el costo de construir una vivienda en tu ciudad y qué lo está moviendo? "
    "Índice oficial de INEGI (INPP, construcción residencial, base julio 2019 = 100)."
)

ciudades = sorted(panel.loc[panel["ciudad_id"] != "nacional", "ciudad"].unique())
ciudad = st.selectbox(
    "Ciudad", ciudades, index=ciudades.index("Colima") if "Colima" in ciudades else 0
)
d = panel[panel["ciudad"] == ciudad].sort_values("fecha")
nac = panel[panel["ciudad_id"] == "nacional"].sort_values("fecha")
hoy, r = d.iloc[-1], ranking[ranking["ciudad"] == ciudad].iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric(f"Costo en 12 meses ({ultimo:%m/%Y})", f"{hoy['var_anual_general']:+.1f} %")
c2.metric("Promedio nacional", f"{nac.iloc[-1]['var_anual_general']:+.1f} %",
          f"{hoy['brecha_vs_nacional_pp']:+.1f} puntos tu ciudad", delta_color="inverse")  # fmt: skip  # noqa: E501
c3.metric("Lugar entre 46 ciudades", f"{int(r['lugar'])}", help="1 = donde más subió")
c4.metric("Desde julio de 2019", f"{hoy['indice_general'] - 100:+.0f} %")

st.subheader("Qué lo está moviendo")
desde = st.slider("Desde el año", 2005, int(ultimo.year) - 1, 2018)
largo = d[d["fecha"].dt.year >= desde].melt(
    id_vars="fecha", value_vars=[f"var_anual_{k}" for k in COMPONENTE],
    var_name="componente", value_name="variacion",
)  # fmt: skip
largo["componente"] = largo["componente"].str.replace("var_anual_", "").map(COMPONENTE)
grafica = (
    alt.Chart(largo.dropna())
    .mark_line(strokeWidth=2)
    .encode(
        x=alt.X("fecha:T", title=None),
        y=alt.Y("variacion:Q", title="% en 12 meses"),
        color=alt.Color(
            "componente:N",
            title=None,
            sort=list(COLOR),
            scale=alt.Scale(domain=list(COLOR), range=list(COLOR.values())),
            legend=alt.Legend(orient="top"),
        ),  # fmt: skip
        tooltip=[
            alt.Tooltip("fecha:T", format="%m/%Y", title="Mes"),
            alt.Tooltip("componente:N", title="Componente"),
            alt.Tooltip("variacion:Q", format="+.1f", title="% en 12 meses"),
        ],
    )
    .properties(height=320)
)
st.altair_chart(grafica, width="stretch")
partes = {v: hoy[f"var_anual_{k}"] for k, v in COMPONENTE.items() if k != "general"}
mayor = max(partes, key=partes.get)
st.write(
    f"En {ciudad}, lo que más subió en los últimos 12 meses fue **{mayor.lower()}** "
    f"({partes[mayor]:+.1f} %). " + " · ".join(f"{k}: {v:+.1f} %" for k, v in partes.items())
)

st.subheader("Qué esperar en los próximos meses")
p = pron[pron["ciudad"] == ciudad] if pron is not None else None
if p is None or p.empty:
    st.info(
        "El pronóstico validado está disponible por ahora para Colima y para el total nacional. "
        "Las demás ciudades se agregan en la siguiente etapa."
    )
else:
    hist = d[d["fecha"] >= ultimo - pd.DateOffset(years=4)][["fecha", "indice_general"]]
    base = alt.Chart(p).encode(x=alt.X("fecha:T", title=None))
    banda = base.mark_area(opacity=0.18, color="#6250d6").encode(
        y=alt.Y("ic80_inf:Q", title="Índice (julio 2019 = 100)", scale=alt.Scale(zero=False)),
        y2="ic80_sup:Q",
    )
    linea = base.mark_line(color="#6250d6", strokeWidth=2).encode(
        y="pronostico_sarima:Q",
        tooltip=[
            alt.Tooltip("fecha:T", format="%m/%Y", title="Mes"),
            alt.Tooltip("pronostico_sarima:Q", format=".1f", title="Pronóstico"),
            alt.Tooltip("ic80_inf:Q", format=".1f", title="Mínimo probable (80 %)"),
            alt.Tooltip("ic80_sup:Q", format=".1f", title="Máximo probable (80 %)"),
        ],
    )
    real = (
        alt.Chart(hist)
        .mark_line(color="#0b0b0b", strokeWidth=2)
        .encode(x="fecha:T", y="indice_general:Q",
                tooltip=[alt.Tooltip("fecha:T", format="%m/%Y", title="Mes"),
                         alt.Tooltip("indice_general:Q", format=".1f", title="Observado")])
    )  # fmt: skip
    st.altair_chart((banda + linea + real).properties(height=320), width="stretch")
    st.caption("Negro: observado. Morado: pronóstico. Banda: donde caería en 8 de cada 10 casos.")
    meses = st.radio("¿A cuántos meses empieza o termina tu obra?", [1, 3, 6, 12], index=1,
                     horizontal=True)  # fmt: skip
    f = p[p["horizonte_meses"] == meses].iloc[0]
    st.success(frase_cliente(f))
    st.caption(
        f"Modelo: SARIMA {f['modelo_sarima']}, elegido por tener el menor error en 36 pruebas con "
        f"datos que no había visto. Error típico a este plazo: {f['error_esperado_sarima_pct']:.1f} %. "  # noqa: E501
        "En épocas de choque de precios (como 2021 y 2022) el margen real es mayor que el mostrado."
    )

st.subheader("Cómo va tu ciudad contra las demás")
tabla = ranking[["lugar", "ciudad", "estado", "var_anual_general", "var_anual_materiales",
                 "var_anual_maquinaria", "var_anual_mano_obra"]].rename(columns={
    "lugar": "Lugar", "ciudad": "Ciudad", "estado": "Estado", "var_anual_general": "General %",
    "var_anual_materiales": "Materiales %", "var_anual_maquinaria": "Maquinaria %",
    "var_anual_mano_obra": "Mano de obra %"})  # fmt: skip
st.dataframe(tabla.round(1), hide_index=True, width="stretch", height=280)

st.subheader("¿Por qué confiar en estos datos?")
i, b = puerta["inegi_inpp"], puerta["banxico_sie"]
q1, q2, q3 = st.columns(3)
q1.metric("Registros de INEGI revisados", f"{i['registros_bronce']:,}")
q2.metric("Aceptados", f"{i['registros_plata']:,}")
q3.metric("Rechazados con motivo", f"{i['registros_cuarentena']:,}")
st.write(
    "Cada dato pasa por una puerta de calidad automática antes de publicarse. Los rechazados no "
    "se borran: se guardan con su motivo. En esta corrida, todos los rechazos son meses en los "
    "que INEGI todavía no medía esa ciudad o componente."
)
with st.expander("Detalle de la puerta de calidad"):
    st.dataframe(pd.DataFrame(i["cuarentena_por_motivo"] + b["cuarentena_por_motivo"]),
                 hide_index=True)  # fmt: skip
    st.dataframe(pd.DataFrame(puerta["revisiones_de_conjunto"])[["revision", "ok", "detalle"]],
                 hide_index=True, width="stretch")  # fmt: skip
st.caption(
    f"Fuentes: INEGI, Índice Nacional de Precios Productor; Banco de México, tipo de cambio FIX. "
    f"Último mes publicado: {ultimo:%m/%Y}. El índice mide cuánto cambia el costo, no el precio "
    "en pesos de una obra. Proyecto escolar TRUSTED DATA LAB, TecNM campus Colima."
)
