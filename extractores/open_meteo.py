"""Fuente 2: clima horario de Open-Meteo para las ciudades del observatorio.

- Captura diaria: API de pronostico con los ultimos 3 dias y los 2 siguientes.
- Historico: API de archivo (reanalisis), por bloques de un ano.
Una sola peticion trae todas las ubicaciones (coordenadas separadas por coma).
Nota para el plan de recopilacion: la capa gratuita es para uso no comercial.
"""
import json

from extractores import bronce, config

FUENTE = "open_meteo"
URL_PRONOSTICO = "https://api.open-meteo.com/v1/forecast"
URL_ARCHIVO = "https://archive-api.open-meteo.com/v1/archive"


def parametros_base():
    nombres = list(config.UBICACIONES)
    return nombres, {
        "latitude": ",".join(str(config.UBICACIONES[n][0]) for n in nombres),
        "longitude": ",".join(str(config.UBICACIONES[n][1]) for n in nombres),
        "hourly": ",".join(config.OPEN_METEO_VARIABLES),
        "timezone": config.ZONA_HORARIA,
    }


def resumir(payload):
    lista = payload if isinstance(payload, list) else [payload]
    horas = sum(len((p.get("hourly") or {}).get("time", [])) for p in lista)
    return {"ubicaciones": len(lista), "valores": horas}


def _capturar(extractor, url, params, nombres, subruta, nombre, base=None):
    capturado = bronce.ahora_utc()
    r = extractor.get(url, params=params)
    meta = {
        "url": r.url,
        "http_status": r.status_code,
        "capturado_utc": capturado.isoformat(),
        "ubicaciones": nombres,  # mismo orden que la lista de la respuesta
        "parametros": params,
        "intentos": extractor.ultimos_intentos,
    }
    ruta = bronce.guardar(FUENTE, r.content, meta, subruta, nombre, base=base)
    resumen = resumir(json.loads(r.content))
    if resumen["ubicaciones"] != len(nombres) or resumen["valores"] == 0:
        raise ValueError(f"Respuesta incompleta de Open-Meteo: {resumen} ({ruta.name})")
    return ruta, resumen


def capturar_pronostico(extractor, subruta, nombre, base=None):
    nombres, params = parametros_base()
    params |= {"past_days": 3, "forecast_days": 2}
    return _capturar(extractor, URL_PRONOSTICO, params, nombres, subruta, nombre, base)


def capturar_archivo(extractor, inicio, fin, subruta, nombre, base=None):
    nombres, params = parametros_base()
    params |= {"start_date": inicio.isoformat(), "end_date": fin.isoformat()}
    return _capturar(extractor, URL_ARCHIVO, params, nombres, subruta, nombre, base)
