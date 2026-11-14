# Diccionario de datos · capa oro

Las tablas de esta carpeta se regeneran completas con `python -m pipeline.ejecutar` (y el pronóstico con `python -m laboratorio.pronosticar`). No se editan a mano. Todas son CSV en UTF-8, separador coma, punto decimal y fechas `AAAA-MM-DD`.

Fuentes: INEGI, Índice Nacional de Precios Productor, "Construcción residencial por ciudad" (base julio 2019 = 100); Banco de México, tipo de cambio FIX.

Convenciones:
- Los índices no tienen unidad: 100 es el costo de julio de 2019. Un índice de 163 significa 63 % más caro que entonces.
- Las variaciones están en porcentaje (%). Las brechas, en puntos porcentuales (pp).
- Una celda vacía significa "no existe el dato" y nunca cero. Las causas posibles están anotadas en cada columna.
- Componentes: `general`, `materiales`, `maquinaria` (alquiler de maquinaria) y `mano_obra`.

## `obraprecio_panel_mensual.csv`
Una fila por serie (ciudad × componente) y mes, desde enero de 2004. Llave: `serie` + `fecha` (equivale a `ciudad_id` + `componente` + `fecha`).

| Columna | Tipo | Descripción | Vacíos |
|---|---|---|---|
| `fecha` | fecha | Primer día del mes al que corresponde el dato | No |
| `anio`, `trimestre`, `mes` | entero, texto, entero | Jerarquía temporal: mes → trimestre (`2026-T4`) → año | No |
| `ciudad_id` | texto | Clave estable de la ciudad, sin acentos ni espacios (`colima`, `nacional`) | No |
| `ciudad`, `estado`, `region` | texto | Jerarquía geográfica: ciudad → estado → región (Norte, Centro Norte, Centro, Sur; regionalización de Banco de México). El total del país lleva `Nacional` | No |
| `componente` | texto | `general`, `materiales`, `maquinaria` o `mano_obra` | No |
| `serie` | texto | Clave de la serie en la estructura vigente de INEGI | No |
| `indice` | decimal | Índice de costo de construcción, julio 2019 = 100 | No |
| `var_mensual_pct` | decimal | Cambio contra el mes anterior, % | No |
| `var_anual_pct` | decimal | Cambio contra el mismo mes del año anterior, % | En 2004, para las series que inician en diciembre de 2003 |
| `var_anual_nacional_pct` | decimal | `var_anual_pct` del índice Nacional del mismo componente y mes | Igual que la anterior |
| `brecha_vs_nacional_pp` | decimal | `var_anual_pct` − `var_anual_nacional_pct`. Positivo: la ciudad sube más que el país | Igual |
| `nivel_inflacion` | categoría | Discretización de `var_anual_pct` con cortes de negocio: `deflacion` (< 0), `baja` (0 a 3), `moderada` (3 a 6), `alta` (6 a 10), `muy_alta` (≥ 10) | Igual |
| `costo_relativo` | categoría | Tercil de `var_anual_pct` entre todas las ciudades, por componente y mes: `bajo`, `medio`, `alto` | Igual; también en meses donde más de un tercio de las ciudades empata (mano de obra) |
| `indice_minmax` | decimal 0 a 1 | `indice` normalizado Min-Max dentro de su serie (0 = mínimo desde 2004, 1 = máximo) | No |
| `var_mensual_z` | decimal | `var_mensual_pct` estandarizada (Z-Score) dentro de su serie | No |
| `serie_escalonada` | booleano | `True` si en ese componente más de la mitad de los meses no cambian (mano de obra, maquinaria) | No |
| `z_robusto` | decimal | Z modificado (mediana y MAD) de `var_mensual_pct` dentro del componente. En series escalonadas, 0 cuando el mes no cambió | No |
| `atipico_iqr` | booleano | Fuera de Q1 − 3·IQR, Q3 + 3·IQR | No |
| `atipico_z` | booleano | \|`z_robusto`\| > 3.5 | No |
| `atipico_iforest` | booleano | Marcado por Isolation Forest (variación mensual, anual y brecha; 1 % de contaminación) | No (`False` si le falta algún insumo) |
| `atipico_votos` | entero 0 a 3 | Cuántos de los tres métodos lo marcan | No |
| `var_mensual_tratada_pct` | decimal | `var_mensual_pct` recortada (winsorizada) a mediana ± 3.5 escalas robustas. Para modelos; el valor original no cambia | No |
| `fix_promedio` | decimal | Promedio mensual del tipo de cambio FIX, pesos por dólar | Antes de enero de 2017 (el observatorio no tiene FIX anterior) |
| `fix_cierre` | decimal | FIX vigente el último día del mes | Igual |
| `fix_var_mensual_pct` | decimal | Cambio de `fix_promedio` contra el mes anterior, % | Antes de febrero de 2017 |

