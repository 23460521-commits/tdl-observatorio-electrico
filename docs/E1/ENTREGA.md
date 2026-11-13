# Entrega E1 · ObraPrecio (TRUSTED DATA LAB)

Equipo: Julio Alberto Orozco Téllez · Ángel Salvador Álvarez · José Rey Sánchez Navarro (solo Calidad en los Sistemas de Información) · Etiquetas: `e1` (Ingeniería de Datos) y `e1-final` (las tres materias) · Tablero: pendiente (E2)

## Resumen en tres líneas
ObraPrecio responde cuánto ha subido el costo de construir vivienda en 46 ciudades de México y qué lo mueve (materiales, maquinaria o mano de obra), con el índice oficial de INEGI integrado con el tipo de cambio de Banxico.
En E1 el flujo bronce → puerta de calidad → plata → oro quedó automatizado: 96,392 registros de INEGI y 2,509 de Banxico pasan por un contrato Pandera, y los 24,604 que no pasan están en cuarentena con su motivo.
El proyecto cambió de tema respecto a E0 (antes Observatorio Eléctrico); el porqué y el plan nuevo están en [pivote-obraprecio.md](pivote-obraprecio.md).

## Cómo reproducir
```bash
pip install -r requirements-dev.txt
python -m pytest                 # 60 pruebas, sin internet
python -m pipeline.ejecutar      # bronce -> plata -> oro + cuarentena + reporte
jupyter nbconvert --to notebook --execute --inplace docs/E1/limpieza.ipynb
jupyter nbconvert --to notebook --execute --inplace docs/E1/pronostico.ipynb
python calidad/fiabilidad.py     # recalcula disponibilidad, MTBF y MTTR
```

## Ingeniería de Datos
| Entregable de E1 | Evidencia | Nota del equipo |
|---|---|---|
| **1. Pipeline de limpieza y preprocesamiento** | Cuaderno con evidencia: [limpieza.ipynb](limpieza.ipynb) · Código que corre en automático: [pipeline/](../../pipeline/) | El cuaderno usa las mismas funciones que el pipeline; no hay dos versiones de la lógica |
| Valores faltantes: mecanismo e imputación | [limpieza.ipynb §3](limpieza.ipynb) · [`limpieza.diagnostico_faltantes`](../../pipeline/limpieza.py) | INEGI: MAR estructural (0 huecos interiores; ji-cuadrada contra década, componente y región). No se imputa hacia atrás; oro arranca en 2004 con panel completo. Método para huecos futuros elegido con un experimento de enmascarado (656 valores). Banxico: MAR por calendario, imputación LOCF con bandera `imputado` |
| Atípicos y ruido (IQR, Z robusto, Isolation Forest) | [limpieza.ipynb §4](limpieza.ipynb) · [`oro.panel_mensual`](../../pipeline/oro.py) | Los tres métodos, con banderas y votos por fila. Hallazgo: mano de obra y maquinaria son series escalonadas y requieren una referencia distinta. Tratamiento: marcar y winsorizar en columna aparte, sin borrar |
| Normalización y estandarización | [limpieza.ipynb §5](limpieza.ipynb) | `indice_minmax` y `var_mensual_z`, por serie; se verifica 0–1 y media 0, desviación 1 en las 188 series |
| Discretización y jerarquías conceptuales | [limpieza.ipynb §6](limpieza.ipynb) · [pipeline/catalogos.py](../../pipeline/catalogos.py) | `nivel_inflacion` (cortes de negocio), `costo_relativo` (terciles); jerarquías ciudad → estado → región y mes → trimestre → año |
| Reducción de datos | [limpieza.ipynb §7](limpieza.ipynb) · [data/oro/](../../data/oro/) | Agregación (71,788 → 368 filas región-año), selección de variables con correlación y PCA, muestreo estratificado con semilla |
| **2. Integración y resolución de conflictos** | [pipeline/plata.py](../../pipeline/plata.py) · [limpieza.ipynb §1](limpieza.ipynb) · [extractores/inegi.py](../../extractores/inegi.py) | Dos fuentes heterogéneas: INEGI (CSV ancho, Windows-1252, mensual, fechas "Ene 2023") y Banxico (JSON, UTF-8, diario). Nueve discrepancias documentadas con su regla de resolución |
| **3. Puerta de calidad automática (Pandera)** | [pipeline/puerta.py](../../pipeline/puerta.py) · [calidad/reporte-puerta.json](../../calidad/reporte-puerta.json) · [limpieza.ipynb §2](limpieza.ipynb) | Esquemas estrictos con validación completa; 6 revisiones de conjunto; una falla grave detiene el flujo con código 1 |
| Cuarentena con motivo documentado | [data/cuarentena/](../../data/cuarentena/) · [README de cuarentena](../../data/cuarentena/README.md) | 24,604 registros `N/E` de INEGI con motivo, etapa y archivo de origen. Balance verificado: bronce = plata + cuarentena + duplicados idénticos |
| Automatización del flujo | [.github/workflows/captura.yml](../../.github/workflows/captura.yml) · [.github/workflows/ci.yml](../../.github/workflows/ci.yml) · [calidad/bitacora-pipeline.csv](../../calidad/bitacora-pipeline.csv) | El pipeline corre a diario después de la captura y en cada cambio de código |
| **4. Ficha técnica y relatoría** | Este archivo · [relatoria-E1.md](../relatoria-E1.md) | |

