# Relatoría de la etapa E1

Periodo: 9 al 13 de noviembre de 2026 · Equipo: Julio Alberto Orozco Téllez, Ángel Salvador Álvarez y José Rey Sánchez Navarro (participa solo en Calidad en los Sistemas de Información).

## 1. Qué pasó en esta etapa
1. **La captura de E0 siguió corriendo sola.** Del 9 al 13 de noviembre el flujo diario de GitHub Actions capturó CENACE y Banxico sin fallas de fuentes obligatorias (ver `calidad/bitacora-captura.csv`).
2. **Se cambió el tema del proyecto.** Al intentar aterrizar el modelo de negocio del Observatorio Eléctrico no se encontró un cliente al alcance del equipo. Se evaluaron cuatro ideas y se eligió ObraPrecio (costo de construcción por ciudad). El razonamiento está en [E1/pivote-obraprecio.md](E1/pivote-obraprecio.md). El equipo lo aprobó en el grupo de trabajo el 13 de noviembre; la confirmación de los docentes está solicitada y pendiente.
3. **Se incorporó José Rey.** No cursa Ingeniería de Datos ni Análisis Estadístico, así que su participación se limita a Calidad.
4. **Se construyó E1 en un día.** La decisión del cambio se tomó el mismo día de la entrega. Se construyeron el extractor de INEGI, el pipeline plata/oro, la puerta de calidad, las pruebas, el cuaderno y esta documentación.

## 2. Decisiones técnicas y por qué
| Decisión | Alternativa descartada | Razón |
|---|---|---|
| Usar la exportación CSV pública del sitio de índices de precios de INEGI | API del Banco de Indicadores (pide token y no se tenía el identificador de cada serie) | Sin llave, robots.txt lo permite y entrega las 188 series con sus metadatos |
| Guardar el catálogo de series en un archivo versionado | Consultarlo en cada corrida | Menos peticiones a la fuente y el pipeline corre sin internet |
| Catálogo explícito de ciudades | Extraer el estado del texto con expresiones regulares | La fuente escribe "Villahermosa,Tab." y "Cd. Jiménez Chih."; adivinar es frágil. Lo que no está en catálogo va a cuarentena |
| No imputar los `N/E` | Rellenar hacia atrás | Son periodos en que la serie no existía; rellenar sería inventar historia |
| Marcar y winsorizar atípicos en columna aparte | Eliminarlos | Aparecen en muchas ciudades el mismo mes: son choques de precios reales, justo lo que el usuario quiere ver |
| Referencia distinta para series escalonadas | Aplicar IQR y MAD igual a todo | En mano de obra y maquinaria más de la mitad de los meses no cambian; IQR y MAD valen 0 |
| Excluir `general` de los modelos | Usar las cuatro variables | Correlación de 0.99 con materiales; es redundante |
| Conservar la primera captura cuando el valor se repite | Conservar la última | La procedencia de cada fila no cambia en cada corrida y los archivos de plata solo cambian cuando cambian los datos |

## 3. Problemas encontrados
- **Los datos de la primera estructura consultada terminaban en julio de 2025.** Se detectó al revisar el periodo disponible que declara la fuente. La causa: INEGI actualizó el índice en agosto de 2025 y lo publica en una estructura nueva con otras claves de serie. Se localizó la vigente (datos hasta octubre de 2026), se comprobó que coincide con la anterior en los 68,968 valores comunes y se volvió a correr todo. Las etiquetas `e1` y `e1-final` conservan la versión con datos a julio de 2025; `e1-v2` trae la corregida.
- **Un componente llegó con otro nombre** ("-- Materiales de construcción") y generaba una quinta categoría. Se detectó al revisar la matriz de correlaciones.
- **Dos afirmaciones del cuaderno no coincidían con sus propias salidas** (número de celdas faltantes y oleadas de incorporación de ciudades). Se corrigieron contra los datos antes de entregar.
- **El tipo de cambio solo cubre desde 2017**, por lo que la integración con el índice queda parcial de 2004 a 2016.
- Los siete defectos están registrados en [calidad/defectos-e1.csv](../calidad/defectos-e1.csv).

## 4. Qué no se hizo
- La entrevista con un cliente, pendiente desde E0.
- El tablero público.
- Apagar o separar la captura de CENACE, que ya no es parte del producto.
- Pronóstico por componente y para las 46 ciudades (solo Colima y Nacional).
- Medición de cobertura de pruebas.

## 4 bis. Análisis Estadístico: qué se encontró
- **Una sola ventana de prueba engaña.** Con los últimos 12 meses, SARIMA quedaba peor que repetir el último valor en Colima y era el mejor en el Nacional. Por eso se agregó la validación con 36 orígenes, que es la que decide.
- **El suavizamiento simple resultó idéntico al modelo ingenuo** (α ≈ 1). Se reporta tal cual: en esta serie no aporta.
- **La estacionalidad parecía débil y no lo era del todo.** La STL daba fuerza de 0.2, pero la ACF del rezago 12 (0.39) era mayor que la del rezago 1 y los residuos de tres modelos fallaban justo en los rezagos 12 y 24: el índice da un escalón cada enero.
- **El modelo elegido no deja residuos de ruido blanco.** Al ampliar la búsqueda de SARIMA a 64 variantes, una sola pasó Ljung-Box a 12 y 24 rezagos. No se eligió: escoger el modelo por ser el único que pasa el diagnóstico es ajustarlo a la prueba. Se reporta la limitación y el candidato.
- **Las conclusiones cambiaron con más datos.** Con datos a julio de 2025, a 12 meses ningún modelo superaba a la referencia de deriva; con datos a octubre de 2026 gana Holt-Winters. El resultado de corto plazo (SARIMA a 1 y 3 meses) se mantuvo.
- La primera redacción del cuaderno decía que los residuos fallaban en el primer rezago; al ver las gráficas era en el 12. Se corrigió contra las salidas.

## 4 ter. Calidad: qué se encontró
- **Con 5 días sin fallas no se puede calcular MTBF ni MTTR.** En lugar de reportar "infinito" se reporta la cota (más de 86 horas) y el límite superior de 95 % para la probabilidad de falla por ejecución (45 %), que deja claro lo poco que se sabe todavía.
- **Una fuente opcional nunca ha traído datos:** la petición del día siguiente de CENACE se omitió en 5 de 5 ejecuciones. Queda como observación.
- gitleaks y pip-audit salieron limpios y se agregaron al CI.
- Requerimientos y plan SQA son borradores generados con IA; falta la revisión de José Rey.

## 5. Reparto del trabajo
| Integrante | E1 |
|---|---|
| Julio Alberto Orozco Téllez | Administrador del repositorio; base de extractores y captura diaria de E0 que E1 reutiliza |
| Ángel Salvador Álvarez | Propuesta del cambio de tema, coordinación con el equipo y los docentes, dirección y revisión del pipeline de E1 construido con asistencia de IA |
| José Rey Sánchez Navarro | Calidad: revisión y aprobación del plan SQA, los requerimientos y los reportes de fiabilidad y seguridad (borradores listos, revisión pendiente) |

## 6. Lecciones
1. Buscar al cliente antes de escoger los datos: el cambio de tema costó la semana.
2. La puerta de calidad sirvió también para revisar al propio equipo: la revisión de base julio 2019 = 100 confirma en cada corrida que se está leyendo la estructura correcta del índice.
3. Leer las salidas antes de escribir las conclusiones.

## 7. Siguiente etapa
Entrevistas de validación, precio base por ciudad para pasar de índice a pesos, tablero con chat de consulta sobre la capa oro.
