# Entrega E1 · ObraPrecio (TRUSTED DATA LAB)
Equipo: Julio Alberto Orozco Téllez · Ángel Salvador Álvarez Fernández · José Rey Sánchez Navarro (solo Calidad) · Etiqueta: `e1` · Tablero: sin URL pública todavía; corre con `streamlit run tablero/app.py`

## Resumen en tres líneas
ObraPrecio responde cuánto ha subido el costo de construir vivienda en 46 ciudades de México y qué lo mueve (materiales, maquinaria o mano de obra), con el índice oficial de INEGI integrado con el tipo de cambio de Banxico.
Los datos viajan solos de bronce a oro: 96,392 registros de INEGI pasan por una puerta Pandera, 24,604 se rechazan con motivo, y el pronóstico de Colima se elige por error en 36 orígenes (0.43 % a un mes) y se publica con su intervalo.
El proyecto cambió de tema respecto a E0 ([por qué](pivote-obraprecio.md)); quedan abiertos: 5 días de bitácora de 7, tablero sin publicar y pronóstico solo para Colima y Nacional.

## Cómo reproducir
```bash
pip install -r requirements-dev.txt
python -m pytest                      # 63 pruebas, sin internet
python -m pipeline.ejecutar           # bronce -> plata -> oro + cuarentena + reporte
python -m laboratorio.pronosticar     # publica el pronóstico en oro
python calidad/fiabilidad.py          # disponibilidad, MTBF y MTTR
python calidad/respaldo_bronce.py     # respaldo de bronce con prueba de restauración
pip install -r tablero/requirements.txt && streamlit run tablero/app.py
```

## Ingeniería de Datos
| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Valores faltantes (15) | [limpieza.ipynb §3](limpieza.ipynb) · [`limpieza.diagnostico_faltantes`](../../pipeline/limpieza.py) | INEGI: MAR estructural (0 huecos interiores; ji-cuadrada contra década, componente y región). No se imputa hacia atrás; oro arranca en 2004 con panel completo. Método para huecos futuros elegido con un experimento de enmascarado (656 valores). Banxico: MAR por calendario, imputación con último valor y bandera |
| Atípicos y ruido (15) | [limpieza.ipynb §4](limpieza.ipynb) · [`oro.panel_mensual`](../../pipeline/oro.py) | IQR, Z robusto e Isolation Forest, con tabla de decisión por tipo: error de captura a cuarentena, choque real marcado, escalón no es atípico, columna winsorizada para modelos |
| Normalización, discretización y reducción (15) | [limpieza.ipynb §5, §6 y §7](limpieza.ipynb) · [pipeline/catalogos.py](../../pipeline/catalogos.py) | Min-Max y Z-Score con tabla comparativa de uso; discretización por ancho, por frecuencia y por cortes de negocio comparadas; jerarquías ciudad → estado → región y mes → trimestre → año; reducción de 71,788 a 368 filas (99.5 %) con lo que se pierde en cada paso; selección de variables con correlación y PCA |
| Integración de fuentes (20) | [pipeline/plata.py](../../pipeline/plata.py) · [limpieza.ipynb §1](limpieza.ipynb) · [extractores/inegi.py](../../extractores/inegi.py) | INEGI (CSV ancho, Windows-1252, mensual) y Banxico (JSON, UTF-8, diario). Nueve conflictos de esquema y de valores con su regla; duplicados entre capturas resueltos; cambio de estructura de INEGI verificado en 68,968 valores |
| Puerta de calidad (25) | [pipeline/puerta.py](../../pipeline/puerta.py) · [calidad/reporte-puerta.json](../../calidad/reporte-puerta.json) · [data/cuarentena/](../../data/cuarentena/README.md) · [limpieza.ipynb §2](limpieza.ipynb) | Esquemas Pandera estrictos, rangos, unicidad y reglas de negocio; 6 revisiones de conjunto. 24,604 rechazos con motivo y archivo de origen. Balance verificado: bronce = plata + cuarentena + duplicados idénticos |
| Capas plata y oro automáticas, con diccionario | [.github/workflows/captura.yml](../../.github/workflows/captura.yml) · [data/oro/DICCIONARIO.md](../../data/oro/DICCIONARIO.md) | El pipeline corre después de la captura diaria. Cinco tablas de oro documentadas columna por columna |

Cifras de la corrida entregada:

| Fuente | Bronce | Plata | Cuarentena | Duplicados idénticos | Aceptado |
|---|---|---|---|---|---|
| INEGI · INPP construcción residencial por ciudad | 96,392 | 71,788 | 24,604 | 0 | 74.48 % |
| Banxico · FIX | 2,509 | 2,481 | 0 | 28 | 98.88 % |

Cobertura: 188 series (46 ciudades más Nacional × 4 componentes), enero de 1973 a octubre de 2026. Capa oro: 51,512 filas desde enero de 2004.

