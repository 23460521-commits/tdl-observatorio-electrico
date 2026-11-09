# Propuesta · Observatorio Eléctrico de Colima

**Proyecto Integrador TRUSTED DATA LAB** · Tecnológico Nacional de México, campus Colima
**Equipo:** Julio Alberto Orozco Téllez (23460521) · ⟨PENDIENTE: compañero/a y matrícula⟩
**Roles:** Data Engineer: ⟨PENDIENTE⟩ · Data Statistician: ⟨PENDIENTE⟩
**Repositorio:** ⟨PENDIENTE: URL⟩ · **Versión:** E0, noviembre de 2026

---

## 1. Ficha del observatorio

| Campo | Contenido |
|---|---|
| Sector | Mercado eléctrico mayorista y autoconsumo con energía solar |
| Región | Colima, comparada con otras zonas de carga del Sistema Interconectado Nacional (SIN) |
| Pregunta central | ¿Cuándo vale más la electricidad en Colima y cuánto valdría, según la hora y el día, la energía solar que una empresa colimense inyecta a la red? |
| Unidad de observación | Precio horario por zona de carga ($/MWh) y clima horario por ciudad |
| Quién pagaría | Desarrolladores e instaladores de proyectos solares y empresas medianas o grandes de Colima que evalúan un sistema de autoconsumo (agroindustria, empacadoras con refrigeración, hoteles, industria en Manzanillo) |
| Por qué pagaría | Para estimar con datos, y no con promedios genéricos, cuánto ahorra o cuánto cobra un sistema solar según la hora en que produce |

## 2. Contexto: por qué esta pregunta vale dinero

El Centro Nacional de Control de Energía (CENACE) calcula para cada hora y cada zona de carga un precio de la energía. Este precio se compone de tres partes: energía, pérdidas y congestión. Los precios del Mercado de Día en Adelanto (MDA) se publican un día antes del día de operación, y los del Mercado de Tiempo Real, siete días después [1]. Los datos existen desde 2016 y son públicos, pero están dispersos en servicios técnicos que casi nadie consulta.

Desde el 13 de diciembre de 2025 rigen las Disposiciones Administrativas de Carácter General para el Autoconsumo de Energía Eléctrica, publicadas por la Comisión Nacional de Energía [3]. Para las centrales de autoconsumo de 0.7 MW o más, los excedentes solo pueden venderse a CFE. Si la central usa energía limpia, la energía se paga a 0.9 veces el menor valor entre el costo nivelado de la última subasta y el Precio Marginal Local (PML) horario, y un PML negativo se toma como cero [3]. En la práctica, el valor de cada kWh que una empresa inyecta depende del precio de la hora en que lo produce. Eso es justo lo que este observatorio mide, pronostica y compara.

**Alcance honesto:** los sistemas solares pequeños (menos de 0.7 MW, como los techos de casas y comercios) se rigen por otro esquema. El observatorio no promete calcular su tarifa. Para ellos, el valor está en saber en qué horas y temporadas la energía de la red es más cara.

## 3. Entrevista con el sector

Guion completo: [`guion-entrevista.md`](guion-entrevista.md).

| Campo | Registro |
|---|---|
| Perfil de la persona entrevistada (giro y cargo, sin nombre) | ⟨PENDIENTE⟩ |
| Fecha, medio y duración (mínimo 15 min) | ⟨PENDIENTE⟩ |

| # | Pregunta | Respuesta (resumen) |
|---|---|---|
| 1 | ¿Cómo estiman hoy el ahorro o el pago por excedentes de un sistema solar? ¿Qué datos usan? | ⟨PENDIENTE⟩ |
| 2 | ¿Qué proporción de sus proyectos en Colima son menores y mayores a 0.7 MW? | ⟨PENDIENTE⟩ |
| 3 | ¿En qué horas y meses les importa más el precio de la energía? | ⟨PENDIENTE⟩ |
| 4 | Si tuvieran un pronóstico del precio por hora en Colima a dos semanas, ¿qué decisión cambiarían? ¿En qué formato lo querrían? | ⟨PENDIENTE⟩ |
| 5 | ¿Cuánto les cuesta hoy no tener esta información y cuánto pagarían por ella? | ⟨PENDIENTE⟩ |

