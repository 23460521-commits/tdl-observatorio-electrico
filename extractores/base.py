"""Extractor etico: respeta robots.txt, se identifica y no satura sitios.

Parte del codigo base del Kit de arranque TDL, con estos cambios:
1. robots.txt se descarga con requests y con timeout. urllib.robotparser.read()
   no tiene timeout y puede dejar colgada la captura programada.
2. Si robots.txt responde 401/403 se bloquea todo; otro 4xx (no existe) permite,
   igual que la regla de la biblioteca estandar. Un 5xx o un error de red detiene
   la captura en lugar de suponer permiso.
3. Los errores de red tambien se reintentan con espera exponencial.
4. Acepta parametros de consulta y encabezados (para APIs con token, como Banxico).
   El token va en un encabezado para que nunca quede en la URL ni en los metadatos.
"""
import time
import urllib.robotparser
from urllib.parse import urlparse

import requests

from extractores.config import USER_AGENT


class ExtractorEtico:
    def __init__(self, pausa=1.5, timeout=30, sesion=None, user_agent=USER_AGENT):
        self.pausa = pausa  # segundos minimos entre peticiones al mismo dominio
        self.timeout = timeout
        self.user_agent = user_agent
        self.robots = {}
        self.ultimo = {}
        self.ultimos_intentos = 0
        self.sesion = sesion or requests.Session()
        self.sesion.headers["User-Agent"] = user_agent

    def _esperar(self, dominio, pausa):
        espera = pausa - (time.time() - self.ultimo.get(dominio, 0))
        if espera > 0:
            time.sleep(espera)

    def _reglas(self, url):
        p = urlparse(url)
        base = f"{p.scheme}://{p.netloc}"
        if base not in self.robots:
            rp = urllib.robotparser.RobotFileParser(base + "/robots.txt")
            self._esperar(p.netloc, self.pausa)
            r = self.sesion.get(base + "/robots.txt", timeout=self.timeout)
            self.ultimo[p.netloc] = time.time()
            if r.status_code in (401, 403):
                rp.disallow_all = True
            elif 400 <= r.status_code < 500:
                rp.allow_all = True
            elif r.status_code == 200:
                rp.parse(r.text.splitlines())
            else:
                raise RuntimeError(
                    f"No se pudo leer {base}/robots.txt (HTTP {r.status_code}); "
                    "no se captura sin conocer las reglas"
                )
            self.robots[base] = rp
        return self.robots[base]

    def get(self, url, params=None, headers=None, intentos=3):
        reglas = self._reglas(url)
        if not reglas.can_fetch(self.user_agent, url):
            raise PermissionError(f"robots.txt no permite {url}")
        dominio = urlparse(url).netloc
        pausa = max(self.pausa, reglas.crawl_delay(self.user_agent) or 0)
        ultimo_error = None
        for i in range(intentos):
            self.ultimos_intentos = i + 1
            self._esperar(dominio, pausa)
            try:
                r = self.sesion.get(url, params=params, headers=headers, timeout=self.timeout)
            except (requests.ConnectionError, requests.Timeout) as e:
                self.ultimo[dominio] = time.time()
                ultimo_error = f"{type(e).__name__}: {e}"
                time.sleep(pausa * 2**i)  # espera exponencial ante fallas de red
                continue
            self.ultimo[dominio] = time.time()
            if r.status_code == 429 or r.status_code >= 500:
                ultimo_error = f"HTTP {r.status_code}"
                time.sleep(pausa * 2**i)  # espera exponencial ante saturacion
                continue
            r.raise_for_status()
            return r
        raise RuntimeError(
            f"Sin respuesta valida de {url} tras {intentos} intentos ({ultimo_error})"
        )
