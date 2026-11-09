"""Pruebas sin red: una sesion falsa reemplaza a internet."""
import csv
import gzip
import hashlib
import json
from datetime import date

import pytest
import requests

from extractores import bronce, cenace, open_meteo
from extractores.base import ExtractorEtico


class Respuesta:
    def __init__(self, status=200, contenido=b"", url=""):
        self.status_code = status
        self.content = contenido
        self.text = contenido.decode()
        self.url = url

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class SesionFalsa:
    """Responde segun el final de la URL; registra lo que se pidio."""

    def __init__(self, rutas):
        self.rutas = rutas
        self.headers = {}
        self.pedidas = []

    def get(self, url, params=None, timeout=None):
        self.pedidas.append(url)
        for sufijo, resp in self.rutas.items():
            if url.endswith(sufijo) or sufijo in url:
                if isinstance(resp, Exception):
                    raise resp
                return resp
        return Respuesta(404)


@pytest.fixture(autouse=True)
def sin_esperas(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)


PAYLOAD_CENACE = {
    "status": "OK",
    "Resultados": [
        {"zona_carga": "GUADALAJARA", "Valores": [
            {"fecha": "2026-11-01", "hora": "1", "pz": "1500.1"},
            {"fecha": "2026-11-01", "hora": "2", "pz": "1480.0"},
        ]},
        {"zona_carga": "COLIMA", "Valores": [
            {"fecha": "2026-11-01", "hora": "1", "pz": "1510.3"},
        ]},
    ],
}


# --- Extractor etico -------------------------------------------------------------
def test_sin_robots_txt_permite():
    s = SesionFalsa({"/robots.txt": Respuesta(404), "/datos": Respuesta(200, b"{}")})
    r = ExtractorEtico(pausa=0, sesion=s).get("https://sitio.mx/datos")
    assert r.status_code == 200


def test_robots_que_prohibe_bloquea():
    robots = Respuesta(200, b"User-agent: *\nDisallow: /privado\n")
    s = SesionFalsa({"/robots.txt": robots})
    with pytest.raises(PermissionError):
        ExtractorEtico(pausa=0, sesion=s).get("https://sitio.mx/privado/x")


def test_robots_403_bloquea_todo():
    s = SesionFalsa({"/robots.txt": Respuesta(403)})
    with pytest.raises(PermissionError):
        ExtractorEtico(pausa=0, sesion=s).get("https://sitio.mx/datos")


def test_robots_con_error_de_servidor_no_supone_permiso():
    s = SesionFalsa({"/robots.txt": Respuesta(503)})
    with pytest.raises(RuntimeError):
        ExtractorEtico(pausa=0, sesion=s).get("https://sitio.mx/datos")


def test_reintenta_ante_saturacion_y_reporta_intentos():
    s = SesionFalsa({"/robots.txt": Respuesta(404), "/datos": Respuesta(429)})
    ex = ExtractorEtico(pausa=0, sesion=s)
    with pytest.raises(RuntimeError, match="3 intentos"):
        ex.get("https://sitio.mx/datos")
    assert ex.ultimos_intentos == 3
    assert s.pedidas.count("https://sitio.mx/datos") == 3


def test_reintenta_errores_de_red():
    s = SesionFalsa({"/robots.txt": Respuesta(404), "/datos": requests.ConnectionError("caida")})
    with pytest.raises(RuntimeError, match="ConnectionError"):
        ExtractorEtico(pausa=0, sesion=s).get("https://sitio.mx/datos")


def test_se_identifica_con_user_agent():
    s = SesionFalsa({})
    ExtractorEtico(pausa=0, sesion=s)
    assert "TDL-ObservatorioElectricoColima" in s.headers["User-Agent"]


# --- CENACE ------------------------------------------------------------------------
def test_url_pend_formato():
    url = cenace.url_pend(["VDM CENTRO", "colima"], date(2026, 11, 1), date(2026, 11, 7))
    assert url.endswith("/SWPEND/SIM/SIN/MDA/VDM-CENTRO,COLIMA/2026/11/01/2026/11/07/JSON")


