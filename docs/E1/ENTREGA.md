# Entrega E1 · ObraPrecio (TRUSTED DATA LAB)

Equipo: Julio Alberto Orozco Téllez · Ángel Salvador Álvarez · José Rey Sánchez Navarro (solo Calidad en los Sistemas de Información) · Etiqueta: `e1` · Tablero: pendiente (E2)

## Resumen en tres líneas
ObraPrecio responde cuánto ha subido el costo de construir vivienda en 46 ciudades de México y qué lo mueve (materiales, maquinaria o mano de obra), con el índice oficial de INEGI integrado con el tipo de cambio de Banxico.
En E1 el flujo bronce → puerta de calidad → plata → oro quedó automatizado: 93,572 registros de INEGI y 2,509 de Banxico pasan por un contrato Pandera, y los 24,604 que no pasan están en cuarentena con su motivo.
El proyecto cambió de tema respecto a E0 (antes Observatorio Eléctrico); el porqué y el plan nuevo están en [pivote-obraprecio.md](pivote-obraprecio.md).

## Cómo reproducir
```bash
pip install -r requirements-dev.txt
python -m pytest                 # 45 pruebas, sin internet
python -m pipeline.ejecutar      # bronce -> plata -> oro + cuarentena + reporte
jupyter nbconvert --to notebook --execute --inplace docs/E1/limpieza.ipynb
```

## Ingeniería de Datos
| Entregable de E1 | Evidencia | Nota del equipo |
|---|---|---|
| **1. Pipeline de limpieza y preprocesamiento** | Cuaderno con evidencia: [limpieza.ipynb](limpieza.ipynb) · Código que corre en automático: [pipeline/](../../pipeline/) | El cuaderno usa las mismas funciones que el pipeline; no hay dos versiones de la lógica |
| Valores faltantes: mecanismo e imputación | [limpieza.ipynb §3](limpieza.ipynb) · [`limpieza.diagnostico_faltantes`](../../pipeline/limpieza.py) | INEGI: MAR estructural (0 huecos interiores; ji-cuadrada contra década, componente y región). No se imputa hacia atrás; oro arranca en 2004 con panel completo. Método para huecos futuros elegido con un experimento de enmascarado (622 valores). Banxico: MAR por calendario, imputación LOCF con bandera `imputado` |
| Atípicos y ruido (IQR, Z robusto, Isolation Forest) | [limpieza.ipynb §4](limpieza.ipynb) · [`oro.panel_mensual`](../../pipeline/oro.py) | Los tres métodos, con banderas y votos por fila. Hallazgo: mano de obra y maquinaria son series escalonadas y requieren una referencia distinta. Tratamiento: marcar y winsorizar en columna aparte, sin borrar |
| Normalización y estandarización | [limpieza.ipynb §5](limpieza.ipynb) | `indice_minmax` y `var_mensual_z`, por serie; se verifica 0–1 y media 0, desviación 1 en las 188 series |
| Discretización y jerarquías conceptuales | [limpieza.ipynb §6](limpieza.ipynb) · [pipeline/catalogos.py](../../pipeline/catalogos.py) | `nivel_inflacion` (cortes de negocio), `costo_relativo` (terciles); jerarquías ciudad → estado → región y mes → trimestre → año |
| Reducción de datos | [limpieza.ipynb §7](limpieza.ipynb) · [data/oro/](../../data/oro/) | Agregación (68,968 → 352 filas región-año), selección de variables con correlación y PCA, muestreo estratificado con semilla |
| **2. Integración y resolución de conflictos** | [pipeline/plata.py](../../pipeline/plata.py) · [limpieza.ipynb §1](limpieza.ipynb) · [extractores/inegi.py](../../extractores/inegi.py) | Dos fuentes heterogéneas: INEGI (CSV ancho, Windows-1252, mensual, fechas "Ene 2023") y Banxico (JSON, UTF-8, diario). Nueve discrepancias documentadas con su regla de resolución |
| **3. Puerta de calidad automática (Pandera)** | [pipeline/puerta.py](../../pipeline/puerta.py) · [calidad/reporte-puerta.json](../../calidad/reporte-puerta.json) · [limpieza.ipynb §2](limpieza.ipynb) | Esquemas estrictos con validación completa; 6 revisiones de conjunto; una falla grave detiene el flujo con código 1 |
| Cuarentena con motivo documentado | [data/cuarentena/](../../data/cuarentena/) · [README de cuarentena](../../data/cuarentena/README.md) | 24,604 registros `N/E` de INEGI con motivo, etapa y archivo de origen. Balance verificado: bronce = plata + cuarentena + duplicados idénticos |
| Automatización del flujo | [.github/workflows/captura.yml](../../.github/workflows/captura.yml) · [.github/workflows/ci.yml](../../.github/workflows/ci.yml) · [calidad/bitacora-pipeline.csv](../../calidad/bitacora-pipeline.csv) | El pipeline corre a diario después de la captura y en cada cambio de código |
| **4. Ficha técnica y relatoría** | Este archivo · [relatoria-E1.md](../relatoria-E1.md) | |

