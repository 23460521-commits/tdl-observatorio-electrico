# Requerimientos del sistema · ObraPrecio (E1)

Estado: **revisado por el responsable de Calidad (José Rey Sánchez Navarro) el 13 de noviembre de 2026, con observaciones**. Las observaciones y su atención están al final. Cada requerimiento tiene un criterio verificable y la evidencia con la que hoy se comprueba. "Pendiente" significa que todavía no existe la función.

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
| RF-07 | Pronosticar el índice a 1, 3, 6 y 12 meses con su margen de error | Error medido con validación de origen móvil y publicado | `docs/E1/pronostico.ipynb`; `laboratorio/modelos.py` | **Parcial**: cumplido para Colima y Nacional; pendiente para las otras 45 ciudades |
| RF-08 | Mostrar un ranking de ciudades por variación anual | Tabla del último mes ordenada | `data/oro/ranking_ciudades.csv` | Cumplido |
| RF-09 | Tablero público para consultar una ciudad | Página accesible sin instalar nada | `tablero/app.py` (Streamlit): ciudad, componentes, pronóstico con intervalo, ranking y puerta de calidad; probado con `streamlit.testing` | **Parcial**: construido y probado en local; falta publicarlo en una URL pública |
| RF-10 | Chat de consulta que responda con los datos de la capa oro | Respuestas que citan cifra, mes y fuente | | Pendiente (E2) |
| RF-11 | Convertir el índice a pesos con un precio base por ciudad | Presupuesto estimado para una obra tipo | | Pendiente; depende de las entrevistas |

## Requerimientos no funcionales
| ID | Atributo (ISO/IEC 25010) | Requerimiento | Métrica y objetivo | Medición actual | Estado |
|---|---|---|---|---|---|
| RNF-01 | Fiabilidad: disponibilidad | La captura diaria debe ocurrir | Días con captura exitosa ≥ 95 %, medidos en 7 días | 100 % (5 de 5 días) | Cumple en lo observado; **evidencia incompleta**: 5 días de bitácora de los 7 pedidos |
| RNF-02 | Fiabilidad: recuperabilidad | Una falla se repara pronto | MTTR ≤ 24 h | Sin fallas registradas | Sin evidencia todavía |
| RNF-03 | Fiabilidad: tolerancia a fallos | Un error temporal de red no tumba la captura | Hasta 3 intentos con espera creciente | 0 reintentos necesarios; cubierto por pruebas | Cumple |
| RNF-04 | Adecuación funcional: completitud | Las series no tienen huecos | Meses faltantes dentro de una serie = 0 | 0 (revisión `continuidad_mensual`) | Cumple |
| RNF-05 | Adecuación funcional: exactitud | Lo publicado coincide con la fuente | Base julio 2019 = 100 en las 188 series | Desviación máxima 0 | Cumple |
| RNF-06 | Seguridad: confidencialidad | Ningún secreto en el repositorio | Hallazgos de gitleaks = 0 | 0 en 16 commits; en verde en GitHub Actions | Cumple |
| RNF-07 | Seguridad: integridad | Dependencias sin vulnerabilidades conocidas | Hallazgos de pip-audit = 0 | 0 en 29 paquetes | Cumple |
| RNF-08 | Seguridad: privacidad | Cero datos personales | Solo estadística agregada; esquema estricto | Sin columnas fuera del contrato | Cumple |
| RNF-09 | Mantenibilidad: capacidad de prueba | Todo cambio pasa pruebas automáticas | CI en verde en cada push | 63 pruebas; CI en verde en los 4 commits de E1 que lo dispararon | Cumple |
| RNF-10 | Mantenibilidad: analizabilidad | Estilo uniforme | `ruff check` sin errores | 0 errores | Cumple |
| RNF-11 | Eficiencia de desempeño | El pipeline completo corre rápido | ≤ 60 s en GitHub Actions | 6 s en GitHub Actions (ejecución 43524364243; el trabajo completo, con instalación, 42 s) | Cumple |
| RNF-12 | Portabilidad: reproducibilidad | Cualquiera puede regenerar los resultados | Comandos documentados que corren en una máquina limpia | Instalación, ruff, pytest y pipeline corren en cada push en una máquina nueva de GitHub Actions. Los cuadernos y el tablero solo se han ejecutado en la sesión de desarrollo | Cumple para el pipeline; por confirmar para cuadernos y tablero |
| RNF-13 | Uso ético de las fuentes | Respetar robots.txt, identificarse y no saturar | ≥ 1 s entre peticiones; User-Agent con contacto | Cubierto por pruebas de `extractores/base.py` | Cumple |
| RNF-14 | Oportunidad del dato | El último mes publicado por INEGI está disponible | Rezago ≤ 2 meses respecto a la fuente | Último dato: octubre de 2026, capturado el 13 de noviembre de 2026 | Cumple (no cumplía con la estructura anterior del índice; ver limitación 1 de la ficha) |
| RNF-15 | Seguridad: disponibilidad de los datos | La capa bronce se puede recuperar | Restauración de un respaldo sin diferencias (SHA-256) | 2,137 de 2,137 archivos restaurados iguales | Cumple en prueba local; el flujo semanal aún no corre en GitHub |