**Lo que aprendimos:** ⟨PENDIENTE: 3 a 5 líneas. Qué confirmó la entrevista, qué cambió de la propuesta y qué no esperábamos.⟩

## 4. Preguntas analíticas

Cada pregunta corresponde a una técnica del proyecto y se puede responder con un número.

**P1 · Pronóstico (E1).** ¿Qué modelo pronostica con menor error el precio promedio diario de la zona de carga de Colima a 14 días? Variable: promedio diario de `pz` (MDA) en $/MWh. Se comparan suavizamiento exponencial simple, Holt, Holt-Winters con estacionalidad semanal y SARIMA, con MAE, RMSE y MAPE sobre las últimas 8 semanas reservadas como prueba. Serie disponible: diaria desde 2017, más de 3,500 periodos.

**P2 · Experimento (E2, ruta ingeniería).** ¿Qué combinación de factores reduce más el tiempo de procesamiento de bronce a plata sin aumentar los errores? Diseño 2³ sobre una copia local de la capa bronce, sin peticiones a CENACE:

| Factor | Nivel bajo | Nivel alto |
|---|---|---|
| A · Procesos en paralelo | 1 | 4 |
| B · Lector de JSON | `json` (biblioteca estándar) | `orjson` |
| C · Formato de escritura | CSV | Parquet |

Respuestas: tiempo de procesamiento de un año de datos (segundos) y registros enviados a cuarentena. Se harán dos réplicas por tratamiento, con orden aleatorizado y la máquina como bloque. Para el diseño de dos factores con tres niveles o más se usará procesos (1, 2, 4, 8) × formato (CSV, Parquet).

**P3 · Multivariado (E3).** ¿Las zonas de carga difieren a la vez en precio medio, volatilidad, peso de la congestión, peso de las pérdidas, diferencia entre la hora pico y la hora valle, y relación con la temperatura? ¿Qué perfiles forman? Unidad de análisis: zona × mes (aproximadamente 115 meses por zona). Grupos: al menos tres zonas de carga, incluida Colima, o las gerencias regionales a las que pertenecen. Técnicas: MANOVA (lambda de Wilks y traza de Pillai) y componentes principales.

## 5. Plan de recopilación

### 5.1 CENACE · Servicio web SW-PEND (fuente principal, captura diaria)

| Aspecto | Detalle |
|---|---|
| Qué contiene | Precio de la energía por zona de carga para cada hora (`pz`) y sus componentes de energía (`pz_ene`), pérdidas (`pz_per`) y congestión (`pz_cng`), en $/MWh [1]. Cada precio de zona es el promedio ponderado de los PML de sus nodos [1] |
| Estructura | `Resultados` → una entrada por zona (`zona_carga`) → `Valores` → un registro por hora con `fecha`, `hora` y los cuatro precios. Encabezado con `status`, `proceso` y `sistema` [1] |
| Formato | JSON, solicitado de forma explícita (el formato por omisión es XML) [1] |
| Acceso | REST con GET, sin llave: `https://ws01.cenace.gob.mx:8082/SWPEND/SIM/{sistema}/{proceso}/{zonas}/{aaaa/mm/dd inicio}/{aaaa/mm/dd fin}/JSON` [1] |
| Límites | De 1 a 10 zonas y de 1 a 7 días de operación por petición [1] |
| Frecuencia de actualización | Diaria. El MDA se publica un día antes del día de operación [1] |
| Historia disponible | MDA del SIN desde el 29 de enero de 2016 [1]. Usaremos desde el 1 de enero de 2017 (años completos) |
| Códigos de respuesta | 200 OK, 204 sin contenido, 401 no autorizado y 404 no encontrado [1] |
| robots.txt | ⟨PENDIENTE: resultado que registre el extractor en la primera ejecución⟩. Una fuente de terceros reporta que el servidor del servicio no publica robots.txt [5]. El extractor lo verifica en cada ejecución y se detiene si encuentra una regla que lo prohíba |
| Términos de uso | El manual establece que el servicio es propiedad de CENACE y es para uso del público en general, exclusivamente para descargar esta información, y que CENACE puede deshabilitarlo sin aviso si se usa indebidamente [1] |
| Licencia | Los mismos precios se publican como datos abiertos en datos.gob.mx bajo Creative Commons Atribución 4.0 [2] |
| Cómo cumplimos | User-Agent con el nombre del proyecto y un correo de contacto, pausa mínima de 1.5 s entre peticiones, una sola ejecución diaria con 2 o 3 peticiones, histórico descargado una única vez y de forma reanudable, y atribución a CENACE en el tablero y en el dataset. Si el servicio no está disponible, se notifica al correo de soporte que indica el manual [1] |
| Datos personales | Ninguno: solo claves de zona, fechas, horas y precios |

