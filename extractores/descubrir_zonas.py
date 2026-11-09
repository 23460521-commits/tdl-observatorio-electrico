"""Confirma que nombres de zona de carga responde CENACE y los guarda.

Prueba cada candidata de config.ZONAS_CANDIDATAS por separado, con un dia de
hace una semana (ya publicado). Las que regresan datos se escriben en
extractores/zonas_confirmadas.json, que es lo que usan la captura diaria y el
historico. Se corre localmente y el archivo resultante se sube al repositorio.

Uso:  python -m extractores.descubrir_zonas
"""
import json
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from extractores import cenace, config
from extractores.base import ExtractorEtico


def probar(ex, zona, dia):
    try:
        r = ex.get(cenace.url_pend([zona], dia, dia))
        res = cenace.resumir(json.loads(r.content))
        if res["valores"] > 0:
            return True, f"{res['valores']} valores"
        return False, f"sin valores (status={res['status']})"
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:120]}"


def main():
    dia = datetime.now(ZoneInfo(config.ZONA_HORARIA)).date() - timedelta(days=7)
    ex = ExtractorEtico()
    confirmadas, errores_red = [], 0
    print(f"Probando {len(config.ZONAS_CANDIDATAS)} zonas con el dia {dia}...\n")
    for zona in config.ZONAS_CANDIDATAS:
        ok, detalle = probar(ex, zona, dia)
        print(f"  {'OK ' if ok else 'NO '} {zona:<14} {detalle}")
        if ok:
            confirmadas.append(zona)
        elif detalle.startswith("RuntimeError"):  # red, SSL o servidor caido
            errores_red += 1

    if not confirmadas:
        print("\nNinguna zona respondio; no se modifica zonas_confirmadas.json.")
        if errores_red:
            print("Parece un problema de conexion o de certificado SSL (ver README).")
        sys.exit(1)

    config.ARCHIVO_ZONAS.write_text(
        json.dumps({"probado_con": dia.isoformat(), "zonas": confirmadas}, indent=2),
        encoding="utf-8",
    )
    print(f"\n{len(confirmadas)} zonas guardadas en {config.ARCHIVO_ZONAS.name}")
    if not {"COLIMA", "MANZANILLO"} & set(confirmadas):
        print(
            "OJO: no se confirmo ninguna zona de Colima. Revisen el catalogo de zonas de "
            "carga de CENACE, corrijan el nombre en config.ZONAS_CANDIDATAS y repitan."
        )


if __name__ == "__main__":
    main()