## Revisión contra las características de un buen requerimiento
Se revisaron los 26 requerimientos (11 funcionales y 15 no funcionales) contra cuatro características.

| Característica | Pregunta de revisión | Resultado |
|---|---|---|
| Necesario | ¿Lo pide un interesado de la tabla inicial o la rúbrica del proyecto? | 26 de 26 |
| No ambiguo | ¿Tiene una sola lectura posible, sin adjetivos como "rápido" o "confiable" sin número? | 24 de 26. RF-10 ("respuestas que citan cifra, mes y fuente") y RF-11 ("obra tipo") todavía no definen el alcance exacto; se precisan al diseñarlos en E2 |
| Verificable | ¿Existe un comando, archivo o prueba que diga si se cumple? | 23 de 26. RF-09 a RF-11 no tienen prueba de aceptación hasta que haya usuarios entrevistados |
| Rastreable | ¿Apunta a un archivo, prueba o revisión del repositorio? | 23 de 26 (los mismos tres) |

## Trazabilidad
Cada requerimiento cumplido apunta a una prueba, un archivo de datos o una revisión automática. Los pendientes o parciales (RF-07, RF-09 a RF-11) son alcance de E2.

## Revisión del responsable de Calidad

Responsable: José Rey Sánchez Navarro
Fecha: 13 de noviembre de 2026 a las 7:57

Revisé los requerimientos funcionales y no funcionales del proyecto ObraPrecio. En general, considero que están bien organizados y explican lo que debe hacer el sistema.

Sin embargo, encontré algunos puntos que todavía se deben revisar:

Solo hay registros de 5 días y el proyecto pide 7 para comprobar la fiabilidad.

No se pudieron calcular MTBF y MTTR porque no se presentaron fallas.

Falta confirmar que las pruebas de seguridad estén actualizadas.

Se debe comprobar el tiempo que tarda en ejecutarse el sistema en GitHub Actions.

Hay que verificar que los comandos del proyecto funcionen correctamente.

Los pronósticos todavía no están disponibles para todas las ciudades.

Conclusión:

Considero que los requerimientos están bien planteados y cumplen con la estructura solicitada. Solo hace falta revisar los puntos mencionados para poder dar la aprobación final.

Estado: Revisado, pendiente de algunas correcciones y comprobaciones.

### Atención a las observaciones
| Observación de la revisión | Situación al cierre de E1 | Evidencia |
|---|---|---|
| Solo hay 5 días de registros y se piden 7 | **No se puede resolver.** La captura programada empezó el 9 de noviembre; los días 6 a 8 no existen y no se inventan. Queda declarado como evidencia incompleta | `calidad/reporte-fiabilidad.md` |
| No se pueden calcular MTBF y MTTR | **Sigue igual, y es correcto.** Sin fallas no hay intervalo que medir. Se reporta la cota (más de 86 h) y el límite de 95 % para la probabilidad de falla | `calidad/reporte-fiabilidad.md` |
| Confirmar que las pruebas de seguridad estén actualizadas | **Resuelto.** Se repitieron sobre la versión que se entrega y corren en cada push en GitHub Actions | `calidad/seguridad/README.md` |
| Comprobar el tiempo en GitHub Actions | **Resuelto.** El pipeline tarda 6 s en GitHub Actions | RNF-11 |
| Verificar que los comandos funcionen | **Resuelto para el pipeline** (corre en una máquina nueva en cada push). Cuadernos y tablero, solo en desarrollo | RNF-12 |
| Los pronósticos no están para todas las ciudades | **Sigue pendiente.** RF-07 queda como parcial | RF-07 |
| Confirmar que GitHub Actions ejecute los controles | **Resuelto, con un hallazgo.** El CI excluía los cambios que solo tocaban documentos, así que el commit de esta revisión no lo disparó. Se quitó la exclusión: ahora corre en todo push | `.github/workflows/ci.yml` |

La aprobación final corresponde al responsable de Calidad.
