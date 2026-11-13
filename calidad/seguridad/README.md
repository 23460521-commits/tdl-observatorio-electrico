# Seguridad: resultados de E1

Revisión del 13 de noviembre de 2026 sobre el commit de la entrega. Los reportes en JSON de esta carpeta son la salida original de cada herramienta.

## Resultados

| Revisión | Herramienta | Alcance | Resultado | Evidencia |
|---|---|---|---|---|
| Secretos en el historial | gitleaks 8.24.3 (`gitleaks git`) | Los 12 commits del repositorio, 27 MB | **0 hallazgos** | [gitleaks-historial.json](gitleaks-historial.json) |
| Secretos en los archivos actuales | gitleaks 8.24.3 (`gitleaks dir`) | Todo el árbol de trabajo, incluidos los datos de bronce | **0 hallazgos** | [gitleaks-archivos.json](gitleaks-archivos.json) |
| Dependencias vulnerables | pip-audit 2.10.1 | `requirements.txt` y sus dependencias transitivas (29 paquetes) | **0 vulnerabilidades conocidas** | [pip-audit.json](pip-audit.json) |
| Token en la capa bronce | Búsqueda manual (`grep -rli token data/bronce`) | Archivos `.meta.json` | **Sin coincidencias**: la URL guardada no lleva el token (viaja en un encabezado) | |

Las dos herramientas quedaron además en el flujo de CI (trabajo `seguridad` de [ci.yml](../../.github/workflows/ci.yml)): si aparece un secreto o una dependencia vulnerable, el cambio queda en rojo.

## Controles vigentes

| Riesgo | Control | Dónde se verifica |
|---|---|---|
| Fuga del token de Banxico | Vive en GitHub Secrets (`BANXICO_TOKEN`); se lee por variable de entorno y nunca se escribe en código, bitácoras ni metadatos | `extractores/config.py`, pruebas `test_banxico_token_va_en_encabezado_y_no_se_guarda` y `test_banxico_sin_token_falla_con_mensaje_claro`, gitleaks en CI |
| Datos personales en un repositorio público | Las fuentes son estadística agregada (índices por ciudad, tipo de cambio). El contrato de plata es estricto: no admite columnas fuera del esquema | `pipeline/puerta.py` (`strict=True`) |
| Abuso de las fuentes | robots.txt, User-Agent con contacto, pausa mínima entre peticiones y reintentos con espera | `extractores/base.py` y sus pruebas |
| Flujo automático con permisos de más | `ci.yml` solo lectura (`contents: read`); `captura.yml` escribe únicamente datos y bitácoras | Encabezado `permissions` de cada flujo |
| Datos alterados después de la captura | SHA-256 de cada respuesta en bronce y de cada tabla de salida | `.meta.json` de bronce, `calidad/reporte-puerta.json` |
| Dependencia comprometida | pip-audit en CI | Trabajo `seguridad` |

## Pendiente
- Las dependencias tienen versión mínima, no exacta. Falta un archivo de versiones fijas para que la instalación sea idéntica en cada corrida.
- Las acciones de GitHub se referencian por etiqueta (`@v5`), no por hash de commit.
- No hay protección de la rama `main` (cualquiera con permiso de escritura sube sin revisión).
