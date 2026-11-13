# Cuarentena

Aquí cae todo registro que **no pasó** de bronce a plata. Nada se borra en silencio: cada fila conserva el valor original, el archivo de bronce del que salió y el motivo del rechazo. Los archivos se regeneran completos en cada corrida de `python -m pipeline.ejecutar`.

| Columna | Significado |
|---|---|
| `etapa` | `formato` (no se pudo interpretar o cruzar con catálogo) o `puerta` (rompe una regla del contrato Pandera) |
| `motivo` | Regla que rompió (ver tabla siguiente) |
| `serie`, `periodo`, `valor` | Tal como llegaron de la fuente |
| `archivo_bronce`, `capturado_utc` | Procedencia, para rastrear el registro hasta la respuesta original |

| Motivo | Qué significa | Qué se hace |
|---|---|---|
| `valor_no_existe_en_fuente_NE` | La fuente respondió `N/E`: la serie no existía en ese periodo | Faltante estructural; no se imputa (ver `docs/E1/limpieza.ipynb` §3) |
| `valor_vacio`, `valor_no_numerico` | Celda vacía o texto donde debe ir un número | Revisar la respuesta de bronce |
| `fecha_no_interpretable` | El periodo no tiene el formato esperado | Revisar si la fuente cambió su formato |
| `serie_no_catalogada`, `ciudad_no_catalogada`, `componente_no_catalogado` | Llegó algo que no está en los catálogos | Actualizar `extractores/inegi_series.json` o `pipeline/catalogos.py` |
| `valor_superado_por_captura_mas_reciente` | La fuente revisó una cifra; esta es la versión anterior | Solo informativo: queda el historial de revisiones |
| `indice: ...`, `fecha: ...`, `fix: ...` | Regla del esquema Pandera (rango, catálogo, llave única...) | Revisar el registro; si la regla está mal calibrada, ajustarla con un issue |
| `salto_mensual_mayor_a_60_pct` | Cambio mensual no creíble: probable error de captura | Comparar con la fuente |

El resumen de cada corrida está en [`calidad/reporte-puerta.json`](../../calidad/reporte-puerta.json).
