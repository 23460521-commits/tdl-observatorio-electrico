# Observatorio Eléctrico de Colima · TRUSTED DATA LAB

**¿Cuándo vale más la electricidad en Colima y cuánto vale la energía solar que un negocio inyecta a la red según la hora y el día?**

Observatorio de datos del Proyecto Integrador TRUSTED DATA LAB (TecNM campus Colima): Ingeniería de Datos, Análisis Estadístico para Ciencia de Datos y Calidad en los Sistemas de Información.

- Tablero público: _pendiente (E1)_
- Equipo: _integrantes_

## Fuentes

| Fuente | Qué aporta | Acceso | Frecuencia de captura |
|---|---|---|---|
| CENACE, servicio web SW-PEND | Precio horario por zona de carga (MXN/MWh) y sus componentes de energía, pérdidas y congestión, Mercado de Día en Adelanto | API pública sin llave | Diaria (GitHub Actions) |
| Banxico, API del SIE | Tipo de cambio FIX (pesos por dólar), serie SF43718 | API pública con token gratuito | Diaria (GitHub Actions) |

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
