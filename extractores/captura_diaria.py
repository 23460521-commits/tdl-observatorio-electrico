"""Captura diaria: lo que corre GitHub Actions una vez al dia.

Cada fuente se registra en calidad/bitacora-captura.csv con su estado:
  exito    la fuente respondio con datos validos
  fallo    fuente obligatoria sin datos validos (cuenta para la fiabilidad)
  omitido  fuente opcional sin datos; no cuenta como falla

CENACE se pide con 4 dias hacia atras: si una ejecucion falla, la siguiente
recupera el hueco. Los duplicados que esto genera se resuelven en la capa plata.

Uso:  python -m extractores.captura_diaria
"""
import sys
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from extractores import bronce, cenace, config, open_meteo
from extractores.base import ExtractorEtico


def ejecutar(fuente, funcion, extractor, obligatoria=True):
    inicio = bronce.ahora_utc()
    t0 = time.monotonic()
    registros, estado, mensaje = 0, "exito", ""
    try:
        registros = funcion()
    except Exception as e:  # se registra cualquier falla; no se oculta
        estado = "fallo" if obligatoria else "omitido"
        mensaje = f"{type(e).__name__}: {e}"[:400]
    bronce.registrar({
        "ejecucion_id": bronce.id_ejecucion(),
        "disparador": bronce.disparador(),
        "fuente": fuente,
        "inicio_utc": inicio.isoformat(timespec="seconds"),
        "fin_utc": bronce.ahora_utc().isoformat(timespec="seconds"),
        "duracion_s": round(time.monotonic() - t0, 2),
        "estado": estado,
        "registros": registros,
        "intentos": extractor.ultimos_intentos,
        "mensaje": mensaje,
    })
    print(f"[{estado.upper():7}] {fuente}: {registros} registros {mensaje}")
    return estado


def main():
    hoy = datetime.now(ZoneInfo(config.ZONA_HORARIA)).date()
    ahora = bronce.ahora_utc()
    subruta = f"diario/fecha_captura={ahora:%Y-%m-%d}"
    sello = f"{ahora:%H%M%S}Z"
    ex = ExtractorEtico()

    def cenace_reciente():
        total = 0
        for i, grupo in enumerate(cenace.grupos(cenace.cargar_zonas())):
            _, res = cenace.capturar(
                ex, grupo, hoy - timedelta(days=3), hoy, subruta, f"{sello}_mda_reciente_g{i}"
            )
            total += res["valores"]
        return total

    def cenace_manana():
        total = 0
        manana = hoy + timedelta(days=1)
        for i, grupo in enumerate(cenace.grupos(cenace.cargar_zonas())):
            _, res = cenace.capturar(ex, grupo, manana, manana, subruta, f"{sello}_mda_manana_g{i}")
            total += res["valores"]
        return total

    def clima():
        _, res = open_meteo.capturar_pronostico(ex, subruta, f"{sello}_pronostico")
        return res["valores"]

    estados = [
        ejecutar("cenace_pend_mda", cenace_reciente, ex),
        ejecutar("cenace_pend_mda_manana", cenace_manana, ex, obligatoria=False),
        ejecutar("open_meteo", clima, ex),
    ]
    sys.exit(1 if "fallo" in estados else 0)


if __name__ == "__main__":
    main()
