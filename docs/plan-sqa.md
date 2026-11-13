# Plan de Aseguramiento de la Calidad del Software (SQAP) · ObraPrecio

Estructura basada en IEEE Std 730. Versión 1.0 del 13 de noviembre de 2026.
Estado: **borrador para revisión y aprobación del responsable de Calidad** (José Rey Sánchez Navarro).

## 1. Propósito y alcance
Este plan define cómo el equipo asegura la calidad de ObraPrecio, el módulo del TRUSTED DATA LAB que informa cuánto ha subido el costo de construir vivienda en 46 ciudades de México.

Cubre todo lo que vive en el repositorio: extractores, pipeline de datos (bronce, plata, oro y cuarentena), laboratorio estadístico, flujos de GitHub Actions, datos publicados y documentación. Queda fuera lo que aún no existe (tablero y chat de consulta); se incorporará en la siguiente versión del plan.

## 2. Documentos de referencia
- IEEE Std 730, Software Quality Assurance Processes.
- ISO/IEC 25010, modelo de calidad del producto de software.
- ISO/IEC 25012, modelo de calidad de datos.
- [Requerimientos del sistema](E1/requerimientos.md).
- Fichas de entrega [E0](E0/ENTREGA.md) y [E1](E1/ENTREGA.md), [cambio de tema](E1/pivote-obraprecio.md).
- [Reporte de fiabilidad](../calidad/reporte-fiabilidad.md) y [resultados de seguridad](../calidad/seguridad/README.md).

## 3. Gestión
### 3.1 Organización y responsabilidades
| Rol | Persona | Responsabilidad |
|---|---|---|
| Responsable de Calidad | José Rey Sánchez Navarro | Mantiene este plan, revisa cada entrega contra la lista de la sección 6, lleva el registro de defectos y calcula los indicadores |
| Líder del proyecto | Ángel Salvador Álvarez | Prioriza, coordina con docentes y cliente, aprueba el contenido de cada entrega |
| Administrador del repositorio | Julio Alberto Orozco Téllez | Permisos, secretos, flujos de GitHub Actions y etiquetas de entrega |
| Todo el equipo | | Registrar defectos y tiempo, no subir cambios con el CI en rojo |

Independencia: quien revisa una entrega no es quien escribió el cambio principal. Cuando el código se genera con asistencia de IA, la revisión humana de la sección 6 es obligatoria antes de etiquetar.

### 3.2 Tareas de calidad por etapa
| Etapa | Tareas de SQA | Producto |
|---|---|---|
| E0 | Definir objetivos de calidad, bitácora de captura, pruebas de extractores | Hecho |
| E1 | Puerta de calidad de datos, CI, revisión de seguridad, primer cálculo de fiabilidad, este plan | Hecho |
| E2 | Auditoría del tablero, pruebas de aceptación con usuarios entrevistados, recálculo de MTBF y MTTR con más historia | Pendiente |

## 4. Documentación
| Documento | Dónde | Quién lo mantiene |
|---|---|---|
| README y fichas de entrega | `README.md`, `docs/E*/ENTREGA.md` | Líder |
| Relatorías | `docs/relatoria-E*.md` | Líder |
| Requerimientos | `docs/E1/requerimientos.md` | Calidad |
| Este plan | `docs/plan-sqa.md` | Calidad |
| Contrato de datos | `pipeline/puerta.py` (esquemas Pandera) | Datos |
| Motivos de cuarentena | `data/cuarentena/README.md` | Datos |
| Evidencia de limpieza y de modelos | `docs/E1/limpieza.ipynb`, `docs/E1/pronostico.ipynb` | Datos y Estadística |

Regla: toda cifra escrita en un documento debe poder regenerarse con un comando del repositorio.

## 5. Estándares, prácticas, convenciones y métricas
### 5.1 Estándares y convenciones
- Python 3.11, estilo verificado con `ruff` (líneas de hasta 100 caracteres, reglas E, F, W, I, UP, B).
- Nombres de código, datos y documentos en español.
- Mensajes de commit: una línea de resumen con la etapa (`E1: ...`) y, debajo, qué cambia y por qué.
- Datos: la capa bronce nunca se modifica; plata y oro se regeneran completos desde bronce.
- Ética de fuentes: robots.txt, User-Agent con contacto, al menos 1 s entre peticiones.

