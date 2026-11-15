# Seguridad: resultados de E1

Revisión del 13 de noviembre de 2026 sobre la versión que se entrega. Los archivos JSON de esta carpeta son la salida original de cada herramienta. Las dos herramientas corren además en GitHub Actions en cada push (trabajo `seguridad` de [ci.yml](../../.github/workflows/ci.yml)).

## Resultados

| Revisión | Herramienta | Alcance | Resultado | Evidencia |
|---|---|---|---|---|
| Secretos en el historial | gitleaks 8.24.3 (`gitleaks git`) | Todos los commits del repositorio (16 al momento de la revisión) | **0 hallazgos** | [gitleaks-historial.json](gitleaks-historial.json) |
| Secretos en los archivos actuales | gitleaks 8.24.3 (`gitleaks dir`) | Todo el árbol de trabajo, incluidos los datos (108 MB) | **0 hallazgos** | [gitleaks-archivos.json](gitleaks-archivos.json) |
| Dependencias vulnerables | pip-audit | `requirements.txt` (29 paquetes con transitivas) y `tablero/requirements.txt` | **0 vulnerabilidades conocidas** | [pip-audit.json](pip-audit.json) |
| Las mismas dos, en GitHub Actions | CI, trabajo `seguridad` | Commit `41e0f0f` (ejecución 43524364243) | **Verde**: pip-audit 13 s, gitleaks 1 s | Pestaña Actions del repositorio |
| Token en la capa bronce | Búsqueda (`grep -rli token data/bronce`) | Archivos `.meta.json` | **Sin coincidencias**: la URL guardada no lleva el token (viaja en un encabezado) | |
| Respaldo de la capa bronce | `python calidad/respaldo_bronce.py` | 2,139 archivos, 21.4 MB | **Restauración correcta**: 0 faltantes, 0 distintos | [respaldo-bronce.md](respaldo-bronce.md) |

Hallazgos abiertos: ninguno.

## Tokens con el mínimo permiso necesario

| Credencial | Para qué | Permiso | Dónde vive |
|---|---|---|---|
| `BANXICO_TOKEN` | Consultar series públicas del SIE | Solo lectura de datos públicos; no da acceso a ninguna cuenta | GitHub Secrets; se lee por variable de entorno |
| `GITHUB_TOKEN` en `ci.yml` | Clonar el repositorio | `contents: read` | Lo crea GitHub en cada ejecución y caduca al terminar |
| `GITHUB_TOKEN` en `captura.yml` | Subir datos y bitácoras | `contents: write` (el mínimo para hacer push); sin acceso a issues, paquetes ni ajustes | Igual |
| `GITHUB_TOKEN` en `respaldo.yml` | Clonar y guardar el artefacto | `contents: read` | Igual |
| INEGI | Consulta pública | No usa credencial | |

No hay tokens personales ni llaves en el repositorio.

## Respaldo de la capa bronce

Bronce es lo único que no se puede regenerar: plata y oro salen de ella. El script empaqueta `data/bronce`, lo restaura en una carpeta temporal y compara el SHA-256 de cada archivo contra el original; si uno solo no coincide, termina con error. La prueba local del 13 de noviembre restauró los 2,139 archivos sin diferencias. El flujo [respaldo.yml](../../.github/workflows/respaldo.yml) repite la prueba cada domingo y guarda el paquete como artefacto durante 90 días. **Ese flujo todavía no ha tenido su primera ejecución en GitHub.**

## Controles vigentes

| Riesgo | Control | Dónde se verifica |
|---|---|---|
| Fuga del token de Banxico | GitHub Secrets; nunca se escribe en código, bitácoras ni metadatos | `extractores/config.py`, pruebas `test_banxico_token_va_en_encabezado_y_no_se_guarda` y `test_banxico_sin_token_falla_con_mensaje_claro`, gitleaks en CI |
| Datos personales en un repositorio público | Las fuentes son estadística agregada. El contrato de plata es estricto: no admite columnas fuera del esquema | `pipeline/puerta.py` (`strict=True`) |
| Abuso de las fuentes | robots.txt, User-Agent con contacto, pausa entre peticiones y reintentos con espera | `extractores/base.py` y sus pruebas |
| Flujo automático con permisos de más | Permisos declarados por flujo (tabla anterior) | Encabezado `permissions` de cada flujo |
| Datos alterados después de la captura | SHA-256 de cada respuesta en bronce y de cada tabla de salida | `.meta.json` de bronce, `calidad/reporte-puerta.json` |
| Pérdida de la capa bronce | Respaldo con prueba de restauración | `calidad/respaldo_bronce.py` |
| Dependencia comprometida | pip-audit en CI | Trabajo `seguridad` |

## Pendiente
- Las dependencias tienen versión mínima, no exacta. Falta un archivo de versiones fijas.
- Las acciones de GitHub se referencian por etiqueta (`@v5`), no por hash de commit.
- La rama `main` no está protegida: el 13 de noviembre se reescribió su historial con un push forzado para corregir el autor de los commits. Conviene activar la protección al cerrar E1.
