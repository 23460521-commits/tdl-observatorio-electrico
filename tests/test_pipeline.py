"""Pruebas del pipeline plata/oro y de la puerta de calidad. Sin red: bronce sintetico."""

import gzip
import json

import numpy as np
import pandas as pd
import pytest

from extractores import inegi
from pipeline import catalogos, ejecutar, limpieza, oro, plata, puerta

SERIES = [
    {"serie": "1001", "ciudad_fuente": "Colima, Col.", "componente": "general"},
    {"serie": "1002", "ciudad_fuente": "Colima, Col.", "componente": "materiales"},
    {"serie": "1003", "ciudad_fuente": "Villahermosa,Tab.", "componente": "general"},
    {"serie": "1004", "ciudad_fuente": "Atlantida, Atl.", "componente": "general"},
]
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def csv_inegi(columnas, anios=(2018, 2019)):
    """Imita la exportacion CSV de INEGI (encabezado de metadatos + una fila por mes)."""
    claves = list(columnas)
    lineas = [
        '"Instituto Nacional de Estadística y Geografía",',
        "",
        '"Título",' + ",".join(f'"Serie {c}"' for c in claves),
        '"Fecha",' + ",".join(f'"{c}"' for c in claves),
    ]
    n = 0
    for anio in anios:
        for mes in MESES:
            valores = [columnas[c](n) for c in claves]
            lineas.append(f'"{mes} {anio}",' + ",".join(f'"{v}"' for v in valores))
            n += 1
    return ("\r\n".join(lineas) + "\r\n").encode("cp1252")


def escribir(base, fuente, subruta, nombre, contenido, ext, capturado):
    destino = base / fuente / subruta
    destino.mkdir(parents=True, exist_ok=True)
    with gzip.open(destino / f"{nombre}.{ext}.gz", "wb") as f:
        f.write(contenido)
    (destino / f"{nombre}.meta.json").write_text(
        json.dumps({"capturado_utc": capturado, "codificacion": "cp1252"}), encoding="utf-8"
    )


def banxico_json(datos):
    cuerpo = {
        "bmx": {
            "series": [{"idSerie": "SF43718", "datos": [{"fecha": f, "dato": d} for f, d in datos]}]
        }
    }
    return json.dumps(cuerpo).encode()


@pytest.fixture
def bronce_tmp(tmp_path):
    base = tmp_path / "bronce"
    escribir(
        base,
        "inegi_inpp",
        "historico",
        "bloque0",
        csv_inegi(
            {
                "1001": lambda n: f"{90 + n:.6f}",
                "1002": lambda n: "N/E" if n < 6 else f"{80 + n:.6f}",  # la serie empieza despues
                "1003": lambda n: f"{95 + n * 0.5:.6f}",
                "1004": lambda n: f"{100 + n:.6f}",  # ciudad fuera de catalogo
            }
        ),
        "csv",
        "2026-11-01T00:00:00+00:00",
    )
    # Captura posterior que traslapa 2019: mismo valor salvo una revision en Dic 2019 (n=23)
    escribir(
        base,
        "inegi_inpp",
        "diario/fecha_captura=2026-11-09",
        "x_inpp_g0",
        csv_inegi(
            {
                "1001": lambda n: f"{90 + 12 + n + (0.25 if n == 11 else 0):.6f}",
            },
            anios=(2019,),
        ),
        "csv",
        "2026-11-09T00:00:00+00:00",
    )
    escribir(
        base,
        "banxico_sie",
        "historico",
        "2019",
        banxico_json(
            [
                ("02/01/2019", "19.6512"),
                ("03/01/2019", "19.6073"),
                ("04/01/2019", "N/E"),
                ("07/01/2019", "19.4902"),
                ("08/01/2019", "1949.02"),
                ("31/02/2019", "19.50"),
                ("05/01/2019", "19.48"),  # sabado: el FIX no se determina en fin de semana
            ]
        ),
        "json",
        "2026-11-01T00:00:00+00:00",
    )
    escribir(
        base,
        "banxico_sie",
        "diario/fecha_captura=2026-11-09",
        "x_fix",
        banxico_json(
            [
                ("07/01/2019", "19.4902"),
                ("09/01/2019", "19.3601"),
            ]
        ),
        "json",
        "2026-11-09T00:00:00+00:00",
    )
    return base


# --- Catalogos ----------------------------------------------------------------------
def test_todas_las_ciudades_del_catalogo_de_inegi_estan_mapeadas():
    for s in inegi.cargar_series():
        geo = catalogos.ciudad(s["ciudad_fuente"])
        assert geo is not None, s["ciudad_fuente"]
        assert geo["region"] in [*catalogos.REGIONES, "Nacional"]
        assert s["componente"] in catalogos.COMPONENTES