### 5.2 Métricas y objetivos
| Métrica | Cómo se mide | Objetivo | Valor en E1 |
|---|---|---|---|
| Disponibilidad de la captura | `python calidad/fiabilidad.py` | ≥ 95 % | 100 % (5 de 5 días) |
| MTTR | Igual | ≤ 24 h | Sin fallas registradas |
| MTBF | Igual | Se reporta; sin objetivo aún | No estimable (0 fallas en 86 h) |
| Registros aceptados por la puerta | `calidad/reporte-puerta.json` | Se reporta por fuente | INEGI 74.48 %, Banxico 98.88 % |
| Registros perdidos sin motivo | Balance bronce = plata + cuarentena + duplicados | 0 | 0 |
| Huecos dentro de las series | Revisión `continuidad_mensual` | 0 | 0 |
| Pruebas automáticas que pasan | `pytest` | 100 % | 60 de 60 |
| Errores de estilo | `ruff check .` | 0 | 0 |
| Secretos expuestos | gitleaks | 0 | 0 |
| Dependencias vulnerables | pip-audit | 0 | 0 |
| Defectos registrados y cerrados | `calidad/defectos-e1.csv` | 100 % cerrados antes de etiquetar | 7 de 7 |
| Error del pronóstico a 1 mes (MAPE) | `docs/E1/pronostico.ipynb` | Se reporta; objetivo por fijar con el cliente | 0.47 % (Colima, SARIMA) |

El porcentaje aceptado de INEGI es bajo por una razón conocida: los rechazados son celdas `N/E` de periodos en que la serie no existía, no errores.

## 6. Revisiones y auditorías
| Revisión | Cuándo | Quién | Criterio de salida |
|---|---|---|---|
| Revisión de cambio | En cada subida a `main` | CI automático | ruff, pytest, pipeline y seguridad en verde |
| Revisión de entrega | Antes de crear la etiqueta | Responsable de Calidad | Lista siguiente completa |
| Auditoría de datos | En cada corrida del pipeline | Puerta de calidad | Sin revisiones graves fallidas |
| Revisión posterior a un incidente | Tras cada falla de captura | Calidad y administrador | Defecto registrado con causa y corrección |

**Lista de revisión de entrega**
1. El CI del commit a etiquetar está en verde.
2. La ficha `ENTREGA.md` enlaza evidencia existente para cada criterio de la rúbrica.
3. Las cifras de la ficha y de los cuadernos coinciden con `calidad/reporte-puerta.json` y con las salidas ejecutadas.
4. Lo que no se hizo está escrito como pendiente o limitación.
5. No hay secretos ni datos personales (gitleaks en verde y revisión visual de archivos nuevos).
6. Los defectos de la etapa están registrados y cerrados, o listados como abiertos.
7. La relatoría describe el reparto real del trabajo y el uso de IA.

## 7. Pruebas
| Nivel | Qué cubre | Dónde | Cantidad en E1 |
|---|---|---|---|
| Unitarias | Extractores, limpieza de formato, funciones estadísticas, modelos de pronóstico | `tests/` | 60 |
| Integración | Pipeline de punta a punta con bronce sintético | `test_pipeline_completo_escribe_plata_oro_y_cuarentena` | 1 |
| Datos (contrato) | Esquemas Pandera y revisiones de conjunto sobre los datos reales | `pipeline/puerta.py` | 2 esquemas, 6 revisiones |
| Sistema | Pipeline completo contra los datos del repositorio en GitHub Actions | `.github/workflows/ci.yml` | En cada cambio |
| Aceptación | Con usuarios reales (entrevistados) | | Pendiente (E2) |

Las pruebas no usan internet: las respuestas de las fuentes se simulan. No se mide todavía la cobertura de código; se agregará en E2.

