"""Configuracion central del Observatorio Electrico de Colima.

Todo lo que cambia entre equipos o entre entregas vive aqui, no regado en el codigo.
"""

import os
from pathlib import Path

VERSION = "0.1.0"

# --- Identificacion honesta del extractor (regla del proyecto) ---------------
# En GitHub se define como variable del repositorio TDL_CONTACTO.
CONTACTO = os.environ.get("TDL_CONTACTO", "CAMBIAR-correo@ejemplo.mx")
USER_AGENT = (
    f"TDL-ObservatorioElectricoColima/{VERSION} "
    f"(proyecto academico TecNM campus Colima; contacto: {CONTACTO})"
)

# CENACE publica el SIN en hora del centro; alineamos todo a esa zona horaria.
ZONA_HORARIA = "America/Mexico_City"

# --- Rutas ---------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
DIR_BRONCE = RAIZ / "data" / "bronce"
DIR_PLATA = RAIZ / "data" / "plata"
DIR_ORO = RAIZ / "data" / "oro"
DIR_CUARENTENA = RAIZ / "data" / "cuarentena"
DIR_CALIDAD = RAIZ / "calidad"
BITACORA = RAIZ / "calidad" / "bitacora-captura.csv"
ARCHIVO_ZONAS = RAIZ / "extractores" / "zonas_confirmadas.json"

# --- CENACE: precios por zona de carga (servicio web SW-PEND) -------------------
CENACE_BASE = "https://ws01.cenace.gob.mx:8082"
CENACE_SISTEMA = "SIN"  # Sistema Interconectado Nacional
CENACE_PROCESO = "MDA"  # Mercado de Dia en Adelanto
CENACE_MAX_DIAS = 7  # limite de dias por peticion
CENACE_MAX_ZONAS = 10  # limite de zonas por peticion

# Nombres a probar con `python -m extractores.descubrir_zonas`.
# Solo los que respondan con datos pasan a zonas_confirmadas.json.
# Las de Colima son candidatas: hay que confirmarlas contra el servicio.
ZONAS_CANDIDATAS = [
    "COLIMA",
    "MANZANILLO",
    "GUADALAJARA",
    "MONTERREY",
    "VDM CENTRO",
    "CULIACAN",
    "HERMOSILLO",
    "MERIDA",
    "PUEBLA",
    "QUERETARO",
    "MORELIA",
    "LEON",
]

# --- Banxico: Sistema de Informacion Economica (SIE) ----------------------------
# El token es personal: en GitHub va como *secret* BANXICO_TOKEN, nunca en el codigo.
BANXICO_BASE = "https://www.banxico.org.mx/SieAPIRest/service/v1"
BANXICO_SERIES = {
    "SF43718": "Tipo de cambio pesos por dolar E.U.A., FIX",
}
BANXICO_DESDE = "2017-01-01"

# --- INEGI: Indice Nacional de Precios Productor (INPP), construccion --------------
# Estructura "Construccion residencial por ciudad" (antes INCEVIS), base julio 2019 = 100:
# 46 ciudades + Nacional, cada una con indice general y tres componentes
# (materiales, alquiler de maquinaria y mano de obra). Consulta publica, sin llave.
#
# INEGI actualizo la canasta del INPP en agosto de 2025 y publico el indice en una
# estructura nueva (con otras claves de serie). La anterior quedo congelada en julio de
# 2025. Se consulta la vigente; lo capturado de la anterior se conserva en bronce.
INEGI_BASE = "https://www.inegi.org.mx/app/indicesdeprecios"
INEGI_ESTRUCTURA = "1120019000100010"  # vigente (INPP actualizacion 2025)
INEGI_ESTRUCTURA_ANTERIOR = "1120015000400010"  # congelada en julio de 2025
INEGI_TITULO = "Construcción residencial por ciudad"
INEGI_ANIO_INICIAL = 1973  # primer periodo que publica la fuente (serie Nacional)
INEGI_SERIES_POR_PETICION = 48  # 12 ciudades x 4 series; mantiene corta la URL
ARCHIVO_SERIES_INEGI = RAIZ / "extractores" / "inegi_series.json"


def banxico_token():
    token = os.environ.get("BANXICO_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "Falta la variable de entorno BANXICO_TOKEN (token gratuito del SIE de Banxico)"
        )
    return token