def test_catalogo_tiene_46_ciudades_mas_nacional_con_4_componentes():
    series = inegi.cargar_series()
    assert len({s["ciudad_fuente"] for s in series}) == 47
    assert len(series) == 47 * 4


def test_nombres_irregulares_de_la_fuente_se_normalizan():
    assert catalogos.ciudad("Villahermosa,Tab.")["ciudad"] == "Villahermosa"
    assert catalogos.ciudad("Cd. Jiménez Chih.")["estado"] == "Chihuahua"
    assert catalogos.ciudad("Colima, Col.")["region"] == "Centro Norte"
    assert catalogos.ciudad("Atlantida, Atl.") is None
    assert catalogos.slug("San Luis Potosí") == "san_luis_potosi"


def test_parsear_arbol_quita_guiones_del_nombre_del_componente():
    arbol = (
        "<tr id=\"TR_1\" data-arbolnivel='0'><td><input id='CBox_Serie_11'>Colima, Col.</td>"
        "<span onclick=\"goCalculadora('11','Dic 2003','Jul 2025','x')\"></span></tr>"
        "<tr id=\"TR_2\" data-arbolnivel=1><td><input id='CBox_Serie_12'>"
        "-- Materiales de construcción</td></tr>"
    )
    s = inegi.parsear_arbol(arbol)
    assert [x["componente"] for x in s] == ["general", "materiales"]
    assert s[1]["ciudad_fuente"] == "Colima, Col." and s[0]["inicio_fuente"] == "Dic 2003"


# --- Plata: formato, integracion y duplicados --------------------------------------------
def test_inegi_ancho_a_largo_con_fechas_y_tipos(bronce_tmp):
    limpio, _ = plata.limpiar_inegi(plata.leer_inegi(bronce_tmp), SERIES)
    col = limpio[limpio["serie"] == "1001"]
    assert len(col) == 24 and col["fecha"].min() == pd.Timestamp("2018-01-01")
    assert col["indice"].dtype == float and col["ciudad"].iloc[0] == "Colima"
    assert limpio[limpio["serie"] == "1003"]["estado"].iloc[0] == "Tabasco"


def test_ne_y_ciudad_desconocida_van_a_cuarentena_con_motivo(bronce_tmp):
    limpio, q = plata.limpiar_inegi(plata.leer_inegi(bronce_tmp), SERIES)
    motivos = q["motivo"].value_counts()
    assert motivos["valor_no_existe_en_fuente_NE"] == 6
    assert motivos["ciudad_no_catalogada"] == 24
    assert "1004" not in set(limpio["serie"])
    assert len(limpio[limpio["serie"] == "1002"]) == 18  # 24 meses - 6 N/E


def test_revision_de_la_fuente_gana_la_captura_reciente(bronce_tmp):
    limpio, q = plata.limpiar_inegi(plata.leer_inegi(bronce_tmp), SERIES)
    dic = limpio[(limpio["serie"] == "1001") & (limpio["fecha"] == "2019-12-01")]
    assert len(dic) == 1 and dic["indice"].iloc[0] == pytest.approx(113.25)
    superado = q[q["motivo"] == "valor_superado_por_captura_mas_reciente"]
    assert len(superado) == 1 and superado["valor"].iloc[0] == "113.000000"
    # los 11 meses repetidos con el mismo valor se colapsan sin ir a cuarentena
    assert not limpio.duplicated(["serie", "fecha"]).any()


def test_ningun_registro_se_pierde_en_silencio(bronce_tmp):
    crudo = plata.leer_inegi(bronce_tmp)
    limpio, q = plata.limpiar_inegi(crudo, SERIES)
    identicos = 11  # traslape de 2019 con el mismo valor
    assert len(limpio) + len(q) + identicos == len(crudo)


def test_banxico_fecha_valor_y_duplicados(bronce_tmp):
    limpio, q = plata.limpiar_banxico(plata.leer_banxico(bronce_tmp))
    assert set(q["motivo"]) == {"valor_no_existe_en_fuente_NE", "fecha_no_interpretable"}
    assert not limpio["fecha"].duplicated().any()
    assert limpio["fix"].dtype == float


# --- Puerta de calidad ------------------------------------------------------------------
def test_puerta_fix_rechaza_fuera_de_rango_y_fin_de_semana(bronce_tmp):
    limpio, _ = plata.limpiar_banxico(plata.leer_banxico(bronce_tmp))
    ok, malos = puerta.validar(limpio, puerta.ESQUEMA_FIX)
    motivos = " ".join(malos["motivo"])
    assert "fix_fuera_de_rango" in motivos and "fix_en_fin_de_semana" in motivos
    assert len(malos) == 2 and ok["fix"].between(puerta.FIX_MIN, puerta.FIX_MAX).all()


