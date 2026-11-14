"""Publica el pronostico en la capa oro para que el tablero lo muestre.

Uso:  python -m laboratorio.pronosticar

Los modelos se eligieron en docs/E1/pronostico.ipynb con validacion de origen movil
(36 origenes). Aqui solo se reajustan con todos los datos disponibles y se escribe
data/oro/pronostico_mensual.csv. El error esperado por horizonte sale de esa validacion:
si cambia el modelo elegido, hay que actualizar ELEGIDOS.
"""

import warnings

import pandas as pd

from extractores import config
from laboratorio import modelos as M

HORIZONTE = 12
# ciudad -> SARIMA (orden, estacional) y MAPE de validacion (%) a 1, 3, 6 y 12 meses
ELEGIDOS = {
    "colima": {
        "sarima": ((3, 1, 3), (1, 0, 1, 12)),
        "mape": {
            "sarima": {1: 0.43, 3: 1.12, 6: 1.56, 12: 3.03},
            "holt_winters": {1: 0.63, 3: 1.27, 6: 1.43, 12: 2.34},
        },
    },  # fmt: skip
    "nacional": {
        "sarima": ((0, 1, 2), (1, 0, 1, 12)),
        "mape": {
            "sarima": {1: 0.30, 3: 0.74, 6: 1.12, 12: 1.75},
            "holt_winters": {1: 0.29, 3: 0.89, 6: 1.49, 12: 2.20},
        },
    },  # fmt: skip
}


def _error_esperado(mape, h):
    """MAPE del horizonte validado mas cercano por arriba (1, 3, 6 o 12 meses)."""
    return mape[min(k for k in mape if k >= h)]


def pronosticar(tabla, h=HORIZONTE):
    filas = []
    for ciudad, cfg in ELEGIDOS.items():
        y = M.serie_mensual(tabla, ciudad)
        nombre = tabla.loc[tabla["ciudad_id"] == ciudad, "ciudad"].iloc[0]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            sar = M.ajustar("sarima", y, cfg["sarima"])
            hw = M.ajustar("holt_winters", y)
            p, ic80, ic95 = sar["pronosticar"](h), sar["intervalo"](h, 0.20), sar["intervalo"](h)
            p_hw = hw["pronosticar"](h)
        for i, fecha in enumerate(p.index):
            hace_un_anio = y.get(fecha - pd.DateOffset(years=1))
            filas.append({
                "ciudad_id": ciudad, "ciudad": nombre, "fecha": fecha, "horizonte_meses": i + 1,
                "ultimo_dato": y.index[-1], "indice_ultimo_dato": y.iloc[-1],
                "pronostico_sarima": p.iloc[i],
                "ic80_inf": ic80.iloc[i, 0], "ic80_sup": ic80.iloc[i, 1],
                "ic95_inf": ic95.iloc[i, 0], "ic95_sup": ic95.iloc[i, 1],
                "pronostico_holt_winters": p_hw.iloc[i],
                "var_vs_ultimo_dato_pct": (p.iloc[i] / y.iloc[-1] - 1) * 100,
                "var_anual_pct": (p.iloc[i] / hace_un_anio - 1) * 100 if hace_un_anio else None,
                "error_esperado_sarima_pct": _error_esperado(cfg["mape"]["sarima"], i + 1),
                "error_esperado_holt_winters_pct": _error_esperado(
                    cfg["mape"]["holt_winters"], i + 1
                ),
                "modelo_sarima": f"{cfg['sarima'][0]}{cfg['sarima'][1][:3]}12",
            })  # fmt: skip
    return pd.DataFrame(filas)


def frase_cliente(fila):
    """La explicacion del intervalo en palabras de quien va a construir."""
    cambio = "suba" if fila["var_vs_ultimo_dato_pct"] >= 0 else "baje"
    return (
        f"Para {fila['fecha']:%m/%Y} esperamos que construir en {fila['ciudad']} {cambio} "
        f"alrededor de {abs(fila['var_vs_ultimo_dato_pct']):.1f} % respecto a "
        f"{fila['ultimo_dato']:%m/%Y}. No es un número exacto: si se repitiera esta situación "
        f"100 veces, en unas 80 el cambio quedaría entre "
        f"{(fila['ic80_inf'] / fila['indice_ultimo_dato'] - 1) * 100:+.1f} % y "
        f"{(fila['ic80_sup'] / fila['indice_ultimo_dato'] - 1) * 100:+.1f} %. "
        "Un presupuesto que deja ese margen queda cubierto en la mayoría de los casos."
    )


def main():
    tabla = pd.read_csv(config.DIR_ORO / "obraprecio_ciudad_mensual.csv", parse_dates=["fecha"])
    p = pronosticar(tabla)
    destino = config.DIR_ORO / "pronostico_mensual.csv"
    num = p.select_dtypes("number").columns
    p.assign(**{c: p[c].round(4) for c in num}).to_csv(
        destino, index=False, lineterminator="\n", date_format="%Y-%m-%d"
    )
    print(f"Escrito {destino.name}: {len(p)} filas, {p['ciudad_id'].nunique()} ciudades")
    for h in (3, 12):
        print(
            "  "
            + frase_cliente(p[(p["ciudad_id"] == "colima") & (p["horizonte_meses"] == h)].iloc[0])
        )


if __name__ == "__main__":
    main()