def test_url_pend_respeta_limites():
    with pytest.raises(ValueError):
        cenace.url_pend(["A"], date(2026, 11, 1), date(2026, 11, 8))  # 8 dias
    with pytest.raises(ValueError):
        cenace.url_pend([f"Z{i}" for i in range(11)], date(2026, 11, 1), date(2026, 11, 1))


def test_rangos_cubren_todo_sin_traslape():
    bloques = list(cenace.rangos(date(2026, 1, 1), date(2026, 1, 20)))
    assert bloques[0] == (date(2026, 1, 1), date(2026, 1, 7))
    assert bloques[-1] == (date(2026, 1, 15), date(2026, 1, 20))
    dias = sum((b - a).days + 1 for a, b in bloques)
    assert dias == 20


def test_resumir_payload():
    res = cenace.resumir(PAYLOAD_CENACE)
    assert res["valores"] == 3
    assert res["zonas"] == ["GUADALAJARA", "COLIMA"]
    assert res["fechas"] == ["2026-11-01"]


def test_capturar_guarda_en_bronce(tmp_path):
    contenido = json.dumps(PAYLOAD_CENACE).encode()
    s = SesionFalsa({"/robots.txt": Respuesta(404), "/JSON": Respuesta(200, contenido)})
    ex = ExtractorEtico(pausa=0, sesion=s)
    ruta, res = cenace.capturar(
        ex, ["GUADALAJARA", "COLIMA"], date(2026, 11, 1), date(2026, 11, 1),
        "prueba", "bloque", base=tmp_path,
    )
    assert res["valores"] == 3
    assert gzip.decompress(ruta.read_bytes()) == contenido
    meta = json.loads(ruta.with_name("bloque.meta.json").read_text())
    assert meta["sha256"] == hashlib.sha256(contenido).hexdigest()
    assert meta["zonas_solicitadas"] == ["GUADALAJARA", "COLIMA"]


def test_respuesta_vacia_se_guarda_pero_falla(tmp_path):
    contenido = json.dumps({"status": "ZERO RESULTS", "Resultados": []}).encode()
    s = SesionFalsa({"/robots.txt": Respuesta(404), "/JSON": Respuesta(200, contenido)})
    ex = ExtractorEtico(pausa=0, sesion=s)
    with pytest.raises(ValueError, match="sin valores"):
        cenace.capturar(ex, ["COLIMA"], date(2026, 11, 1), date(2026, 11, 1),
                        "prueba", "vacio", base=tmp_path)
    assert (tmp_path / cenace.FUENTE / "prueba" / "vacio.json.gz").exists()


# --- Open-Meteo y bitacora -----------------------------------------------------------
def test_resumir_open_meteo_multiples_ubicaciones():
    payload = [{"hourly": {"time": ["a", "b"]}}, {"hourly": {"time": ["a", "b"]}}]
    assert open_meteo.resumir(payload) == {"ubicaciones": 2, "valores": 4}


def test_bitacora_escribe_encabezado_una_vez(tmp_path):
    archivo = tmp_path / "bitacora.csv"
    bronce.registrar({"fuente": "a", "estado": "exito"}, archivo)
    bronce.registrar({"fuente": "b", "estado": "fallo"}, archivo)
    filas = list(csv.DictReader(archivo.open()))
    assert [f["estado"] for f in filas] == ["exito", "fallo"]


def test_gzip_reproducible(tmp_path):
    r1 = bronce.guardar("x", b"hola", {}, "a", "n1", base=tmp_path)
    r2 = bronce.guardar("x", b"hola", {}, "a", "n2", base=tmp_path)
    assert r1.read_bytes() == r2.read_bytes()


def test_204_sin_contenido_se_reporta_claro(tmp_path):
    s = SesionFalsa({"/robots.txt": Respuesta(404), "/JSON": Respuesta(204, b"")})
    ex = ExtractorEtico(pausa=0, sesion=s)
    with pytest.raises(ValueError, match="sin contenido"):
        cenace.capturar(ex, ["COLIMA"], date(2026, 11, 9), date(2026, 11, 9),
                        "prueba", "manana", base=tmp_path)
