# ObraPrecio · TRUSTED DATA LAB

**¿Cuánto ha subido el costo de construir una vivienda en mi ciudad y qué lo está moviendo: los materiales, la maquinaria o la mano de obra?**

Proyecto Integrador TRUSTED DATA LAB (TecNM campus Colima): Ingeniería de Datos, Análisis Estadístico para Ciencia de Datos y Calidad en los Sistemas de Información.

- Equipo: Julio Alberto Orozco Téllez · Ángel Salvador Álvarez · José Rey Sánchez Navarro
- Entregas: [E0](docs/E0/ENTREGA.md) · [E1](docs/E1/ENTREGA.md) · [por qué cambió el tema](docs/E1/pivote-obraprecio.md)
- Tablero público: _pendiente (E2)_

> El repositorio conserva el nombre de la propuesta original (Observatorio Eléctrico de Colima). La captura de CENACE sigue activa en bronce, pero el producto es ObraPrecio.

## Fuentes

| Fuente | Qué aporta | Acceso | Frecuencia de captura |
|---|---|---|---|
| INEGI, Índice Nacional de Precios Productor, "Construcción residencial por ciudad" (base julio 2019 = 100) | Índice general, materiales, alquiler de maquinaria y mano de obra para 46 ciudades y el total nacional, mensual | Consulta pública sin llave | Semanal (lunes) |
| Banxico, API del SIE | Tipo de cambio FIX (pesos por dólar), serie SF43718 | API pública con token gratuito | Diaria |
| CENACE, servicio web SW-PEND (propuesta original) | Precio horario de la electricidad por zona de carga | API pública sin llave | Diaria |

Fuente de los datos de construcción: INEGI, Índice Nacional de Precios Productor. Fuente del tipo de cambio: Banco de México.

## Capas de datos

```
fuentes -> data/bronce (respuesta exacta + SHA-256)
        -> puerta de calidad (Pandera)  -> data/cuarentena (rechazados, con motivo)
        -> data/plata (tablas limpias y tipadas)
        -> data/oro (tablas de análisis)
```

| Tabla | Contenido |
|---|---|
| `data/plata/inpp_construccion.csv` | Una fila por serie y mes desde 1973, con ciudad, estado, región y componente |
| `data/plata/fix_diario.csv` | FIX por día natural; `imputado` marca fines de semana y festivos |
| `data/oro/obraprecio_panel_mensual.csv` | Desde 2004: índice, variaciones, nivel de inflación, banderas de atípicos, normalizaciones y tipo de cambio |
| `data/oro/obraprecio_ciudad_mensual.csv` | Una fila por ciudad y mes con los 4 componentes en columnas |
| `data/oro/resumen_region_anual.csv` | Agregado por región, año y componente |
| `data/oro/ranking_ciudades.csv` | Último mes: ciudades ordenadas por variación anual |

```bash
python -m pipeline.ejecutar      # regenera plata, oro, cuarentena y calidad/reporte-puerta.json
python calidad/fiabilidad.py     # recalcula calidad/reporte-fiabilidad.md
```

Pronóstico del índice: [docs/E1/pronostico.ipynb](docs/E1/pronostico.ipynb) con `laboratorio/modelos.py`. Calidad: [plan SQA](docs/plan-sqa.md), [requerimientos](docs/E1/requerimientos.md), [fiabilidad](calidad/reporte-fiabilidad.md) y [seguridad](calidad/seguridad/README.md).

Para regenerar el catálogo de series o bajar de nuevo la historia de INEGI: `python -m extractores.inegi --catalogo --historico`.

## Puesta en marcha (una sola vez)

```bash
python -m venv .venv
source .venv/bin/activate          # en Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python -m pytest                   # pruebas sin internet
```

1. **Confirmar las zonas de carga.** Prueba cada nombre de `extractores/config.py` contra CENACE y guarda los que responden en `extractores/zonas_confirmadas.json`:
   ```bash
   python -m extractores.descubrir_zonas
   ```
