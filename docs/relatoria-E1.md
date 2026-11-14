# Relatoría E1 · ObraPrecio (TRUSTED DATA LAB)
Equipo: Julio Alberto Orozco Téllez, Ángel Salvador Álvarez Fernández y José Rey Sánchez Navarro (solo Calidad) · Periodo: 2 al 13 de noviembre de 2026

## 1. Qué nos propusimos
Que los datos viajen de bronce a oro sin intervención, pasando por una puerta de calidad que rechace con motivo; pronosticar la serie principal con cuatro modelos y elegir por error fuera de muestra; y medir con bitácoras qué tan disponible estuvo la captura contra el objetivo de E0 (≥ 95 %).

## 2. Qué hicimos (cronología con fechas, responsable y horas)
| Fecha y hora (centro) | Qué | Quién | Tiempo |
|---|---|---|---|
| 9 al 13 nov, 05:00 | Captura diaria automática de CENACE y Banxico: 5 ejecuciones, 0 fallas | Flujo de GitHub Actions (configurado por Julio en E0) | 10 s por ejecución |
| 12 y 13 nov | Búsqueda de cliente para el Observatorio Eléctrico; evaluación de 4 ideas; consulta a equipo, familia y docentes | Ángel | Sin registro |
| 13 nov, 13:20 | Decisión de cambiar a ObraPrecio; el equipo la aprueba | Ángel, Julio, José Rey | |
| 13 nov, 13:22 a 13:41 | Extractor de INEGI, pipeline plata y oro, puerta Pandera, cuaderno de limpieza, CI | Ángel con asistente de IA | 0.3 h de sesión |
| 13 nov, 15:55 a 16:15 | Laboratorio de pronóstico, fiabilidad, seguridad, borradores de plan SQA y requerimientos | Ángel con asistente de IA | 0.3 h |
| 13 nov, 16:22 a 16:35 | Se detecta que los datos terminaban en julio de 2025; se localiza la estructura vigente de INEGI y se regenera todo | Ángel con asistente de IA | 0.2 h |
| 13 nov, 17:11 | Verificación del CI y registro de la entrega | Julio | Sin registro |
| 13 nov, 19:32 a 19:57 | Revisión del plan SQA y de los requerimientos, con 7 observaciones | José Rey | 0.4 h |
| 13 nov, 20:56 a 22:00 | Lectura del documento completo del proyecto; se completa lo faltante (diccionario, tablero, respaldo, correlación cruzada, esta relatoría) | Ángel con asistente de IA | 1 h |

Los tiempos de sesión salen de las marcas de hora de los commits. **El registro individual de tiempo no se llevó en E1** (ver sección 4).

## 3. Qué decidimos y por qué (alternativas descartadas)
1. **Cambiar de tema el día de la entrega.** El Observatorio Eléctrico no tenía cliente al alcance. Se descartaron plátano (otro equipo), sistema médico (datos personales) y remesas (pocas variables). Costo: E1 se construyó en un día.
2. **No imputar los `N/E` de INEGI.** Son periodos en que la serie no existía (0 huecos interiores). Se descartó rellenar hacia atrás; oro arranca en 2004 con panel completo.
3. **Elegir el modelo por error en 36 orígenes y no por AIC ni por una sola ventana.** Ocho SARIMA quedaban a menos de 4 puntos de AIC. Con una sola ventana de 12 meses ganaba una regla simple que en 36 orígenes resultó la peor.
4. **Marcar atípicos en lugar de borrarlos.** Aparecen el mismo mes en muchas ciudades: son choques de precios reales.

## 4. Qué salió mal y cómo lo corregimos (con número de defecto)
- **Defecto 9 (180 min, el más caro):** E1 se construyó desde el texto de una tarea de Classroom y no desde el documento del proyecto. Faltaban diccionario de datos, tablero, respaldo de bronce, correlación cruzada y este formato. Se completó la misma noche.
- **Defecto 7 (60 min):** se consultó una estructura de INEGI congelada en julio de 2025. Se localizó la vigente y se comprobó que coinciden en los 68,968 valores comunes.
- **Defecto 2 (15 min):** IQR y Z robusto marcaban todo ajuste de mano de obra como atípico (series escalonadas, MAD = 0).
- **Defecto 8 (10 min):** el CI no corría en push de solo documentos. Lo detectó José Rey.
- **Defecto 5 (10 min):** dos afirmaciones del cuaderno no coincidían con sus salidas.
- **Sin resolver:** solo hay 5 días de bitácora de los 7 pedidos (la captura inició el 9); no se llevaron registros individuales de tiempo ni de defectos; el tablero no tiene URL pública; el equipo tiene tres personas y el proyecto pide máximo dos, pendiente de consultar con los docentes.

## 5. Qué aprendimos
### Ingeniería de Datos
Un faltante no siempre se imputa: los 24,604 `N/E` eran MAR estructural y la decisión correcta fue no tocarlos. Y la fuente puede cambiar sin avisar: INEGI movió el índice a otra estructura con claves nuevas, y lo resolvió integrar por ciudad y componente, no por clave.
### Análisis Estadístico
Una sola ventana de prueba engaña: la referencia de deriva ganó en los últimos 12 meses (MAPE 0.70 %) y fue la peor en 36 orígenes. Y la fuerza estacional de la STL (0.2) escondía un escalón cada enero que la ACF del rezago 12 (0.39) sí mostraba.
### Calidad en los Sistemas de Información
Sin fallas no hay MTBF ni MTTR: con 5 ejecuciones exitosas lo único demostrable es que la probabilidad de falla es menor a 45 %. Y la revisión independiente funciona: quien no escribió el plan encontró que el CI no cubría todos los push.

## 6. Evidencias
- Commits: [pipeline y puerta](https://github.com/23460521-commits/tdl-observatorio-electrico/commit/7d5d1dc) · [pronóstico y calidad](https://github.com/23460521-commits/tdl-observatorio-electrico/commit/fcb50aa) · [estructura vigente de INEGI](https://github.com/23460521-commits/tdl-observatorio-electrico/commit/bc60585) · [revisión de Calidad](https://github.com/23460521-commits/tdl-observatorio-electrico/commit/6add90e)
- Cuadernos: [limpieza](E1/limpieza.ipynb) · [pronóstico](E1/pronostico.ipynb)
- Calidad: [reporte de la puerta](../calidad/reporte-puerta.json) · [fiabilidad](../calidad/reporte-fiabilidad.md) · [seguridad y respaldo](../calidad/seguridad/README.md) · [defectos](../calidad/defectos-e1.csv) · [plan SQA](plan-sqa.md)
- CI en GitHub Actions: ejecución 43524364243, en verde (pipeline 6 s).

## Uso de IA generativa (herramienta y para qué)
Claude (Anthropic). Se usó para localizar el servicio de exportación de INEGI, generar el código de extractores, pipeline, laboratorio, tablero, pruebas y flujos, ejecutar los cuadernos, correr gitleaks y pip-audit, y redactar los borradores de la ficha, esta relatoría, los requerimientos y el plan SQA. Decisiones humanas: el tema, las reglas del proyecto, la aprobación del cambio y la revisión de Calidad. Lo que el equipo no pueda explicar en la defensa no cuenta: está previsto estudiar el repositorio antes del panel del 17 y 18 de noviembre.
