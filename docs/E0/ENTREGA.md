# Entrega E0 · Observatorio Eléctrico de Colima

Equipo: Julio Alberto Orozco Téllez · ⟨PENDIENTE: compañero/a⟩ · Etiqueta: e0 · Tablero: pendiente (E1)

## Resumen en tres líneas
Observatorio del precio horario de la electricidad en Colima, comparado con otras zonas de carga del país, para estimar cuánto vale la energía solar que una empresa produce según la hora.
Fuentes: CENACE (servicio web SW-PEND, precios por zona de carga desde 2017) y Open-Meteo (clima horario), las dos capturadas a diario con GitHub Actions.
Cliente: desarrolladores solares y empresas colimenses que evalúan sistemas de autoconsumo.

## Ingeniería de Datos
| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Pregunta y cliente | [propuesta.md §1–3](propuesta.md) · [guion-entrevista.md](guion-entrevista.md) | |
| Plan de recopilación | [propuesta.md §5](propuesta.md) | Incluye análisis de términos, licencia y robots.txt por fuente |
| Captura y serie histórica | [.github/workflows/captura.yml](../../.github/workflows/captura.yml) · [extractores/](../../extractores/) · [data/bronce/](../../data/bronce/) | ⟨PENDIENTE: enlace a la primera ejecución exitosa en Actions⟩ |

## Análisis Estadístico
| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Preguntas analíticas | [propuesta.md §4](propuesta.md) | Pronóstico (E1), experimento 2³ (E2) y MANOVA/PCA (E3) |
| Serie histórica identificada | [data/bronce/cenace_pend/historico/](../../data/bronce/cenace_pend/historico/) | Serie diaria desde 2017 (más de 36 periodos) |

## Calidad en los Sistemas de Información
| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Registros individuales de defectos y tiempo | [calidad/](../../calidad/) | Uno por integrante |
| Bitácora de captura activa | [calidad/bitacora-captura.csv](../../calidad/bitacora-captura.csv) | La alimenta el flujo de GitHub Actions |
| Tres objetivos de calidad medibles | [propuesta.md §7](propuesta.md) | Disponibilidad ≥ 95 %, MTTR ≤ 24 h, completitud ≥ 99 % |
| Pruebas automáticas (adelanto de E1) | [tests/](../../tests/) | 17 pruebas sin red |

## Uso de IA generativa
Se usó Claude (Anthropic) para: generar el código base de los extractores, las pruebas y el flujo de GitHub Actions; investigar los términos de uso y licencias de las fuentes; y redactar el borrador de la propuesta y del guion de entrevista. El equipo revisó, ejecutó y ajustó todo lo entregado.

## Issues de la entrega anterior
No aplica (primera entrega).
