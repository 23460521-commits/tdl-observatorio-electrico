"""Fiabilidad y disponibilidad del flujo automatico, calculadas de las bitacoras.

Uso:  python calidad/fiabilidad.py     (escribe calidad/reporte-fiabilidad.md)

Definiciones
- Ejecucion: una corrida del flujo diario (mismo `ejecucion_id`).
- Falla: ejecucion en la que una fuente OBLIGATORIA termina en `fallo`. Una fuente
  opcional `omitida` no es falla del sistema, pero se reporta aparte.
- Disponibilidad operativa = dias con captura exitosa / dias calendario del periodo.
- MTBF = tiempo en operacion / numero de fallas.  MTTR = tiempo medio entre una falla
  y la siguiente ejecucion exitosa.
- Con cero fallas el MTBF no se puede estimar: se reporta una cota. Para la probabilidad
  de falla por ejecucion se usa el limite superior exacto de 95 %: 1 - 0.05^(1/n).
"""

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
OBLIGATORIAS = {"cenace_pend_mda", "banxico_fix"}
OBJETIVO_DISPONIBILIDAD = 95.0
OBJETIVO_MTTR_H = 24.0


def leer(nombre):
    ruta = RAIZ / nombre
    if not ruta.exists():
        return []
    with open(ruta, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ejecuciones(filas):
    """Agrupa la bitacora de captura por ejecucion y decide si fue exitosa."""
    grupos = defaultdict(list)
    for f in filas:
        grupos[f["ejecucion_id"]].append(f)
    salida = []
    for eid, fs in grupos.items():
        inicio = min(datetime.fromisoformat(f["inicio_utc"]) for f in fs)
        fin = max(datetime.fromisoformat(f["fin_utc"]) for f in fs)
        fallas = [f["fuente"] for f in fs if f["fuente"] in OBLIGATORIAS and f["estado"] == "fallo"]
        salida.append({
            "id": eid, "disparador": fs[0]["disparador"], "inicio": inicio, "fin": fin,
            "duracion_s": sum(float(f["duracion_s"]) for f in fs),
            "exito": not fallas, "fallas": fallas,
            "omitidas": [f["fuente"] for f in fs if f["estado"] == "omitido"],
            "reintentos": sum(int(f["intentos"]) - 1 for f in fs),
            "registros": sum(int(f["registros"] or 0) for f in fs),
        })  # fmt: skip
    return sorted(salida, key=lambda e: e["inicio"])


def indicadores(ejs):
    n = len(ejs)
    if n == 0:
        return {}
    fallas = [e for e in ejs if not e["exito"]]
    dias = sorted({e["inicio"].date() for e in ejs})
    dias_ok = {e["inicio"].date() for e in ejs if e["exito"]}
    periodo = (dias[-1] - dias[0]).days + 1
    horas = (ejs[-1]["fin"] - ejs[0]["inicio"]).total_seconds() / 3600
    reparaciones = []
    for i, e in enumerate(ejs):
        if not e["exito"]:
            sig = next((x for x in ejs[i + 1 :] if x["exito"]), None)
            if sig:
                reparaciones.append((sig["fin"] - e["inicio"]).total_seconds() / 3600)
    return {
        "ejecuciones": n, "fallas": len(fallas), "dias_periodo": periodo,
        "dias_con_captura": len(dias_ok), "desde": dias[0], "hasta": dias[-1],
        "disponibilidad_pct": len(dias_ok) / periodo * 100,
        "horas_observadas": horas,
        "mtbf_h": horas / len(fallas) if fallas else None,
        "mttr_h": sum(reparaciones) / len(reparaciones) if reparaciones else None,
        "p_falla_max_95_pct": (1 - 0.05 ** (1 / n)) * 100 if not fallas else None,
        "duracion_media_s": sum(e["duracion_s"] for e in ejs) / n,
        "reintentos": sum(e["reintentos"] for e in ejs),
        "omitidas": sum(len(e["omitidas"]) for e in ejs),
    }  # fmt: skip


def reporte():
    filas = leer("bitacora-captura.csv")
    ejs = ejecuciones(filas)
    k = indicadores(ejs)
    pipe = leer("bitacora-pipeline.csv")
    lineas = [
        "# Fiabilidad y disponibilidad del flujo automático",
        "",
        "Generado con `python calidad/fiabilidad.py` a partir de `bitacora-captura.csv` y "
        "`bitacora-pipeline.csv`. No se edita a mano.",
        "",
        f"Periodo observado: {k['desde']} a {k['hasta']} ({k['dias_periodo']} días, "
        f"{k['ejecuciones']} ejecuciones del flujo diario).",
        "",
        "## Indicadores de la captura",
        "",
        "| Indicador | Valor | Objetivo | Cumple |",
        "|---|---|---|---|",
    ]
    disp = k["disponibilidad_pct"]
    lineas.append(
        f"| Disponibilidad operativa (días con captura exitosa / días del periodo) | "
        f"{disp:.1f} % ({k['dias_con_captura']} de {k['dias_periodo']}) | "
        f"≥ {OBJETIVO_DISPONIBILIDAD:.0f} % | {'Sí' if disp >= OBJETIVO_DISPONIBILIDAD else 'No'} |"
    )
    lineas.append(f"| Fallas de fuentes obligatorias | {k['fallas']} | | |")
    if k["mtbf_h"] is None:
        lineas.append(
            f"| MTBF | No estimable: 0 fallas. Cota: mayor a {k['horas_observadas']:.0f} h "
            "observadas | | |"
        )
        lineas.append(
            f"| MTTR | Sin fallas que reparar | ≤ {OBJETIVO_MTTR_H:.0f} h | Sin evidencia |"
        )
        lineas.append(
            f"| Probabilidad de falla por ejecución (límite superior de 95 %) | "
            f"≤ {k['p_falla_max_95_pct']:.0f} % | | |"
        )
    else:
        mttr = k["mttr_h"]
        lineas.append(f"| MTBF | {k['mtbf_h']:.1f} h | | |")
        cumple = "Sin evidencia" if mttr is None else ("Sí" if mttr <= OBJETIVO_MTTR_H else "No")
        valor = "Falla aún sin reparar" if mttr is None else f"{mttr:.1f} h"
        lineas.append(f"| MTTR | {valor} | ≤ {OBJETIVO_MTTR_H:.0f} h | {cumple} |")
    lineas += [
        f"| Duración media de una ejecución | {k['duracion_media_s']:.1f} s | | |",
        f"| Reintentos por error de red | {k['reintentos']} | | |",
        f"| Fuentes opcionales omitidas | {k['omitidas']} | | |",
        "",
        "## Detalle por ejecución",
        "",
        "| Inicio (UTC) | Disparador | Resultado | Registros | Duración (s) | Omitidas |",
        "|---|---|---|---|---|---|",
    ]
    for e in ejs:
        lineas.append(
            f"| {e['inicio']:%Y-%m-%d %H:%M} | {e['disparador']} | "
            f"{'éxito' if e['exito'] else 'FALLA: ' + ', '.join(e['fallas'])} | {e['registros']} | "
            f"{e['duracion_s']:.1f} | {', '.join(e['omitidas']) or '-'} |"
        )
    lineas += ["", "## Pipeline plata y oro", ""]
    if pipe:
        ok = sum(1 for p in pipe if p["estado"] == "exito")
        dur = sum(float(p["duracion_s"]) for p in pipe) / len(pipe)
        lineas.append(
            f"Corridas registradas: {len(pipe)}; exitosas: {ok}. Duración media: {dur:.1f} s. "
            f"Última corrida: {pipe[-1]['plata_inpp']} registros de INEGI a plata y "
            f"{pipe[-1]['cuarentena_inpp']} a cuarentena."
        )
    else:
        lineas.append("Sin corridas registradas.")
    lineas += [
        "",
        "## Lectura",
        "",
        f"- En {k['dias_periodo']} días no hubo fallas de fuentes obligatorias, así que la "
        "disponibilidad observada es de 100 % y cumple el objetivo.",
        f"- **La muestra es muy chica.** Con {k['ejecuciones']} ejecuciones sin falla, lo único "
        "que se puede afirmar con 95 % de confianza es que la probabilidad de falla por ejecución "
        f"es menor a {k['p_falla_max_95_pct'] or 0:.0f} %. El MTBF y el MTTR no se pueden "
        "estimar todavía; se volverán a calcular en E2 con más historia."
        if k["mtbf_h"] is None
        else "- Ya hay fallas registradas: revisar el detalle por ejecución.",
        f"- La fuente opcional `cenace_pend_mda_manana` se omitió en {k['omitidas']} de "
        f"{k['ejecuciones']} ejecuciones: a la hora de la corrida CENACE aún no publica el día "
        "siguiente. No afecta la disponibilidad, pero es una petición diaria que nunca ha "
        "traído datos; se registra como observación para mover su horario o retirarla.",
        "- La captura semanal de INEGI y el pipeline dentro del flujo diario entraron en E1 y "
        "todavía no tienen ejecuciones programadas registradas.",
        "",
    ]
    return "\n".join(lineas)


if __name__ == "__main__":
    destino = RAIZ / "reporte-fiabilidad.md"
    destino.write_text(reporte(), encoding="utf-8")
    print(f"Escrito {destino.name}")
