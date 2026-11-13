"""Capa plata: de las respuestas crudas (bronce) a tablas limpias y tipadas.

Integra dos fuentes heterogeneas y resuelve sus discrepancias:

  Aspecto        INEGI (INPP construccion)         Banxico (FIX)
  -------------  --------------------------------  --------------------------
  Formato        CSV ancho, una columna por serie  JSON anidado
  Codificacion   Windows-1252                      UTF-8
  Fecha          "Ene 2023" (texto, mensual)       "02/01/2026" (diaria)
  Valor          texto con 12 decimales            texto con 4 decimales
  Sin dato       "N/E"                             "N/E"
  Llave          clave de serie (672776)           idSerie (SF43718)
  Zona/ciudad    nombres con abreviaturas          no aplica (nacional)

Ningun registro se descarta en silencio: lo que no pasa se devuelve en una tabla
de cuarentena con la columna `motivo`.
"""

import csv
import gzip
import io
import json

import pandas as pd

from extractores import config
from pipeline import catalogos

COLS_INPP = [
    "serie",
    "fecha",
    "ciudad_id",
    "ciudad",
    "estado",
    "region",
    "componente",
    "indice",
    "archivo_bronce",
    "capturado_utc",
]
COLS_FIX = ["fecha", "fix", "archivo_bronce", "capturado_utc"]


def _meta(ruta_gz):
    ruta = ruta_gz.with_name(ruta_gz.name.rsplit(".", 2)[0] + ".meta.json")
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}


def _rel(ruta, base):
    return ruta.relative_to(base).as_posix()


# --- INEGI ----------------------------------------------------------------------
def leer_inegi(dir_bronce=None):
    """Lee todos los CSV de INEGI en bronce y los pasa de ancho a largo, sin limpiar."""
    base = (dir_bronce or config.DIR_BRONCE) / "inegi_inpp"
    filas = []
    for ruta in sorted(base.rglob("*.csv.gz")):
        meta = _meta(ruta)
        texto = gzip.open(ruta).read().decode(meta.get("codificacion", "cp1252"))
        tabla = list(csv.reader(io.StringIO(texto)))
        inicio = next((i for i, f in enumerate(tabla) if f and f[0] == "Fecha"), None)
        if inicio is None:
            raise ValueError(f"{ruta.name}: no trae la fila 'Fecha'")
        claves = tabla[inicio][1:]
        for f in tabla[inicio + 1 :]:
            if not f or not f[0].strip():
                continue
            for clave, valor in zip(claves, f[1:], strict=False):
                filas.append(
                    (
                        clave,
                        f[0].strip(),
                        valor.strip(),
                        _rel(ruta, base),
                        meta.get("capturado_utc", ""),
                    )
                )
    return pd.DataFrame(
        filas, columns=["serie", "periodo", "valor", "archivo_bronce", "capturado_utc"]
    )


def _fecha_inegi(periodo):
    partes = periodo.split()
    if len(partes) != 2 or partes[0] not in catalogos.MESES or not partes[1].isdigit():
        return pd.NaT
    return pd.Timestamp(year=int(partes[1]), month=catalogos.MESES[partes[0]], day=1)


