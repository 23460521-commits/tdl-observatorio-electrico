# Fiabilidad y disponibilidad del flujo automático

Generado con `python calidad/fiabilidad.py` a partir de `bitacora-captura.csv` y `bitacora-pipeline.csv`. No se edita a mano.

Periodo observado: 2026-11-09 a 2026-11-14 (6 días, 6 ejecuciones del flujo diario).

## Indicadores de la captura

| Indicador | Valor | Objetivo | Cumple |
|---|---|---|---|
| Disponibilidad operativa (días con captura exitosa / días del periodo) | 100.0 % (6 de 6) | ≥ 95 % | Sí |
| Tasa de éxito por ejecución | 100.0 % (6 de 6) | | |
| Días de bitácora disponibles | 6 (2026-11-09 a 2026-11-14) | 7 (del 6 al 13 de noviembre) | No |
| Fallas de fuentes obligatorias | 0 | | |
| MTBF | No estimable: 0 fallas. Cota: mayor a 109 h observadas | | |
| MTTR | Sin fallas que reparar | ≤ 24 h | Sin evidencia |
| Probabilidad de falla por ejecución (límite superior de 95 %) | ≤ 39 % | | |
| Duración media de una ejecución | 16.6 s | | |
| Reintentos por error de red | 0 | | |
| Fuentes opcionales omitidas | 7 | | |

## Detalle por ejecución

| Inicio (UTC) | Disparador | Resultado | Registros | Duración (s) | Omitidas |
|---|---|---|---|---|---|
| 2026-11-09 21:12 | workflow_dispatch | éxito | 1158 | 8.5 | cenace_pend_mda_manana |
| 2026-11-10 11:10 | schedule | éxito | 1157 | 9.7 | cenace_pend_mda_manana |
| 2026-11-11 10:56 | schedule | éxito | 1158 | 12.9 | cenace_pend_mda_manana |
| 2026-11-12 11:06 | schedule | éxito | 1159 | 10.3 | cenace_pend_mda_manana |
| 2026-11-13 10:57 | schedule | éxito | 1160 | 10.7 | cenace_pend_mda_manana |
| 2026-11-14 10:24 | schedule | éxito | 8 | 47.8 | inegi_inpp_construccion, cenace_pend_mda_manana |

## Pipeline plata y oro

Corridas registradas: 4; exitosas: 4. Duración media: 6.4 s. Última corrida: 71788 registros de INEGI a plata y 24604 a cuarentena.

## Lectura

- **Evidencia incompleta: hay 6 días de bitácora y la entrega pide 7.** La captura programada empezó el 2026-11-09, tres días después de lo previsto; esos días no se pueden reponer y no se inventan.
- La disponibilidad A = MTBF / (MTBF + MTTR) no se puede calcular sin fallas: no hay MTBF ni MTTR. Lo que se reporta es la disponibilidad operativa (días con captura exitosa entre días del periodo).
- En 6 días no hubo fallas de fuentes obligatorias, así que la disponibilidad observada es de 100 % y cumple el objetivo.
- **La muestra es muy chica.** Con 6 ejecuciones sin falla, lo único que se puede afirmar con 95 % de confianza es que la probabilidad de falla por ejecución es menor a 39 %. El MTBF y el MTTR no se pueden estimar todavía; se volverán a calcular en E2 con más historia.
- **Fuente obligatoria de ObraPrecio: Banxico (FIX), diaria.** INEGI, la otra fuente, se captura los lunes (índice mensual) y por eso no aparece a diario. CENACE es fuente del proyecto anterior (E0): se sigue capturando por compatibilidad, pero ObraPrecio no depende de ella. Tuvo 1 falla(s) en el periodo, que no cuentan contra la disponibilidad de ObraPrecio.
- La fuente opcional `cenace_pend_mda_manana` se omitió en 7 de 6 ejecuciones: a la hora de la corrida CENACE aún no publica el día siguiente. No afecta la disponibilidad, pero es una petición diaria que nunca ha traído datos; se registra como observación para mover su horario o retirarla.
- La captura semanal de INEGI y el pipeline dentro del flujo diario entraron en E1 y todavía no tienen ejecuciones programadas registradas.
