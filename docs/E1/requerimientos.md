# Requerimientos del sistema · ObraPrecio (E1)

Estado: **borrador para revisión del responsable de Calidad** (José Rey Sánchez Navarro). Cada requerimiento tiene un criterio verificable y la evidencia con la que hoy se comprueba. "Pendiente" significa que todavía no existe la función.

## Interesados
| Interesado | Qué necesita |
|---|---|
| Persona que va a construir o ampliar su casa | Saber si el presupuesto que le dan es razonable y cuánto puede subir mientras dura la obra |
| Albañil, contratista o arquitecto que cotiza | Sustento para actualizar una cotización |
| Ferretería | Ver cómo se mueven los precios de materiales en su ciudad |
| Docentes de las tres materias | Evidencia reproducible de datos, estadística y calidad |
| Equipo | Un flujo que corra solo y avise cuando algo falla |

## Requerimientos funcionales
| ID | Requerimiento | Criterio de aceptación | Evidencia actual | Estado |
|---|---|---|---|---|
| RF-01 | Capturar el índice de costo de construcción residencial de INEGI para las 46 ciudades y el total nacional, con sus 4 componentes | 188 series en bronce con respuesta original, fecha de captura y SHA-256 | `extractores/inegi.py`; revisión `cobertura_de_series` del reporte de la puerta | Cumplido |
| RF-02 | Capturar el tipo de cambio FIX de Banxico cada día | Una ejecución diaria registrada en la bitácora | `calidad/bitacora-captura.csv` (5 de 5 días) | Cumplido |
| RF-03 | Integrar las dos fuentes en tablas tipadas con ciudad, estado, región y componente | Tabla de plata sin duplicados por serie y mes; tipos validados | `pipeline/plata.py`; pruebas `test_inegi_ancho_a_largo_con_fechas_y_tipos`, `test_revision_de_la_fuente_gana_la_captura_reciente` | Cumplido |
| RF-04 | Rechazar registros inválidos y conservarlos con su motivo | bronce = plata + cuarentena + duplicados idénticos | `pipeline/puerta.py`; prueba `test_ningun_registro_se_pierde_en_silencio`; `data/cuarentena/` | Cumplido |
| RF-05 | Calcular variación mensual y anual, nivel de inflación y comparación contra el nacional por ciudad | Columnas presentes en la capa oro para todas las ciudades desde 2004 | `data/oro/obraprecio_panel_mensual.csv`; `pipeline/oro.py` | Cumplido |
| RF-06 | Marcar valores atípicos sin eliminarlos | Banderas por tres métodos y columna tratada aparte | `docs/E1/limpieza.ipynb` §4 | Cumplido |
| RF-07 | Pronosticar el índice a 1, 3, 6 y 12 meses con su margen de error | Error medido con validación de origen móvil y publicado | `docs/E1/pronostico.ipynb`; `laboratorio/modelos.py` | Cumplido para Colima y Nacional; pendiente para las demás ciudades |
| RF-08 | Mostrar un ranking de ciudades por variación anual | Tabla del último mes ordenada | `data/oro/ranking_ciudades.csv` | Cumplido |
| RF-09 | Tablero público para consultar una ciudad | Página accesible sin instalar nada | | Pendiente (E2) |
| RF-10 | Chat de consulta que responda con los datos de la capa oro | Respuestas que citan cifra, mes y fuente | | Pendiente (E2) |
| RF-11 | Convertir el índice a pesos con un precio base por ciudad | Presupuesto estimado para una obra tipo | | Pendiente; depende de las entrevistas |

## Requerimientos no funcionales
| ID | Atributo (ISO/IEC 25010) | Requerimiento | Métrica y objetivo | Medición actual | Estado |
|---|---|---|---|---|---|
| RNF-01 | Fiabilidad: disponibilidad | La captura diaria debe ocurrir | Días con captura exitosa ≥ 95 % | 100 % (5 de 5 días) | Cumple, con muestra pequeña |
| RNF-02 | Fiabilidad: recuperabilidad | Una falla se repara pronto | MTTR ≤ 24 h | Sin fallas registradas | Sin evidencia todavía |
| RNF-03 | Fiabilidad: tolerancia a fallos | Un error temporal de red no tumba la captura | Hasta 3 intentos con espera creciente | 0 reintentos necesarios; cubierto por pruebas | Cumple |
| RNF-04 | Adecuación funcional: completitud | Las series no tienen huecos | Meses faltantes dentro de una serie = 0 | 0 (revisión `continuidad_mensual`) | Cumple |
| RNF-05 | Adecuación funcional: exactitud | Lo publicado coincide con la fuente | Base julio 2019 = 100 en las 188 series | Desviación máxima 0 | Cumple |
| RNF-06 | Seguridad: confidencialidad | Ningún secreto en el repositorio | Hallazgos de gitleaks = 0 | 0 en 12 commits | Cumple |
| RNF-07 | Seguridad: integridad | Dependencias sin vulnerabilidades conocidas | Hallazgos de pip-audit = 0 | 0 en 29 paquetes | Cumple |
| RNF-08 | Seguridad: privacidad | Cero datos personales | Solo estadística agregada; esquema estricto | Sin columnas fuera del contrato | Cumple |
| RNF-09 | Mantenibilidad: capacidad de prueba | Todo cambio pasa pruebas automáticas | CI en verde antes de entregar | 59 pruebas, CI activo | Cumple |
| RNF-10 | Mantenibilidad: analizabilidad | Estilo uniforme | `ruff check` sin errores | 0 errores | Cumple |
| RNF-11 | Eficiencia de desempeño | El pipeline completo corre rápido | ≤ 60 s en GitHub Actions | 5.3 s en la sesión de desarrollo; sin medir aún en Actions | Por confirmar |
| RNF-12 | Portabilidad: reproducibilidad | Cualquiera puede regenerar los resultados | Tres comandos documentados | README y fichas de entrega | Cumple |
| RNF-13 | Uso ético de las fuentes | Respetar robots.txt, identificarse y no saturar | ≥ 1 s entre peticiones; User-Agent con contacto | Cubierto por pruebas de `extractores/base.py` | Cumple |
| RNF-14 | Oportunidad del dato | El último mes publicado por INEGI está disponible | Rezago ≤ 2 meses respecto a la fuente | Último dato: julio 2025 | **No cumple** (ver limitación 1 de la ficha) |

## Trazabilidad
Cada requerimiento cumplido apunta a una prueba, un archivo de datos o una revisión automática. Los pendientes (RF-09 a RF-11, RNF-14) son el alcance de E2.