### 5.2 Open-Meteo (fuente complementaria, captura diaria)

| Aspecto | Detalle |
|---|---|
| Qué contiene | Temperatura, humedad relativa, radiación solar de onda corta, nubosidad y precipitación por hora en 8 ciudades (Colima, Manzanillo, Guadalajara, Monterrey, Ciudad de México, Culiacán, Hermosillo y Mérida) |
| Estructura | Una lista con un objeto por ubicación. Cada objeto tiene un bloque `hourly` con el arreglo `time` y un arreglo por variable |
| Formato | JSON |
| Acceso | REST sin llave. Captura diaria: API de pronóstico con los 3 días anteriores y los 2 siguientes. Histórico: API de archivo por bloques anuales |
| Frecuencia de actualización | El pronóstico se actualiza varias veces al día. El archivo histórico tiene algunos días de retraso |
| Historia disponible | Décadas de datos horarios, más de lo que necesitamos desde 2017 |
| robots.txt | ⟨PENDIENTE: resultado que registre el extractor en la primera ejecución⟩ |
| Términos de uso | La API gratuita es para uso no comercial y pide uso justo. Para uso comercial, o para más de 10,000 llamadas al día, se requiere una suscripción [4] |
| Licencia | Datos bajo CC BY 4.0, que exige atribución con el texto "Weather data by Open-Meteo.com" junto a donde se muestren [4] |
| Cómo cumplimos | Una llamada diaria para las 8 ciudades (muy por debajo del límite) y atribución visible en el tablero. **Riesgo para el modelo de negocio:** si el observatorio se vende, el clima debe pasar a la suscripción de Open-Meteo o a una fuente pública mexicana, como el Servicio Meteorológico Nacional. Este costo se incluirá en el modelo de negocio de E4 |
| Datos personales | Ninguno |

### 5.3 Fuente especializada (E2)

Opción preferida: **geoespacial**, con un mapa de las zonas de carga y su precio medio. La unión espacial se hará en GeoPandas, usando las coordenadas de las ciudades y el Marco Geoestadístico de INEGI. La decisión final y su análisis ético y legal van en `docs/etica-datos.md` en E2.

## 6. Captura y serie histórica

| Elemento | Estado |
|---|---|
| Zonas de carga confirmadas contra el servicio | ⟨PENDIENTE: resultado de `descubrir_zonas` (deben incluir al menos una de Colima)⟩ |
| Captura programada | GitHub Actions, diaria a las 21:17 (hora del centro), en `.github/workflows/captura.yml` |
| Primera ejecución exitosa | ⟨PENDIENTE: fecha y enlace a la ejecución en Actions⟩ |
| Serie histórica en bronce | ⟨PENDIENTE: rango descargado y número de bloques⟩. Estimado: unos 3,600 días × 24 horas por zona, es decir, más de 86,000 registros horarios por zona |
| Almacenamiento en bronce | La respuesta exacta comprimida (`.json.gz`) más un `.meta.json` con URL, fecha de captura, estado HTTP, intentos y SHA-256 |
| Tolerancia a fallas | Cada captura pide los últimos 4 días, así que una falla se recupera en la siguiente ejecución. Los duplicados que esto genera se eliminan en la capa plata (E1) |