### Cifras de la corrida entregada
| Fuente | Registros en bronce | A plata | A cuarentena | Duplicados idénticos | Aceptado |
|---|---|---|---|---|---|
| INEGI · INPP construcción residencial por ciudad | 96,392 | 71,788 | 24,604 | 0 | 74.48 % |
| Banxico · FIX | 2,509 | 2,481 | 0 | 28 | 98.88 % |

Cobertura: 188 series (46 ciudades más Nacional × 4 componentes), enero de 1973 a octubre de 2026; tipo de cambio de enero de 2017 a noviembre de 2026. Capa oro: 51,512 filas desde enero de 2004.

## Análisis Estadístico
Cuaderno: [pronostico.ipynb](pronostico.ipynb) · Código: [laboratorio/modelos.py](../../laboratorio/modelos.py) · Pruebas: [tests/test_laboratorio.py](../../tests/test_laboratorio.py)

Serie: índice general de costo de construcción de Colima, enero de 2004 a octubre de 2026 (274 meses), con el índice Nacional como contraste.

| Criterio de la rúbrica | Evidencia | Nota del equipo |
|---|---|---|
| Caracterización de la serie | [pronostico.ipynb §1](pronostico.ipynb) | Tendencia dominante (fuerza 0.998), estacionalidad débil según STL (0.21) pero con un escalón cada enero, y choques de precios en 2004, 2008, 2021 y 2022 |
| Estacionariedad, ACF y PACF | [pronostico.ipynb §2](pronostico.ipynb) | ADF y KPSS coinciden: no estacionaria en nivel, estacionaria con una diferencia del logaritmo. Se fija d = 1, D = 0 |
| Cuatro modelos | [pronostico.ipynb §3](pronostico.ipynb) | Suavizamiento simple, Holt, Holt-Winters y SARIMA (1,1,0)(1,0,1)₁₂ elegido por AIC, más dos modelos de referencia |
| MAE, RMSE y MAPE | [pronostico.ipynb §4](pronostico.ipynb) | Retención de 12 meses y validación con origen móvil (36 orígenes, horizontes de 1, 3, 6 y 12 meses). SARIMA gana a 1 y 3 meses (MAPE 0.47 % y 1.12 %); Holt-Winters a 6 y 12 (1.43 % y 2.34 %) |
| Residuos (Ljung-Box) | [pronostico.ipynb §5](pronostico.ipynb) | **El modelo elegido no pasa todas las pruebas.** SARIMA pasa Ljung-Box a 24 rezagos (p = 0.085) pero no a 12 (p = 0.009), y ninguno tiene residuos normales. De 64 variantes revisadas solo una pasa las dos; se explica por qué no se eligió |
| Conclusión | [pronostico.ipynb §6](pronostico.ipynb) | SARIMA sobre el logaritmo para 1 a 3 meses y Holt-Winters para 6 a 12; pronóstico de noviembre de 2026 a octubre de 2027 con intervalos |