## Análisis Estadístico
Serie: índice general de costo de construcción de Colima, enero de 2004 a octubre de 2026 (274 meses), con el Nacional como contraste. Cuaderno: [pronostico.ipynb](pronostico.ipynb) · Código: [laboratorio/modelos.py](../../laboratorio/modelos.py)

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Caracterización y descomposición (15) | [pronostico.ipynb §1](pronostico.ipynb) | Tendencia dominante, escalón cada enero, ciclos de 3 a 5 años y salto de nivel en 2021 y 2022. **Multiplicativa**: la amplitud estacional crece con el nivel (correlación 0.52; pasa de 2.4 a 4.9 puntos) |
| Estacionariedad y autocorrelación (15) | [pronostico.ipynb §2](pronostico.ipynb) | Dickey-Fuller y KPSS: no estacionaria en nivel, estacionaria con una diferencia del logaritmo (d = 1). ACF y PACF interpretadas. Correlación cruzada con el tipo de cambio: sin relación de corto plazo |
| Cuatro modelos (25) | [pronostico.ipynb §3](pronostico.ipynb) | Suavizamiento simple, Holt, Holt-Winters y SARIMA, más dos referencias. p, d, q justificados con ACF, PACF y AIC |
| Selección por error (20) | [pronostico.ipynb §4](pronostico.ipynb) | MAE, RMSE y MAPE en los últimos 12 meses y en 36 orígenes móviles. SARIMA (3,1,3)(1,0,1)₁₂ gana a 1 y 3 meses (MAPE 0.43 % y 1.12 %); Holt-Winters a 6 y 12 (1.43 % y 2.34 %) |
| Residuos y comunicación (15) | [pronostico.ipynb §5 y §6](pronostico.ipynb) · [data/oro/pronostico_mensual.csv](../../data/oro/pronostico_mensual.csv) · [tablero/app.py](../../tablero/app.py) | Ljung-Box aprobado en el modelo ganador (p = 0.07 a 12 rezagos, 0.24 a 24). **Varianza estable: no se cumple** (ARCH rechaza); se advierte que los intervalos son aproximados. Pronóstico con intervalo de 80 % y frase para el cliente, mostrado en el tablero |

## Calidad en los Sistemas de Información
| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Fiabilidad y disponibilidad (25) | [calidad/reporte-fiabilidad.md](../../calidad/reporte-fiabilidad.md) · [calidad/fiabilidad.py](../../calidad/fiabilidad.py) · [bitácora](../../calidad/bitacora-captura.csv) | Tasa de éxito 100 % (5 de 5), disponibilidad operativa 100 % contra el objetivo de 95 % de E0. **Solo 5 días de bitácora de los 7 pedidos** (la captura inició el 9). MTBF y MTTR no estimables sin fallas: se reporta la cota y el límite de confianza |
| Seguridad (15) | [calidad/seguridad/](../../calidad/seguridad/README.md) · [respaldo probado](../../calidad/seguridad/respaldo-bronce.md) | gitleaks y pip-audit sin hallazgos, en local y en GitHub Actions. Tokens con permiso mínimo documentado. Respaldo de bronce restaurado: 2,137 archivos, 0 diferencias |
| Requerimientos (10) | [requerimientos.md](requerimientos.md) | 11 funcionales y 15 no funcionales, cada uno con su comprobación; revisados contra necesario, no ambiguo, verificable y rastreable; revisión de José Rey con 7 observaciones y su atención |
| Plan SQA (25) | [docs/plan-sqa.md](../plan-sqa.md) | Estructura IEEE 730 adaptada al proyecto, versión 1.2: revisada por José Rey, pendiente de su aprobación final |
| Integración continua (15) | [.github/workflows/ci.yml](../../.github/workflows/ci.yml) · [tests/](../../tests/) | Pruebas (63), linter, puerta de datos y seguridad en cada push. Pipeline: 6 s en GitHub Actions |

Registro de defectos: [calidad/defectos-e1.csv](../../calidad/defectos-e1.csv) (9 defectos, 9 cerrados).

## Relatoría de etapa
[docs/relatoria-E1.md](../relatoria-E1.md)

## Limitaciones conocidas
1. **Bitácora de 5 días, no de 7.** No se puede reponer.
2. **El tablero no tiene URL pública.** Está construido y probado en local.
3. **Pronóstico solo para Colima y Nacional**, índice general. Intervalos aproximados: la varianza de los residuos no es estable.
4. **Registros individuales de tiempo y de defectos sin llevar** en E1; el de defectos se llevó por equipo.
5. **El equipo tiene tres personas** y el proyecto pide máximo dos; pendiente de consultar con los docentes.
6. El tipo de cambio en bronce inicia en 2017. El índice mide variación, no precios en pesos. La captura de CENACE de E0 sigue activa pero ya no es parte del producto.
7. Etiquetas `e1-final` y `e1-v2`: versiones intermedias del mismo día; la entrega es `e1`.

## Uso de IA generativa
Declarado en la [relatoría](../relatoria-E1.md).

## Issues de la entrega anterior
E0 no recibió issues formales. Pendientes propios de E0: la entrevista con cliente (se hizo una primera, con un familiar; faltan las de usuarios externos) y el nombre del tercer integrante en la ficha (corregido).