### Cifras de la corrida entregada
| Fuente | Registros en bronce | A plata | A cuarentena | Duplicados idénticos | Aceptado |
|---|---|---|---|---|---|
| INEGI · INPP construcción residencial por ciudad | 93,572 | 68,968 | 24,604 | 0 | 73.71 % |
| Banxico · FIX | 2,509 | 2,481 | 0 | 28 | 98.88 % |

Cobertura: 188 series (46 ciudades más Nacional × 4 componentes), enero de 1973 a julio de 2025; tipo de cambio de enero de 2017 a noviembre de 2026. Capa oro: 48,692 filas desde enero de 2004.

## Análisis Estadístico
| Criterio de la rúbrica | Evidencia | Nota del equipo |
|---|---|---|
| Caracterización, estacionariedad, cuatro modelos, métricas y residuos | Pendiente | Se trabaja sobre `data/oro/obraprecio_ciudad_mensual.csv`; se entrega por separado dentro del plazo de la materia |

## Calidad en los Sistemas de Información
| Criterio de la rúbrica | Evidencia | Nota del equipo |
|---|---|---|
| Integración continua | [.github/workflows/ci.yml](../../.github/workflows/ci.yml) · [tests/](../../tests/) | ruff + 45 pruebas + pipeline completo en cada cambio |
| Registro de defectos | [calidad/defectos-e1.csv](../../calidad/defectos-e1.csv) | 6 defectos encontrados y corregidos al construir E1 |
| Insumos de fiabilidad | [calidad/bitacora-captura.csv](../../calidad/bitacora-captura.csv) · [calidad/bitacora-pipeline.csv](../../calidad/bitacora-pipeline.csv) | Una fila por ejecución, con estado y duración |
| Fiabilidad y disponibilidad, seguridad, requerimientos y plan SQA | Pendiente | A cargo de José Rey; se entrega por separado dentro del plazo de la materia |

## Limitaciones conocidas
1. El último dato de la estructura de INEGI que se consulta (base julio 2019 = 100) es **julio de 2025**. Falta localizar la estructura vigente y encadenarla.
2. El tipo de cambio en bronce inicia en 2017; en oro, las columnas `fix_*` están vacías de 2004 a 2016.
3. El índice mide variación, no precios en pesos. El precio base por ciudad saldrá de las entrevistas con ferreterías y contratistas.
4. La captura de CENACE de E0 sigue activa en el flujo diario, pero ya no es parte del producto.

## Uso de IA generativa
Se usó Claude (Anthropic) para: localizar el servicio público de exportación de INEGI y escribir su extractor; generar el código del pipeline, la puerta de calidad, las pruebas y los flujos de GitHub Actions; ejecutar el cuaderno y redactar el borrador de esta ficha y de la relatoría. El equipo definió el tema, las reglas del proyecto y revisó lo entregado.

## Issues de la entrega anterior
E0 no recibió issues formales. Pendientes propios que se atienden aquí: el equipo de E0 tenía un integrante sin nombre en la ficha (ya está completo) y la entrevista con cliente sigue pendiente; se reprogramó con el guion nuevo de ObraPrecio.