def test_puerta_inpp_rechaza_indice_no_positivo_y_componente_raro(bronce_tmp):
    limpio, _ = plata.limpiar_inegi(plata.leer_inegi(bronce_tmp), SERIES)
    limpio.loc[0, "indice"] = -5.0
    limpio.loc[1, "componente"] = "acabados"
    ok, malos = puerta.validar(limpio, puerta.ESQUEMA_INPP)
    assert len(malos) == 2 and len(ok) == len(limpio) - 2
    assert any("indice_no_positivo" in m for m in malos["motivo"])
    assert any("componente_fuera_de_catalogo" in m for m in malos["motivo"])


def test_puerta_detiene_si_falta_una_columna(bronce_tmp):
    limpio, _ = plata.limpiar_inegi(plata.leer_inegi(bronce_tmp), SERIES)
    with pytest.raises(ValueError, match="estructura"):
        puerta.validar(limpio.drop(columns=["indice"]), puerta.ESQUEMA_INPP)


def test_salto_implausible_se_detecta():
    d = pd.DataFrame(
        {
            "serie": ["1"] * 4,
            "fecha": pd.date_range("2020-01-01", periods=4, freq="MS"),
            "indice": [100.0, 101.0, 1010.0, 102.0],
        }
    )
    assert list(puerta.saltos_implausibles(d)) == [2, 3]


def test_revisiones_de_conjunto_detectan_hueco(bronce_tmp):
    limpio, _ = plata.limpiar_inegi(plata.leer_inegi(bronce_tmp), SERIES)
    fix, _ = plata.limpiar_banxico(plata.leer_banxico(bronce_tmp))
    con_hueco = limpio.drop(index=limpio.index[5])
    r = {x["revision"]: x for x in puerta.revisiones_de_conjunto(con_hueco, fix, SERIES)}
    assert not r["continuidad_mensual"]["ok"]
    assert r["base_julio_2019_igual_a_100"]["ok"] is False  # el sintetico no esta en base 100


# --- Limpieza estadistica ------------------------------------------------------------------
def test_diagnostico_faltantes_estructural():
    fechas = pd.date_range("2000-01-01", periods=120, freq="MS")
    a = pd.DataFrame({"serie": "a", "fecha": fechas, "indice": 1.0, "componente": "general"})
    b = pd.DataFrame(
        {"serie": "b", "fecha": fechas[60:], "indice": 1.0, "componente": "maquinaria"}
    )
    d = pd.concat([a, b]).assign(ciudad_id="x", region="Sur")
    diag = limpieza.diagnostico_faltantes(limpieza.rejilla_completa(d))
    assert diag["faltantes"] == 60 and diag["faltantes_interiores"] == 0
    assert diag["mecanismo"].startswith("MAR estructural")
    assert diag["pruebas"]["componente"]["p"] < 0.01


def test_completar_calendario_fix_usa_ultimo_valor():
    fix = pd.DataFrame({"fecha": pd.to_datetime(["2026-11-06", "2026-11-09"]), "fix": [18.6, 18.7]})
    d = limpieza.completar_calendario_fix(fix)
    assert list(d["fix"]) == [18.6, 18.6, 18.6, 18.7]
    assert list(d["imputado"]) == [False, True, True, False]


def test_evaluar_imputacion_interpolar_gana_a_la_media():
    t = np.arange(120)
    ancho = pd.DataFrame({"a": 100 * 1.004**t, "b": 90 * 1.005**t + np.sin(t)})
    r = limpieza.evaluar_imputacion(ancho, fraccion=0.1).set_index("metodo")
    assert r.loc["interpolacion_lineal", "MAE"] < r.loc["media_de_la_serie", "MAE"] / 10
    assert r["n_ocultos"].iloc[0] > 0


def test_atipicos_iqr_y_z_robusto():
    x = np.array([1.0, 1.1, 0.9, 1.05, 0.95, 1.0, 1.02, 0.98, 9.0])
    assert limpieza.atipico_iqr(x).tolist() == [False] * 8 + [True]
    z = limpieza.z_robusto(x)
    assert abs(z[-1]) > 3.5 and np.all(np.abs(z[:-1]) < 3.5)
    assert limpieza.winsorizar(x)[-1] < 9.0 and limpieza.winsorizar(x)[0] == 1.0


def test_serie_escalonada_usa_solo_los_meses_con_cambio():
    x = np.array([0.0] * 80 + [4.0, 5.0, 6.0, 5.5, 4.5, 5.2, 4.8, 5.0, 30.0, 5.1])
    ref = limpieza.referencia(x)
    assert len(ref) == 10
    assert limpieza.atipico_iqr(x, ref=ref).sum() == 81  # sin tratar los ceros aparte...
    marca = limpieza.atipico_iqr(x, ref=ref) & (x != 0)
    assert marca.sum() == 1 and marca[88]  # ...solo el ajuste de 30 % es atipico


