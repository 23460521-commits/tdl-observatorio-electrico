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
- **Los datos de la estructura consultada terminan en julio de 2025.** Se detectó al revisar el periodo disponible que declara la fuente. No se resolvió en esta etapa; queda como primera limitación en la ficha.
- **Un componente llegó con otro nombre** ("-- Materiales de construcción") y generaba una quinta categoría. Se detectó al revisar la matriz de correlaciones.
- **Dos afirmaciones del cuaderno no coincidían con sus propias salidas** (número de celdas faltantes y oleadas de incorporación de ciudades). Se corrigieron contra los datos antes de entregar.
- **El tipo de cambio solo cubre desde 2017**, por lo que la integración con el índice queda parcial de 2004 a 2016.
- Los seis defectos están registrados en [calidad/defectos-e1.csv](../calidad/defectos-e1.csv).

## 4. Qué no se hizo
- La entrevista con un cliente, pendiente desde E0.
- El tablero público.
- Apagar o separar la captura de CENACE, que ya no es parte del producto.
- La parte de Análisis Estadístico y el plan SQA no forman parte de esta relatoría de Ingeniería de Datos; se entregan por separado.

## 5. Reparto del trabajo
| Integrante | E1 |
|---|---|
| Julio Alberto Orozco Téllez | Administrador del repositorio; base de extractores y captura diaria de E0 que E1 reutiliza |
| Ángel Salvador Álvarez | Propuesta del cambio de tema, coordinación con el equipo y los docentes, dirección y revisión del pipeline de E1 construido con asistencia de IA |
| José Rey Sánchez Navarro | Calidad: plan SQA, requerimientos, fiabilidad y seguridad (en curso) |

## 6. Lecciones
1. Buscar al cliente antes de escoger los datos: el cambio de tema costó la semana.
2. La puerta de calidad sirvió también para revisar al propio equipo: la revisión de base julio 2019 = 100 confirma en cada corrida que se está leyendo la estructura correcta del índice.
3. Leer las salidas antes de escribir las conclusiones.

## 7. Siguiente etapa
Entrevistas de validación, estructura vigente del índice, precio base por ciudad para pasar de índice a pesos, tablero con chat de consulta sobre la capa oro.