## Calidad en los Sistemas de Información
Los documentos de esta sección son **borradores generados para revisión de José Rey**, responsable de Calidad.

| Criterio de la rúbrica | Evidencia | Nota del equipo |
|---|---|---|
| Fiabilidad y disponibilidad | [calidad/reporte-fiabilidad.md](../../calidad/reporte-fiabilidad.md) · [calidad/fiabilidad.py](../../calidad/fiabilidad.py) | Disponibilidad de 100 % (5 de 5 días), 0 fallas. MTBF y MTTR no estimables todavía: se reporta la cota y el límite de confianza en lugar de inventar un valor |
| Seguridad (gitleaks, pip-audit) | [calidad/seguridad/](../../calidad/seguridad/README.md) | 0 secretos en 13 commits, 0 vulnerabilidades en 29 paquetes. Ambas herramientas quedaron en el CI |
| Requerimientos | [requerimientos.md](requerimientos.md) | 11 funcionales y 14 no funcionales con criterio verificable y evidencia; 4 pendientes declarados |
| Plan SQA (IEEE 730) | [docs/plan-sqa.md](../plan-sqa.md) | 15 secciones: gestión, métricas con objetivo y valor, revisiones, pruebas, problemas, riesgos |
| Integración continua | [.github/workflows/ci.yml](../../.github/workflows/ci.yml) · [tests/](../../tests/) | ruff, 60 pruebas, pipeline completo y revisión de seguridad en cada cambio |
| Registro de defectos | [calidad/defectos-e1.csv](../../calidad/defectos-e1.csv) | 7 defectos encontrados y corregidos al construir E1 |

## Limitaciones conocidas
1. INEGI cambió la estructura del índice en agosto de 2025 (claves de serie nuevas). Se detectó y se resolvió en E1: ahora se consulta la vigente, con datos hasta octubre de 2026, y se verificó que coincide con la anterior en los 68,968 valores que comparten. Si la fuente vuelve a cambiar, el identificador nuevo hay que localizarlo a mano.
2. El tipo de cambio en bronce inicia en 2017; en oro, las columnas `fix_*` están vacías de 2004 a 2016.
3. Los residuos del modelo de pronóstico elegido no son ruido blanco a 12 rezagos ni normales: sus intervalos son optimistas en épocas de choque de precios. Las conclusiones a 12 meses cambiaron al agregar 15 meses de datos; lo estable es el corto plazo.
4. El MTBF y el MTTR no se pueden estimar con 5 días de operación sin fallas.
5. El índice mide variación, no precios en pesos. El precio base por ciudad saldrá de las entrevistas con ferreterías y contratistas.
6. La captura de CENACE de E0 sigue activa en el flujo diario, pero ya no es parte del producto.

## Uso de IA generativa
Se usó Claude (Anthropic) para: localizar el servicio público de exportación de INEGI y escribir su extractor; generar el código del pipeline, la puerta de calidad, el laboratorio de pronóstico, las pruebas y los flujos de GitHub Actions; ejecutar los cuadernos; correr gitleaks y pip-audit; y redactar los borradores de esta ficha, la relatoría, los requerimientos y el plan SQA. El equipo definió el tema, las reglas del proyecto y revisó lo entregado.

## Issues de la entrega anterior
E0 no recibió issues formales. Pendientes propios que se atienden aquí: el equipo de E0 tenía un integrante sin nombre en la ficha (ya está completo) y la entrevista con cliente sigue pendiente; se reprogramó con el guion nuevo de ObraPrecio.
