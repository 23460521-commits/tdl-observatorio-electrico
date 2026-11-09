"""Fuente 2: tipo de cambio FIX de Banxico (API REST del SIE).

Formato del servicio:
  {base}/series/{id_serie}/datos/{aaaa-mm-dd}/{aaaa-mm-dd}
Respuesta: {"bmx": {"series": [{"idSerie", "titulo", "datos": [{"fecha", "dato"}]}]}}
La fecha viene como dd/mm/aaaa y el dato como texto ("N/E" si no existe).

Hipotesis del observatorio: buena parte de la generacion electrica usa gas natural
que se paga en dolares, asi que el tipo de cambio podria anticipar el precio de la
energia. Se pone a prueba con la correlacion cruzada en E1.

El token se manda en el encabezado Bmx-Token, nunca en la URL, para que no quede
guardado en los metadatos de la capa bronce ni en el historial de GitHub.
"""
import json

from extractores import bronce, config

FUENTE = "banxico_sie"


def url_datos(series, inicio, fin):
    ids = ",".join(series)
    return f"{config.BANXICO_BASE}/series/{ids}/datos/{inicio.isoformat()}/{fin.isoformat()}"


def resumir(payload):
    series = ((payload or {}).get("bmx") or {}).get("series") or []
    valores = sum(len(s.get("datos") or []) for s in series)
    return {"series": [s.get("idSerie") for s in series], "valores": valores}


def capturar(extractor, inicio, fin, subruta, nombre, series=None, base=None):
    series = list(series or config.BANXICO_SERIES)
    url = url_datos(series, inicio, fin)
    encabezados = {"Bmx-Token": config.banxico_token(), "Accept": "application/json"}
    capturado = bronce.ahora_utc()
    r = extractor.get(url, headers=encabezados)
    meta = {
        "url": url,  # sin token
        "http_status": r.status_code,
        "capturado_utc": capturado.isoformat(),
        "series": series,
        "fecha_inicio": inicio.isoformat(),
        "fecha_fin": fin.isoformat(),
        "intentos": extractor.ultimos_intentos,
    }
    ruta = bronce.guardar(FUENTE, r.content, meta, subruta, nombre, base=base)
    try:
        payload = json.loads(r.content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Respuesta no es JSON ({ruta.name}): {e}") from e
    resumen = resumir(payload)
    if resumen["valores"] == 0:
        raise ValueError(f"Respuesta sin datos de Banxico ({ruta.name})")
    return ruta, resumen
