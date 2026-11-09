"""Capa bronce: guarda la respuesta tal como llego, comprimida, con sus metadatos.

Cada captura produce dos archivos:
  <nombre>.json.gz    los bytes exactos que respondio la fuente (gzip)
  <nombre>.meta.json  origen, fecha de captura, SHA-256 de los bytes, etc.
El SHA-256 permite demostrar en una auditoria que el dato no se altero.
"""
import csv
import gzip
import hashlib
import json
import os
from datetime import UTC, datetime

from extractores import config


def ahora_utc():
    return datetime.now(UTC)


def guardar(fuente, contenido, meta, subruta, nombre, base=None):
    destino = (base or config.DIR_BRONCE) / fuente / subruta
    destino.mkdir(parents=True, exist_ok=True)
    ruta = destino / f"{nombre}.json.gz"
    # filename="" y mtime=0: el mismo contenido produce el mismo .gz (reproducible)
    with open(ruta, "wb") as f, gzip.GzipFile(filename="", fileobj=f, mode="wb", mtime=0) as gz:
        gz.write(contenido)
    meta = {
        **meta,
        "fuente": fuente,
        "archivo": ruta.name,
        "bytes": len(contenido),
        "sha256": hashlib.sha256(contenido).hexdigest(),
        "capturado_utc": meta.get("capturado_utc") or ahora_utc().isoformat(),
        "user_agent": config.USER_AGENT,
        "version_extractor": config.VERSION,
    }
    (destino / f"{nombre}.meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return ruta


# --- Bitacora de ejecuciones (insumo de MTBF, MTTR y disponibilidad) ------------
CAMPOS_BITACORA = [
    "ejecucion_id", "disparador", "fuente", "inicio_utc", "fin_utc",
    "duracion_s", "estado", "registros", "intentos", "mensaje",
]


def id_ejecucion():
    return os.environ.get("GITHUB_RUN_ID") or "local-" + ahora_utc().strftime("%Y%m%dT%H%M%S")


def disparador():
    return os.environ.get("GITHUB_EVENT_NAME", "local")


def registrar(fila, archivo=None):
    archivo = archivo or config.BITACORA
    archivo.parent.mkdir(parents=True, exist_ok=True)
    nuevo = not archivo.exists() or archivo.stat().st_size == 0
    with open(archivo, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS_BITACORA, lineterminator="\n")
        if nuevo:
            w.writeheader()
        w.writerow({k: fila.get(k, "") for k in CAMPOS_BITACORA})
