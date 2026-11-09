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
BITACORA = RAIZ / "calidad" / "bitacora-captura.csv"
ARCHIVO_ZONAS = RAIZ / "extractores" / "zonas_confirmadas.json"

# --- CENACE: precios por zona de carga (servicio web SW-PEND) -------------------
CENACE_BASE = "https://ws01.cenace.gob.mx:8082"
CENACE_SISTEMA = "SIN"   # Sistema Interconectado Nacional
CENACE_PROCESO = "MDA"   # Mercado de Dia en Adelanto
CENACE_MAX_DIAS = 7      # limite de dias por peticion
CENACE_MAX_ZONAS = 10    # limite de zonas por peticion

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

# --- Open-Meteo: clima por ubicacion -------------------------------------------
# El orden importa: la API responde una lista en este mismo orden y el nombre
# de cada ubicacion se guarda en los metadatos para unirlo en la capa plata.
UBICACIONES = {
    "colima": (19.2433, -103.7250),
    "manzanillo": (19.0522, -104.3158),
    "guadalajara": (20.6597, -103.3496),
    "monterrey": (25.6866, -100.3161),
    "cdmx": (19.4326, -99.1332),
    "culiacan": (24.8091, -107.3940),
    "hermosillo": (29.0729, -110.9559),
    "merida": (20.9674, -89.5926),
}
OPEN_METEO_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "shortwave_radiation",
    "cloud_cover",
    "precipitation",
]