## 8. Reporte de problemas y acción correctiva
1. Quien detecta un defecto lo registra en `calidad/defectos-<etapa>.csv` con tipo, fase en que se introdujo, fase en que se eliminó y minutos de corrección (formato PSP).
2. Si el defecto afecta datos ya publicados, se abre además un issue en GitHub.
3. La corrección incluye una prueba que falle sin el arreglo, cuando sea posible.
4. Un registro inválido en los datos no es un defecto del código: va a cuarentena con su motivo. Si el motivo se repite, se abre un defecto para revisar la regla o el extractor.
5. Una falla de la captura programada deja la ejecución en rojo en GitHub Actions y una fila `fallo` en la bitácora; el administrador la atiende en menos de 24 h.

Defectos de E1: 7 registrados, 7 corregidos (2 de datos, 2 de función, 1 de entorno, 1 de documentación, 1 de estilo).

## 9. Herramientas, técnicas y metodologías
| Herramienta | Uso |
|---|---|
| Git y GitHub | Control de versiones, etiquetas de entrega, issues |
| GitHub Actions | Captura programada, pipeline y CI |
| pytest | Pruebas automáticas |
| ruff | Estilo y errores comunes |
| Pandera | Contrato de datos (puerta de calidad) |
| gitleaks | Búsqueda de secretos en el historial |
| pip-audit | Vulnerabilidades en dependencias |
| PSP (registros de defectos y tiempo) | Medición del proceso personal |
| Claude (IA generativa) | Generación de código y borradores, siempre con revisión humana y verificación automática |

## 10. Control de medios y de configuración
- El repositorio de GitHub es la única fuente de verdad; cada entrega queda fija con una etiqueta (`e0`, `e1`).
- La capa bronce guarda la respuesta original comprimida con su SHA-256; las tablas de salida registran su SHA-256 en el reporte de la puerta.
- Los secretos viven en GitHub Secrets y no se copian a ningún otro lugar.

## 11. Control de proveedores
| Proveedor | Qué entrega | Riesgo | Control |
|---|---|---|---|
| INEGI | Índice de costo de construcción | Cambio de formato o de estructura del índice | El extractor valida la forma de la respuesta; la puerta revisa cobertura y base |
| Banxico | Tipo de cambio | Caída del servicio o token vencido | Reintentos; la falla queda en bitácora y en rojo |
| GitHub | Alojamiento y ejecución | El flujo programado puede retrasarse u omitirse | Disponibilidad medida por día, no por hora exacta |
| Bibliotecas de Python | pandas, statsmodels, etc. | Vulnerabilidades o cambios incompatibles | pip-audit en CI; versiones mínimas declaradas |

## 12. Registros: recolección, mantenimiento y retención
Bitácoras de captura y de pipeline, reportes de la puerta, defectos, tiempo y resultados de seguridad viven en `calidad/` y se conservan en el historial de Git durante todo el proyecto. No se borran entre etapas.

## 13. Capacitación
José Rey no cursa Ingeniería de Datos ni Análisis Estadístico: Julio y Ángel le explican la arquitectura por capas y cómo leer el reporte de la puerta antes de su primera revisión de entrega. Todo el equipo debe saber correr los tres comandos de reproducción del README.

## 14. Gestión de riesgos
| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| INEGI vuelve a cambiar la estructura del índice (ya ocurrió en agosto de 2025; resuelto en E1) | Media | Alto | Revisar la oportunidad del dato en cada corrida; el identificador vigente está en un solo lugar (`extractores/config.py`) |
| Los docentes no aprueban el cambio de tema | Media | Alto | Confirmación solicitada; la arquitectura sirve para cualquier fuente |
| Dependencia de una sola persona y de IA para construir | Alta | Medio | Revisión de entrega obligatoria, sesión de explicación al equipo |
| No conseguir entrevistas con usuarios | Media | Alto | Empezar por contactos de la familia y del equipo |
| El pronóstico falla ante un choque de precios | Media | Medio | Se publica el error por horizonte y se advierte en el producto |
| Fuga del token de Banxico | Baja | Medio | GitHub Secrets, gitleaks en CI |

## 15. Control de cambios de este plan
Los cambios se hacen por commit, con aprobación del responsable de Calidad, y se anotan aquí.

| Versión | Fecha | Cambio |
|---|---|---|
| 1.0 | 2026-11-13 | Primera versión, para la entrega E1 |
