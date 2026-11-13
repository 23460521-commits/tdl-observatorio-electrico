"""Orquestador: bronce -> puerta de calidad -> plata -> oro (y cuarentena).

Uso:  python -m pipeline.ejecutar

Escribe:
  data/plata/inpp_construccion.csv, data/plata/fix_diario.csv
  data/cuarentena/<fuente>.csv            registros rechazados, con `motivo` y `etapa`
  data/oro/*.csv                          tablas de analisis
  calidad/reporte-puerta.json             conteos, motivos y revisiones de la corrida
  calidad/bitacora-pipeline.csv           una fila por corrida (fiabilidad del pipeline)

Sale con codigo 1 si falla una revision grave: asi el flujo de GitHub Actions no
publica datos que no pasaron la puerta.
"""

import csv
import hashlib
import json
import sys
import time

import pandas as pd

from extractores import bronce, config, inegi
from pipeline import limpieza, oro, plata, puerta

CAMPOS = [
    "ejecucion_id",
    "disparador",
    "inicio_utc",
    "duracion_s",
    "estado",
    "bronce_inpp",
    "plata_inpp",
    "cuarentena_inpp",
    "bronce_fix",
    "plata_fix",
    "cuarentena_fix",
    "oro_panel",
    "mensaje",
]
COLS_CUARENTENA = [
    "etapa",
    "motivo",
    "serie",
    "periodo",
    "valor",
    "archivo_bronce",
    "capturado_utc",
]


def _relativa(ruta):
    try:
        return ruta.relative_to(config.RAIZ).as_posix()
    except ValueError:  # carpeta fuera del repositorio (pruebas)
        return ruta.name


def _guardar(df, ruta):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ruta, index=False, lineterminator="\n", date_format="%Y-%m-%d")
    return {
        "archivo": _relativa(ruta),
        "filas": len(df),
        "sha256": hashlib.sha256(ruta.read_bytes()).hexdigest(),
    }


def _cuarentena(partes):
    filas = []
    for etapa, df in partes:
        if len(df):
            d = df.copy()
            d["etapa"] = etapa
            if "periodo" not in d:
                d["periodo"] = d["fecha"].astype(str)
            if "valor" not in d:
                d["valor"] = d.get("indice", d.get("fix")).astype(str)
            if "serie" not in d:
                d["serie"] = "SF43718"
            filas.append(d.reindex(columns=COLS_CUARENTENA))
    if not filas:
        return pd.DataFrame(columns=COLS_CUARENTENA)
    return (
        pd.concat(filas, ignore_index=True).sort_values(COLS_CUARENTENA[:4]).reset_index(drop=True)
    )


def correr(dir_bronce=None, dir_plata=None, dir_oro=None, dir_cuarentena=None, series=None):
    dir_plata = dir_plata or config.DIR_PLATA
    dir_oro = dir_oro or config.DIR_ORO
    dir_cuarentena = dir_cuarentena or config.DIR_CUARENTENA
    series = series or inegi.cargar_series()

    # 1. Bronce -> limpieza de formato (plata.py)
    crudo_inpp = plata.leer_inegi(dir_bronce)
    inpp, q_inpp_formato = plata.limpiar_inegi(crudo_inpp, series)
    crudo_fix = plata.leer_banxico(dir_bronce)
    fix, q_fix_formato = plata.limpiar_banxico(crudo_fix)

    # 2. Puerta de calidad (puerta.py): contrato Pandera + regla de salto implausible
    inpp, q_inpp_puerta = puerta.validar(inpp, puerta.ESQUEMA_INPP)
    saltos = puerta.saltos_implausibles(inpp)
    q_inpp_salto = inpp.loc[saltos].assign(
        motivo=f"salto_mensual_mayor_a_{puerta.SALTO_MAXIMO_PCT:.0f}_pct"
    )
    inpp = inpp.drop(index=saltos).reset_index(drop=True)
    fix, q_fix_puerta = puerta.validar(fix, puerta.ESQUEMA_FIX)
    revisiones = puerta.revisiones_de_conjunto(inpp, fix, series)

    q_inpp = _cuarentena(
        [("formato", q_inpp_formato), ("puerta", q_inpp_puerta), ("puerta", q_inpp_salto)]
    )
    q_fix = _cuarentena([("formato", q_fix_formato), ("puerta", q_fix_puerta)])

    # 3. Oro
    panel = oro.panel_mensual(inpp, fix)
    salidas = [
        _guardar(inpp, dir_plata / "inpp_construccion.csv"),
        _guardar(limpieza.completar_calendario_fix(fix), dir_plata / "fix_diario.csv"),
        _guardar(q_inpp, dir_cuarentena / "inegi_inpp.csv"),
        _guardar(q_fix, dir_cuarentena / "banxico_sie.csv"),
        _guardar(oro.redondear(panel), dir_oro / "obraprecio_panel_mensual.csv"),
        _guardar(
            oro.redondear(oro.ciudad_mensual(panel)), dir_oro / "obraprecio_ciudad_mensual.csv"
        ),
        _guardar(
            oro.redondear(oro.resumen_region_anual(panel)), dir_oro / "resumen_region_anual.csv"
        ),
        _guardar(oro.redondear(oro.ranking_ciudades(panel)), dir_oro / "ranking_ciudades.csv"),
    ]

    def fuente(crudo, limpio, q):
        return {
            "registros_bronce": len(crudo),
            "registros_plata": len(limpio),
            "registros_cuarentena": len(q),
            "duplicados_identicos_colapsados": len(crudo) - len(limpio) - len(q),
            "pct_aceptado": round(len(limpio) / max(len(crudo), 1) * 100, 2),
            "cuarentena_por_motivo": q.groupby(["etapa", "motivo"])
            .size()
            .rename("n")
            .reset_index()
            .to_dict("records"),
        }

    return {
        "inegi_inpp": fuente(crudo_inpp, inpp, q_inpp),
        "banxico_sie": fuente(crudo_fix, fix, q_fix),
        "cobertura": {
            "inpp_desde": str(inpp["fecha"].min().date()),
            "inpp_hasta": str(inpp["fecha"].max().date()),
            "ciudades": int(inpp["ciudad_id"].nunique()),
            "series": int(inpp["serie"].nunique()),
            "fix_desde": str(fix["fecha"].min().date()),
            "fix_hasta": str(fix["fecha"].max().date()),
            "oro_desde": str(panel["fecha"].min().date()),
            "oro_filas": len(panel),
        },
        "estructura_inegi": {
            "vigente": config.INEGI_ESTRUCTURA,
            "archivos_de_estructuras_anteriores_no_leidos": crudo_inpp.attrs.get("ignorados", {}),
        },
        "revisiones_de_conjunto": revisiones,
        "salidas": salidas,
    }