def limpiar_inegi(crudo, series):
    """Tipa, normaliza nombres y separa lo que no se puede usar. Devuelve (limpio, cuarentena)."""
    cat = {s["serie"]: s for s in series}
    d = crudo.copy()
    d["motivo"] = ""

    def marcar(mascara, motivo):
        d.loc[mascara & (d["motivo"] == ""), "motivo"] = motivo

    marcar(~d["serie"].isin(cat), "serie_no_catalogada")
    marcar(d["valor"].str.upper().isin(["N/E", "NE", "N/D", "ND"]), "valor_no_existe_en_fuente_NE")
    marcar(d["valor"] == "", "valor_vacio")
    d["fecha"] = d["periodo"].map(_fecha_inegi)
    marcar(d["fecha"].isna(), "fecha_no_interpretable")
    d["indice"] = pd.to_numeric(d["valor"], errors="coerce")
    marcar(d["indice"].isna(), "valor_no_numerico")

    geo = d["serie"].map(lambda s: catalogos.ciudad(cat[s]["ciudad_fuente"]) if s in cat else None)
    marcar(geo.isna(), "ciudad_no_catalogada")
    for col in ("ciudad_id", "ciudad", "estado", "region"):
        d[col] = geo.map(lambda g, c=col: g[c] if g else None)
    d["componente"] = d["serie"].map(lambda s: cat[s]["componente"] if s in cat else None)
    marcar(~d["componente"].isin(catalogos.COMPONENTES), "componente_no_catalogado")

    malo = d[d["motivo"] != ""]
    bueno, superados = resolver_duplicados(d[d["motivo"] == ""], ["serie", "fecha"], "indice")
    cuarentena = pd.concat([malo, superados], ignore_index=True)
    orden = ["ciudad_id", "componente", "fecha"]
    return bueno[COLS_INPP].sort_values(orden).reset_index(drop=True), cuarentena


def resolver_duplicados(d, llave, valor, tolerancia=1e-9):
    """Una misma observacion puede llegar en varias capturas (historico y periodicas).

    - Copias con el mismo valor: es traslape, no error. Se conserva la primera
      captura (asi la procedencia de cada fila no cambia en cada corrida).
    - Copias con valor distinto (la fuente reviso el dato): gana el valor de la
      captura mas reciente y las versiones anteriores van a cuarentena.
    """
    d = d.sort_values([*llave, "capturado_utc", "archivo_bronce"])
    vigente = d.groupby(llave)[valor].transform("last")
    igual = (d[valor] - vigente).abs() <= tolerancia
    superados = d[~igual].copy()
    superados["motivo"] = "valor_superado_por_captura_mas_reciente"
    return d[igual].drop_duplicates(llave, keep="first").copy(), superados


# --- Banxico --------------------------------------------------------------------
def leer_banxico(dir_bronce=None, serie="SF43718"):
    base = (dir_bronce or config.DIR_BRONCE) / "banxico_sie"
    filas = []
    for ruta in sorted(base.rglob("*.json.gz")):
        meta = _meta(ruta)
        try:
            payload = json.loads(gzip.open(ruta).read())
        except (json.JSONDecodeError, OSError):
            filas.append(("", "", _rel(ruta, base), meta.get("capturado_utc", "")))
            continue
        for s in ((payload or {}).get("bmx") or {}).get("series") or []:
            if s.get("idSerie") != serie:
                continue
            for dato in s.get("datos") or []:
                filas.append(
                    (
                        str(dato.get("fecha", "")).strip(),
                        str(dato.get("dato", "")).strip(),
                        _rel(ruta, base),
                        meta.get("capturado_utc", ""),
                    )
                )
    return pd.DataFrame(filas, columns=["periodo", "valor", "archivo_bronce", "capturado_utc"])


def limpiar_banxico(crudo):
    d = crudo.copy()
    d["motivo"] = ""

    def marcar(mascara, motivo):
        d.loc[mascara & (d["motivo"] == ""), "motivo"] = motivo

    marcar((d["periodo"] == "") & (d["valor"] == ""), "archivo_no_legible")
    marcar(d["valor"].str.upper().isin(["N/E", "NE", "N/D"]), "valor_no_existe_en_fuente_NE")
    d["fecha"] = pd.to_datetime(d["periodo"], format="%d/%m/%Y", errors="coerce")
    marcar(d["fecha"].isna(), "fecha_no_interpretable")
    d["fix"] = pd.to_numeric(d["valor"].str.replace(",", "", regex=False), errors="coerce")
    marcar(d["fix"].isna(), "valor_no_numerico")
    malo = d[d["motivo"] != ""]
    bueno, superados = resolver_duplicados(d[d["motivo"] == ""], ["fecha"], "fix")
    cuarentena = pd.concat([malo, superados], ignore_index=True)
    return bueno[COLS_FIX].sort_values("fecha").reset_index(drop=True), cuarentena
