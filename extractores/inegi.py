"""Fuente 3: indice de costos de construccion residencial por ciudad (INEGI, INPP).

Es la fuente principal del modulo ObraPrecio. El sitio de consulta de indices de
precios de INEGI (https://www.inegi.org.mx/app/indicesdeprecios/) es publico, no
pide llave y su robots.txt permite /app. Se usan dos servicios del mismo sitio:

1. Catalogo de series (una vez; queda versionado en inegi_series.json):
   POST {base}/servicios/ArbolAjaxInteraccion.asmx/EstructuraInicialV2
   Responde el arbol de la estructura en HTML: una fila por serie con su clave,
   nombre, nivel (0 = ciudad, 1 = componente) y periodo disponible.

2. Datos (exportacion CSV que ofrece el boton "Exportar" del sitio):
   GET {base}/Exportacion.aspx?INPtipoExporta=CSV&_series=e|<claves>&_anioI=..&_anioF=..
   Responde un CSV en Windows-1252: encabezado con metadatos por serie y despues
   una fila por mes ("Ene 2023") con una columna por serie. Las celdas sin dato
   llegan vacias.

La respuesta se guarda tal como llego (bytes exactos) en la capa bronce; la
conversion a tabla larga, fechas y UTF-8 ocurre en la capa plata.

Uso:
  python -m extractores.inegi --catalogo     # regenera inegi_series.json
  python -m extractores.inegi --historico    # baja toda la historia (reanudable)
"""

import argparse
import csv
import html
import io
import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from extractores import bronce, config
from extractores.base import ExtractorEtico

FUENTE = "inegi_inpp"
CODIFICACION = "cp1252"
COMPONENTES = {
    "Materiales de construcción": "materiales",
    "Alquiler de maquinaria": "maquinaria",
    "Mano de obra": "mano_obra",
}


# --- Catalogo de series ---------------------------------------------------------
def parsear_arbol(html_arbol):
    """Convierte el arbol HTML del sitio en una lista de series con su ciudad."""
    series, ciudad = [], None
    for fila in re.findall(r'<tr id="TR_\d+"(.*?)</tr>', html_arbol, re.S):
        nivel = int(re.search(r"data-arbolnivel='?(\d+)", fila).group(1))
        clave = re.search(r"CBox_Serie_(\d+)", fila)
        celda = re.search(r"<td[^>]*>(.*?)</td>", fila, re.S)
        if not clave or not celda:
            continue
        nombre = html.unescape(re.sub(r"<[^>]+>", "", celda.group(1))).strip()
        # Algunas filas del sitio llegan con guiones al inicio ("-- Materiales de ...")
        limpio = nombre.lstrip("-– ").strip()
        periodo = re.search(r"goCalculadora\('\d+','([^']*)','([^']*)'", fila)
        if nivel == 0:
            ciudad = nombre
        series.append(
            {
                "serie": clave.group(1),
                "ciudad_fuente": ciudad,
                "componente": "general" if nivel == 0 else COMPONENTES.get(limpio, limpio),
                "nombre_fuente": nombre,
                "inicio_fuente": periodo.group(1) if periodo else "",
                "fin_fuente": periodo.group(2) if periodo else "",
            }
        )
    return series


def descubrir_series(extractor):
    url = f"{config.INEGI_BASE}/servicios/ArbolAjaxInteraccion.asmx/EstructuraInicialV2"
    if not extractor._reglas(url).can_fetch(extractor.user_agent, url):
        raise PermissionError(f"robots.txt no permite {url}")
    cuerpo = {
        "idEstructura": config.INEGI_ESTRUCTURA,
        "esquemaBD": "",
        "paramFuente": "0|CargaInicial",
        "notas": [],
        "open": True,
    }
    r = extractor.sesion.post(url, json=cuerpo, timeout=90)
    r.raise_for_status()
    series = parsear_arbol(r.json()["d"])
    if not series:
        raise ValueError("El catalogo de INEGI llego vacio")
    return series


def cargar_series():
    return json.loads(config.ARCHIVO_SERIES_INEGI.read_text(encoding="utf-8"))["series"]


def grupos(series, tam=None):
    tam = tam or config.INEGI_SERIES_POR_PETICION
    claves = [s["serie"] for s in series]
    return [claves[i : i + tam] for i in range(0, len(claves), tam)]