def main():
    inicio, t0 = bronce.ahora_utc(), time.monotonic()
    estado, mensaje, rep = "exito", "", {}
    try:
        rep = correr()
        graves = [
            r["revision"] for r in rep["revisiones_de_conjunto"] if r["grave"] and not r["ok"]
        ]
        if graves:
            estado, mensaje = "fallo", "revision grave: " + ", ".join(graves)
    except Exception as e:  # se registra en la bitacora y se vuelve a lanzar abajo
        estado, mensaje = "fallo", f"{type(e).__name__}: {e}"[:400]
    dur = round(time.monotonic() - t0, 2)

    if rep:
        # Sin hora ni duracion: el reporte solo cambia cuando cambian los datos
        (config.DIR_CALIDAD / "reporte-puerta.json").write_text(
            json.dumps({"estado": estado, **rep}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    archivo = config.DIR_CALIDAD / "bitacora-pipeline.csv"
    nuevo = not archivo.exists() or archivo.stat().st_size == 0
    i, b = rep.get("inegi_inpp", {}), rep.get("banxico_sie", {})
    with open(archivo, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS, lineterminator="\n")
        if nuevo:
            w.writeheader()
        w.writerow(
            {
                "ejecucion_id": bronce.id_ejecucion(),
                "disparador": bronce.disparador(),
                "inicio_utc": inicio.isoformat(timespec="seconds"),
                "duracion_s": dur,
                "estado": estado,
                "bronce_inpp": i.get("registros_bronce", ""),
                "plata_inpp": i.get("registros_plata", ""),
                "cuarentena_inpp": i.get("registros_cuarentena", ""),
                "bronce_fix": b.get("registros_bronce", ""),
                "plata_fix": b.get("registros_plata", ""),
                "cuarentena_fix": b.get("registros_cuarentena", ""),
                "oro_panel": rep.get("cobertura", {}).get("oro_filas", ""),
                "mensaje": mensaje,
            }
        )

    print(f"[{estado.upper()}] pipeline en {dur}s {mensaje}")
    for nombre in ("inegi_inpp", "banxico_sie"):
        r = rep.get(nombre)
        if r:
            print(
                f"  {nombre}: bronce={r['registros_bronce']} plata={r['registros_plata']} "
                f"cuarentena={r['registros_cuarentena']} ({r['pct_aceptado']} % aceptado)"
            )
            for m in r["cuarentena_por_motivo"]:
                print(f"      {m['etapa']:8} {m['n']:>6}  {m['motivo']}")
    for r in rep.get("revisiones_de_conjunto", []):
        print(f"  [{'OK' if r['ok'] else 'ATENCION'}] {r['revision']}: {r['detalle']}")
    sys.exit(0 if estado == "exito" else 1)


if __name__ == "__main__":
    main()
