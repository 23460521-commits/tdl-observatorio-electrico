"""Fuente 1: precios de energia por zona de carga de CENACE (servicio web SW-PEND).

Referencia: Manual Tecnico SW-PEND de CENACE (version 2022-06-24).
Formato del servicio:
  {base}/SWPEND/SIM/{sistema}/{proceso}/{zona1,zona2,...}/{aaaa/mm/dd}/{aaaa/mm/dd}/JSON
Limites: 1 a 7 dias y 1 a 10 zonas por peticion; zonas separadas por coma sin
espacios, y los espacios del nombre van como guiones (LOS CABOS -> LOS-CABOS).
Campos de cada valor: fecha, hora, pz (precio), pz_ene, pz_per y pz_cng
(componentes de energia, perdidas y congestion), en $/MWh.

La respuesta se guarda cruda en bronce. Aqui solo se resume (cuantas zonas,
cuantos valores, que fechas) para validar la captura y llenar la bitacora;
el desanidado a tabla se hace en la capa plata.
"""
import json
from datetime import timedelta

from extractores import bronce, config

FUENTE = "cenace_pend"


def url_pend(zonas, inicio, fin, sistema=None, proceso=None):
    if not 1 <= len(zonas) <= config.CENACE_MAX_ZONAS:
        raise ValueError(f"Se piden entre 1 y {config.CENACE_MAX_ZONAS} zonas por peticion")
    dias = (fin - inicio).days + 1
    if not 1 <= dias <= config.CENACE_MAX_DIAS:
        raise ValueError(f"El rango debe tener entre 1 y {config.CENACE_MAX_DIAS} dias")
    lista = ",".join(z.strip().upper().replace(" ", "-") for z in zonas)
    return (
        f"{config.CENACE_BASE}/SWPEND/SIM/{sistema or config.CENACE_SISTEMA}/"
        f"{proceso or config.CENACE_PROCESO}/{lista}/"
        f"{inicio:%Y/%m/%d}/{fin:%Y/%m/%d}/JSON"
    )


def _clave(d, nombre):
    """Busca una clave sin importar mayusculas (el JSON de CENACE no es uniforme)."""
    if not isinstance(d, dict):
        return None
    for k, v in d.items():
        if k.lower() == nombre:
            return v
    return None


def resumir(payload):
    resultados = _clave(payload, "resultados") or []
    total, fechas, zonas = 0, set(), []
    for res in resultados:
        valores = _clave(res, "valores") or []
        total += len(valores)
        zona = _clave(res, "zona_carga") or _clave(res, "clv_nodo")
        if zona:
            zonas.append(zona)
        for v in valores:
            f = _clave(v, "fecha")
            if f:
                fechas.add(f)
    return {
        "status": _clave(payload, "status"),
        "zonas": zonas,
        "n_resultados": len(resultados),
        "valores": total,
        "fechas": sorted(fechas),
    }


def rangos(inicio, fin, max_dias=None):
    """Parte [inicio, fin] en bloques de a lo mucho max_dias dias."""
    max_dias = max_dias or config.CENACE_MAX_DIAS
    a = inicio
    while a <= fin:
        b = min(a + timedelta(days=max_dias - 1), fin)
        yield a, b
        a = b + timedelta(days=1)


def grupos(zonas, tam=None):
    tam = tam or config.CENACE_MAX_ZONAS
    for i in range(0, len(zonas), tam):
        yield zonas[i:i + tam]


def cargar_zonas(archivo=None):
    archivo = archivo or config.ARCHIVO_ZONAS
    if not archivo.exists():
        raise FileNotFoundError(
            f"No existe {archivo.name}. Corre primero: python -m extractores.descubrir_zonas"
        )
    zonas = json.loads(archivo.read_text(encoding="utf-8"))["zonas"]
    if not zonas:
        raise ValueError(f"{archivo.name} no tiene zonas confirmadas")
    return zonas


def capturar(extractor, zonas, inicio, fin, subruta, nombre, base=None):
    """Descarga un bloque, lo guarda en bronce aunque venga mal y valida despues.

    Guardar primero es a proposito: una respuesta de error tambien es evidencia.
    """
    url = url_pend(zonas, inicio, fin)
    capturado = bronce.ahora_utc()
    r = extractor.get(url)
    meta = {
        "url": url,
        "http_status": r.status_code,
        "capturado_utc": capturado.isoformat(),
        "zonas_solicitadas": list(zonas),
        "fecha_inicio": inicio.isoformat(),
        "fecha_fin": fin.isoformat(),
        "sistema": config.CENACE_SISTEMA,
        "proceso": config.CENACE_PROCESO,
        "intentos": extractor.ultimos_intentos,
    }
    ruta = bronce.guardar(FUENTE, r.content, meta, subruta, nombre, base=base)
    if r.status_code == 204 or not r.content.strip():
        # El manual de CENACE define 204 No Content: la peticion es valida pero no hay datos
        raise ValueError(f"HTTP {r.status_code} sin contenido: CENACE no tiene datos publicados")
    try:
        payload = json.loads(r.content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Respuesta no es JSON ({ruta.name}): {e}") from e
    resumen = resumir(payload)
    if resumen["valores"] == 0:
        raise ValueError(
            f"Respuesta sin valores (status={resumen['status']}); guardada en {ruta.name}"
        )
    return ruta, resumen