# --- Datos ----------------------------------------------------------------------
def parametros(claves, anio_i, anio_f):
    e = config.INEGI_ESTRUCTURA
    return {
        "INPtipoExporta": "CSV",
        "idEstructura": e,
        "_formato": "CSV",
        "_anioI": str(anio_i),
        "_anioF": str(anio_f),
        "_meta": "1",
        "_tipo": "Niveles",
        "_info": "Índices",
        "_orient": "vertical",
        "esquema": "",
        "st": config.INEGI_TITULO,
        "pf": "inp",
        "cuadro": e,
        "_series": "e|" + ",".join(claves) + ",",
        "cvEstructura": e,
    }


def resumir(contenido):
    """Cuenta series y meses de un CSV de exportacion; falla si no tiene la forma esperada."""
    filas = list(csv.reader(io.StringIO(contenido.decode(CODIFICACION))))
    inicio = next((i for i, f in enumerate(filas) if f and f[0] == "Fecha"), None)
    if inicio is None:
        raise ValueError("El CSV de INEGI no trae la fila 'Fecha' con las claves de serie")
    datos = [f for f in filas[inicio + 1 :] if f and f[0].strip()]
    valores = sum(1 for f in datos for v in f[1:] if v.strip())
    return {"series": [c for c in filas[inicio][1:] if c], "meses": len(datos), "valores": valores}


def capturar(extractor, claves, anio_i, anio_f, subruta, nombre, base=None):
    url = f"{config.INEGI_BASE}/Exportacion.aspx"
    params = parametros(claves, anio_i, anio_f)
    capturado = bronce.ahora_utc()
    r = extractor.get(url, params=params)
    meta = {
        "url": r.url or url,
        "http_status": r.status_code,
        "capturado_utc": capturado.isoformat(),
        "estructura": config.INEGI_ESTRUCTURA,
        "series": claves,
        "anio_inicio": anio_i,
        "anio_fin": anio_f,
        "codificacion": CODIFICACION,
        "intentos": extractor.ultimos_intentos,
    }
    ruta = bronce.guardar(FUENTE, r.content, meta, subruta, nombre, base=base, ext="csv")
    resumen = resumir(r.content)
    if resumen["valores"] == 0:
        raise ValueError(f"Respuesta sin datos de INEGI ({ruta.name})")
    if set(resumen["series"]) != set(claves):
        raise ValueError(f"INEGI respondio series distintas a las pedidas ({ruta.name})")
    return ruta, resumen


def historico(extractor, anio_f, base=None):
    """Baja toda la historia en bloques de series. Salta los bloques que ya existen."""
    total, bloques = 0, grupos(cargar_series())
    for i, claves in enumerate(bloques):
        nombre = f"{config.INEGI_ANIO_INICIAL}_{anio_f}_e{config.INEGI_ESTRUCTURA[6:10]}_g{i:02d}"
        destino = (base or config.DIR_BRONCE) / FUENTE / "historico" / f"{nombre}.csv.gz"
        if destino.exists():
            continue
        _, res = capturar(
            extractor, claves, config.INEGI_ANIO_INICIAL, anio_f, "historico", nombre, base=base
        )
        total += res["valores"]
        print(
            f"  INEGI bloque {i + 1}/{len(bloques)}: {res['meses']} meses, "
            f"{len(res['series'])} series, {res['valores']} valores"
        )
    return total


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--catalogo", action="store_true", help="regenera inegi_series.json")
    p.add_argument("--historico", action="store_true", help="descarga toda la historia")
    a = p.parse_args()
    ex = ExtractorEtico(timeout=120)
    if a.catalogo:
        series = descubrir_series(ex)
        config.ARCHIVO_SERIES_INEGI.write_text(
            json.dumps(
                {
                    "estructura": config.INEGI_ESTRUCTURA,
                    "titulo": config.INEGI_TITULO,
                    "generado_utc": bronce.ahora_utc().isoformat(timespec="seconds"),
                    "series": series,
                },
                ensure_ascii=False,
                indent=1,
            )
            + "\n",
            encoding="utf-8",
        )
        ciudades = {s["ciudad_fuente"] for s in series}
        print(f"Catalogo: {len(series)} series, {len(ciudades)} ciudades (incluye Nacional)")
    if a.historico:
        anio = datetime.now(ZoneInfo(config.ZONA_HORARIA)).year
        print(f"Total: {historico(ex, anio)} valores")


if __name__ == "__main__":
    main()