## 7. Arranque del sistema de calidad

**Registros individuales (PSP):** `calidad/defectos-<nombre>.csv` y `calidad/tiempo-<nombre>.csv`, uno por integrante, con los 10 tipos de defecto de PSP.

**Bitácora de captura:** `calidad/bitacora-captura.csv`. El flujo agrega una fila por fuente en cada ejecución, con inicio, fin, duración, estado (`exito`, `fallo` u `omitido`), registros, intentos y mensaje de error. Es el insumo para medir MTBF, MTTR y disponibilidad en E1.

**Objetivos de calidad**

| # | Objetivo | Métrica y cálculo | Meta | Fuente de la medición |
|---|---|---|---|---|
| 1 | Disponibilidad de la captura | Ejecuciones programadas en las que todas las fuentes obligatorias terminan en `exito`, entre el total de ejecuciones programadas, en ventanas de 14 días | ≥ 95 % | Bitácora de captura e historial de GitHub Actions |
| 2 | Recuperación rápida ante fallas (MTTR) | Tiempo promedio entre la primera ejecución con `fallo` y la siguiente con `exito` de la misma fuente | ≤ 24 horas | Bitácora de captura |
| 3 | Completitud de la serie de precios | Horas presentes entre horas esperadas (24 por zona y día de operación) en la serie integrada | ≥ 99 % en plata y ≥ 95 % en oro (umbral del Sello TDL) | Reporte de la puerta de calidad (E1) |

## 8. Riesgos principales

| Riesgo | Efecto | Mitigación |
|---|---|---|
| Ningún nombre candidato coincide con una zona de carga de Colima | La pregunta central pierde su región | Consultar el Catálogo de NodosP de CENACE [1]. Como alternativa, usar el servicio SW-PML con los nodos ubicados en Colima |
| Error de certificado SSL con el servidor de CENACE | La captura falla | Configurar la cadena de certificados con `REQUESTS_CA_BUNDLE`, sin desactivar la verificación, y registrarlo como defecto de entorno |
| CENACE republica precios corregidos | Hay versiones distintas de un mismo día | Bronce conserva todas las capturas con su fecha. La plata se queda con la más reciente y registra el cambio |
| Open-Meteo no permite uso comercial gratuito | Costo en el modelo de negocio | Presupuestar la suscripción o cambiar a la fuente del SMN |
| Menos de 7 días de bitácora al entregar E1 | Medición de fiabilidad incompleta | Acordar con la docente medir con 7 días contados desde la primera ejecución |

## Referencias

[1] CENACE, *Manual Técnico. Uso de Servicio Web para descarga de Precios de Energía en Nodos Distribuidos (SW-PEND)*, 24 de junio de 2022. https://www.cenace.gob.mx/DocsMEM/2022-06-24%20Manual%20T%C3%A9cnico%20SW-PEND.pdf

[2] CENACE en datos.gob.mx, *Precios Marginales Locales de Energía, Mercado de Día en Adelanto, Sistema Interconectado Nacional, 2021* (licencia Creative Commons Attribution 4.0). https://www.datos.gob.mx/dataset/groups/pml_energia_mda_sistema_interconectado_nacional_2021

[3] Pérez-Llorca, *Se publican las DACGs para regular la figura del Autoconsumo de Energía Eléctrica*, nota jurídica, diciembre de 2025. Texto oficial: Acuerdo de la CNE publicado en el DOF el 12 de diciembre de 2025. https://www.perezllorca.com/wp-content/uploads/2025/12/Nota-Juridica-Se-publican-las-DACGs-para-regular-la-figura-del-Autoconsumo-de-Energia-Electrica-.pdf

[4] Open-Meteo, página principal y términos de uso. https://open-meteo.com/ · https://open-meteo.com/en/terms

[5] Plainwork Tools, *Mexico Day-Ahead & Historical Power Prices (CENACE)*, documentación en Apify (fuente no oficial; se usa solo como referencia secundaria). https://apify.com/plainworktools/mexico-power-prices-cenace