def test_isolation_forest_es_reproducible_e_ignora_nan():
    rng = np.random.default_rng(1)
    X = rng.normal(size=(300, 3))
    X[0] = [15, 15, 15]
    X[1, 1] = np.nan
    a, b = limpieza.atipico_iforest(X), limpieza.atipico_iforest(X)
    assert a[0] and not a[1] and (a == b).all()


def test_normalizacion():
    x = np.array([10.0, 20.0, 30.0])
    assert limpieza.minmax(x).tolist() == [0.0, 0.5, 1.0]
    z = limpieza.zscore(x)
    assert z.mean() == pytest.approx(0) and z.std() == pytest.approx(1)
    assert limpieza.minmax(np.array([5.0, 5.0])).tolist() == [0.0, 0.0]


def test_discretizacion_y_jerarquia_temporal():
    niveles = limpieza.nivel_inflacion(pd.Series([-1.0, 0.0, 2.9, 3.0, 7.0, 15.0]))
    assert list(niveles) == ["deflacion", "baja", "baja", "moderada", "alta", "muy_alta"]
    j = limpieza.jerarquia_temporal(pd.Series(pd.to_datetime(["2025-07-01"])))
    assert j.iloc[0].tolist() == [2025, "2025-T3", 7]
    assert limpieza.terciles(pd.Series(range(9))).value_counts().tolist() == [3, 3, 3]


def test_pca_varianza_suma_a_lo_mas_uno():
    rng = np.random.default_rng(2)
    base = rng.normal(size=200)
    ancho = pd.DataFrame(
        {"a": base, "b": base * 2 + rng.normal(scale=0.1, size=200), "c": rng.normal(size=200)}
    )
    var, cargas = limpieza.componentes_principales(ancho, n=2)
    assert 0.6 < var["CP1"] < 0.7 and var.sum() <= 1 and cargas.shape == (3, 2)


# --- Pipeline de punta a punta -----------------------------------------------------------------
def test_pipeline_completo_escribe_plata_oro_y_cuarentena(bronce_tmp, tmp_path):
    series = SERIES + [{"serie": "1005", "ciudad_fuente": "Nacional", "componente": "general"}]
    escribir(
        bronce_tmp,
        "inegi_inpp",
        "historico",
        "bloque1",
        csv_inegi({"1005": lambda n: f"{92 + n:.6f}"}, anios=range(2003, 2006)),
        "csv",
        "2026-11-01T00:00:00+00:00",
    )
    escribir(
        bronce_tmp,
        "inegi_inpp",
        "historico",
        "bloque2",
        csv_inegi({"1001": lambda n: f"{50 + n:.6f}"}, anios=range(2003, 2006)),
        "csv",
        "2026-10-01T00:00:00+00:00",
    )
    rep = ejecutar.correr(bronce_tmp, tmp_path / "plata", tmp_path / "oro", tmp_path / "q", series)
    assert rep["inegi_inpp"]["registros_cuarentena"] > 0
    q = pd.read_csv(tmp_path / "q" / "inegi_inpp.csv")
    assert q["motivo"].notna().all() and set(q["etapa"]) <= {"formato", "puerta"}
    panel = pd.read_csv(tmp_path / "oro" / "obraprecio_panel_mensual.csv")
    assert {"var_anual_pct", "nivel_inflacion", "atipico_votos", "fix_promedio"} <= set(
        panel.columns
    )
    assert panel["fecha"].min() >= oro.ANALISIS_DESDE
    for salida in rep["salidas"]:
        assert len(salida["sha256"]) == 64


# --- Extractor de INEGI (sin red) -----------------------------------------------------------------
def test_inegi_resumir_cuenta_series_meses_y_valores():
    contenido = csv_inegi({"1001": lambda n: "N/E" if n < 2 else "100.5", "1002": lambda n: "99.1"})
    r = inegi.resumir(contenido)
    assert r["series"] == ["1001", "1002"] and r["meses"] == 24 and r["valores"] == 48
    with pytest.raises(ValueError, match="Fecha"):
        inegi.resumir(b'"sin","encabezado"\r\n')


def test_inegi_parametros_y_grupos():
    p = inegi.parametros(["11", "12"], 2025, 2026)
    assert p["_series"] == "e|11,12," and p["_anioI"] == "2025" and p["INPtipoExporta"] == "CSV"
    bloques = inegi.grupos([{"serie": str(i)} for i in range(100)], tam=48)
    assert [len(b) for b in bloques] == [48, 48, 4]