## `obraprecio_ciudad_mensual.csv`
Una fila por ciudad y mes, con los cuatro componentes en columnas. Es la tabla que usan el tablero y el laboratorio de pronóstico. Llave: `ciudad_id` + `fecha`.

| Columna | Tipo | Descripción |
|---|---|---|
| `fecha`, `ciudad_id`, `ciudad`, `estado`, `region` | | Igual que en el panel |
| `indice_general`, `indice_materiales`, `indice_maquinaria`, `indice_mano_obra` | decimal | Índice de cada componente |
| `var_anual_general`, `var_anual_materiales`, `var_anual_maquinaria`, `var_anual_mano_obra` | decimal | Variación anual de cada componente, % |
| `var_mensual_pct`, `brecha_vs_nacional_pp`, `nivel_inflacion`, `costo_relativo` | | Los del componente `general` |
| `fix_promedio`, `fix_var_mensual_pct` | decimal | Tipo de cambio del mes |

## `resumen_region_anual.csv`
Agregado por región, año y componente (sin el total Nacional). Llave: `anio` + `region` + `componente`.

| Columna | Tipo | Descripción |
|---|---|---|
| `anio`, `region`, `componente` | | Llave |
| `ciudades` | entero | Ciudades de la región |
| `meses` | entero | Meses con dato en el año (12, salvo el año en curso) |
| `indice_promedio` | decimal | Promedio del índice de las ciudades de la región en el año |
| `var_mensual_media_pct`, `var_mensual_desv_pct` | decimal | Media y desviación estándar de la variación mensual |
| `var_anual_cierre_pct` | decimal | Promedio entre ciudades de la variación anual del último mes del año |
| `atipicos` | entero | Meses-ciudad marcados como atípicos por 2 o más métodos |

## `ranking_ciudades.csv`
Una fila por ciudad con el último mes publicado. Llave: `ciudad_id`.

| Columna | Tipo | Descripción |
|---|---|---|
| `fecha` | fecha | Mes del ranking |
| `ciudad_id`, `ciudad`, `estado`, `region` | texto | Ciudad |
| `var_anual_general`, `var_anual_materiales`, `var_anual_maquinaria`, `var_anual_mano_obra` | decimal | Variación anual por componente, % |
| `lugar` | entero | Posición por `var_anual_general` (1 = donde más subió) |
| `var_anual_nacional` | decimal | Variación anual del índice general Nacional |
| `supera_nacional` | booleano | `True` si la ciudad subió más que el país |

## `pronostico_mensual.csv`
Pronóstico del índice general a 12 meses, para las ciudades con modelo validado (Colima y Nacional). Llave: `ciudad_id` + `fecha`. La elección de modelos está en `docs/E1/pronostico.ipynb`.

| Columna | Tipo | Descripción |
|---|---|---|
| `ciudad_id`, `ciudad` | texto | Ciudad |
| `fecha` | fecha | Mes pronosticado |
| `horizonte_meses` | entero 1 a 12 | Meses después del último dato |
| `ultimo_dato`, `indice_ultimo_dato` | fecha, decimal | Último mes observado y su índice |
| `pronostico_sarima` | decimal | Índice pronosticado con SARIMA (modelo para 1 a 3 meses) |
| `ic80_inf`, `ic80_sup`, `ic95_inf`, `ic95_sup` | decimal | Intervalos de predicción de 80 % y 95 % del SARIMA. Son aproximados: la varianza de los residuos no es estable |
| `pronostico_holt_winters` | decimal | Índice pronosticado con Holt-Winters (modelo para 6 a 12 meses) |
| `var_vs_ultimo_dato_pct` | decimal | Cambio del pronóstico SARIMA contra el último dato, % |
| `var_anual_pct` | decimal | Cambio contra el mismo mes del año anterior, % |
| `error_esperado_sarima_pct`, `error_esperado_holt_winters_pct` | decimal | MAPE medido en la validación de 36 orígenes, para el horizonte validado igual o siguiente (1, 3, 6 o 12 meses) |
| `modelo_sarima` | texto | Órdenes del modelo |

## Qué no hay
- **Precios en pesos.** El índice mide cuánto cambia el costo, no cuánto cuesta una obra.
- **Datos personales.** Todo es estadística agregada por ciudad.
- **Pronóstico por componente o para las otras 45 ciudades.** Pendiente.