2. **Descargar la serie histórica** a la capa bronce (desde 2017; tarda entre 30 y 60 minutos porque respeta una pausa entre peticiones; es reanudable, si se corta se vuelve a correr):
   ```bash
   python -m extractores.historico
   ```
   Para Banxico se necesita el token en la terminal (ver "Token de Banxico" abajo):
   ```bash
   python -m extractores.historico --fuente banxico
   ```
3. **Subir todo a GitHub** (incluido `zonas_confirmadas.json` y `data/bronce`).
4. En GitHub, en *Settings → Secrets and variables → Actions → Variables*, crear la variable `TDL_CONTACTO` con el correo del equipo. El extractor la usa para identificarse. En la pestaña *Secrets* del mismo lugar, crear el secret `BANXICO_TOKEN` con el token de Banxico.
5. En la pestaña *Actions*, abrir **Captura diaria** y pulsar *Run workflow* para la primera ejecución. A partir de ahí corre sola todos los días a las 21:17 (hora del centro).

## Token de Banxico

1. Solicitarlo gratis en https://www.banxico.org.mx/SieAPIRest/service/v1/token (se muestra al momento).
2. **Nunca** escribirlo en el código ni subirlo al repositorio. En GitHub va como *secret* `BANXICO_TOKEN`.
3. Para usarlo en la terminal de PowerShell (solo dura mientras la ventana esté abierta):
   ```powershell
   $env:BANXICO_TOKEN = "pega-aqui-tu-token"
   ```

## Cómo funciona la captura

- `extractores/base.py`: extractor ético del Kit. Lee robots.txt, se identifica, espera al menos 1.5 s entre peticiones al mismo dominio y reintenta con espera exponencial.
- `extractores/inegi.py`: los lunes pide a INEGI el año en curso y el anterior de las 188 series (4 peticiones).
- `extractores/captura_diaria.py`: pide a CENACE los últimos 4 días (así una ejecución fallida se recupera en la siguiente) y el día de mañana si ya está publicado, y a Banxico los últimos 10 días del tipo de cambio FIX.
- Cada respuesta se guarda **tal como llegó** en `data/bronce/<fuente>/`, comprimida, con un `.meta.json` que registra URL, fecha de captura, estado HTTP y SHA-256.
- Cada ejecución agrega una fila por fuente a `calidad/bitacora-captura.csv` (estado `exito`, `fallo` u `omitido`). Con esa bitácora se calculan MTBF, MTTR y disponibilidad en E1.

## Si algo falla

- **Error de certificado SSL con CENACE**: no desactiven la verificación (`verify=False`). Descarguen la cadena de certificados del servidor y apúntenla con la variable de entorno `REQUESTS_CA_BUNDLE`. Registren el caso como defecto de tipo *entorno*.
- **`descubrir_zonas` no confirma ninguna zona de Colima**: revisen el nombre exacto en el catálogo de zonas de carga de CENACE y corríjanlo en `ZONAS_CANDIDATAS`.
- **El workflow no puede hacer push**: en *Settings → Actions → General → Workflow permissions*, elegir *Read and write permissions*.

## Estructura

```
├── docs/                 fichas de entrega, propuesta, relatorías, plan SQA
├── calidad/              defectos y tiempo por integrante, bitácora de captura
├── extractores/          un módulo por fuente + captura diaria e histórico
├── pipeline/             bronce -> plata -> oro y puertas de calidad (E1)
├── data/bronce|plata|oro|cuarentena
├── laboratorio/          notebooks de series, experimento y multivariado
├── tablero/              Streamlit
├── tests/
└── .github/workflows/    captura programada (e integración continua en E1)
```

## Atribución

Datos de precios: CENACE (Centro Nacional de Control de Energía). Tipo de cambio: Banco de México, Sistema de Información Económica. Las licencias y términos de uso de cada fuente se documentan en `docs/E0/propuesta.md`.
