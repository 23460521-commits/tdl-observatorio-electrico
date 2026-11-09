"""Descarga de la serie historica a la capa bronce (se corre localmente, una vez).

Es reanudable: si se interrumpe o falla un bloque, al volver a correrlo salta
los bloques que ya existen y solo pide los que faltan.

Uso:
  python -m extractores.historico                       # CENACE y clima desde 2017
  python -m extractores.historico --fuente cenace --desde 2020-01-01
"""
import argparse
import hashlib
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from extractores import cenace, config, open_meteo
from extractores.base import ExtractorEtico


def _firma(zonas):
    return hashlib.sha1(",".join(zonas).encode()).hexdigest()[:8]


def historico_cenace(ex, desde, hasta):
    zonas = cenace.cargar_zonas()
    bloques = [(g, a, b) for g in cenace.grupos(zonas) for a, b in cenace.rangos(desde, hasta)]
    fallidos = []
    print(f"CENACE: {len(bloques)} bloques ({len(zonas)} zonas, {desde} a {hasta})")
    for n, (grupo, a, b) in enumerate(bloques, 1):
        subruta = f"historico/{a.year}"
        nombre = f"{a}_{b}_{_firma(grupo)}"
        if (config.DIR_BRONCE / cenace.FUENTE / subruta / f"{nombre}.json.gz").exists():
            continue
        try:
            _, res = cenace.capturar(ex, grupo, a, b, subruta, nombre)
            print(f"  [{n}/{len(bloques)}] {a}..{b}: {res['valores']} valores")
        except Exception as e:
            fallidos.append((a, b, str(e)[:200]))
            print(f"  [{n}/{len(bloques)}] {a}..{b}: FALLO {e}")
    return fallidos


def historico_clima(ex, desde, hasta):
    fallidos = []
    for anio in range(desde.year, hasta.year + 1):
        a, b = max(desde, date(anio, 1, 1)), min(hasta, date(anio, 12, 31))
        subruta, nombre = "historico", f"{a}_{b}"
        if (config.DIR_BRONCE / open_meteo.FUENTE / subruta / f"{nombre}.json.gz").exists():
            continue
        try:
            _, res = open_meteo.capturar_archivo(ex, a, b, subruta, nombre)
            print(f"  Clima {a}..{b}: {res['valores']} horas")
        except Exception as e:
            fallidos.append((a, b, str(e)[:200]))
            print(f"  Clima {a}..{b}: FALLO {e}")
    return fallidos


def main():
    hoy = datetime.now(ZoneInfo(config.ZONA_HORARIA)).date()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--fuente", choices=["cenace", "clima", "ambas"], default="ambas")
    p.add_argument("--desde", type=date.fromisoformat, default=date(2017, 1, 1))
    p.add_argument("--hasta", type=date.fromisoformat, default=None)
    args = p.parse_args()

    ex = ExtractorEtico()
    fallidos = []
    if args.fuente in ("cenace", "ambas"):
        fallidos += historico_cenace(ex, args.desde, args.hasta or hoy - timedelta(days=1))
    if args.fuente in ("clima", "ambas"):
        # el archivo de Open-Meteo se actualiza con algunos dias de retraso
        fallidos += historico_clima(ex, args.desde, args.hasta or hoy - timedelta(days=7))

    print(f"\nBloques fallidos: {len(fallidos)}")
    for a, b, msg in fallidos:
        print(f"  {a}..{b}: {msg}")
    if fallidos:
        print("Vuelve a correr el comando: solo pedira los bloques que faltan.")


if __name__ == "__main__":
    main()
