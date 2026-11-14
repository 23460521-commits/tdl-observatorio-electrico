"""Respaldo de la capa bronce con prueba de restauracion.

Uso:  python calidad/respaldo_bronce.py [carpeta_destino]

La capa bronce es lo unico que no se puede regenerar (plata y oro salen de ella), asi que
es lo que se respalda. Un respaldo que nunca se ha restaurado no cuenta: el script

  1. empaqueta data/bronce en un .tar.gz con un manifiesto (ruta, bytes y SHA-256),
  2. lo restaura en una carpeta temporal,
  3. compara cada archivo restaurado contra el original (SHA-256) y
  4. escribe el resultado en calidad/seguridad/respaldo-bronce.md.

Sale con codigo 1 si un solo archivo no coincide. En GitHub Actions el paquete se guarda
como artefacto (flujo respaldo.yml): una copia fuera del arbol de Git.
"""

import hashlib
import json
import sys
import tarfile
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
BRONCE = RAIZ / "data" / "bronce"
REPORTE = RAIZ / "calidad" / "seguridad" / "respaldo-bronce.md"


def sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def manifiesto(base):
    archivos = sorted(p for p in base.rglob("*") if p.is_file())
    return {p.relative_to(base).as_posix(): {"bytes": p.stat().st_size, "sha256": sha256(p)}
            for p in archivos}  # fmt: skip


def respaldar(destino, origen=BRONCE):
    destino.mkdir(parents=True, exist_ok=True)
    original = manifiesto(origen)
    sello = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    paquete = destino / f"bronce-{sello}.tar.gz"
    with tarfile.open(paquete, "w:gz") as tar:
        tar.add(origen, arcname="bronce")
    (destino / f"bronce-{sello}.manifiesto.json").write_text(
        json.dumps(original, indent=1), encoding="utf-8"
    )
    return paquete, original


def probar_restauracion(paquete, original):
    """Restaura en una carpeta temporal y compara archivo por archivo."""
    with tempfile.TemporaryDirectory() as tmp:
        with tarfile.open(paquete) as tar:
            tar.extractall(tmp, filter="data")
        restaurado = manifiesto(Path(tmp) / "bronce")
    faltan = sorted(set(original) - set(restaurado))
    sobran = sorted(set(restaurado) - set(original))
    distintos = sorted(k for k in original if k in restaurado and original[k] != restaurado[k])
    return {"faltan": faltan, "sobran": sobran, "distintos": distintos,
            "archivos": len(restaurado)}  # fmt: skip


def main():
    destino = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "respaldos"
    t0 = time.monotonic()
    paquete, original = respaldar(destino)
    r = probar_restauracion(paquete, original)
    ok = not (r["faltan"] or r["sobran"] or r["distintos"])
    por_fuente = {}
    for ruta, info in original.items():
        f = por_fuente.setdefault(ruta.split("/")[0], [0, 0])
        f[0] += 1
        f[1] += info["bytes"]
    lineas = [
        "# Respaldo de la capa bronce: prueba de restauración",
        "",
        "Generado con `python calidad/respaldo_bronce.py`. No se edita a mano.",
        "",
        f"- Fecha de la prueba (UTC): {datetime.now(UTC):%Y-%m-%d %H:%M}",
        f"- Paquete: `{paquete.name}`, {paquete.stat().st_size / 1e6:.2f} MB, "
        f"SHA-256 `{sha256(paquete)[:16]}…`",
        f"- Archivos respaldados: {len(original)} "
        f"({sum(i['bytes'] for i in original.values()) / 1e6:.2f} MB)",
        f"- Archivos restaurados y comparados por SHA-256: {r['archivos']}",
        f"- Faltantes: {len(r['faltan'])} · sobrantes: {len(r['sobran'])} · "
        f"con contenido distinto: {len(r['distintos'])}",
        f"- Duración: {time.monotonic() - t0:.1f} s",
        f"- **Resultado: {'RESTAURACIÓN CORRECTA' if ok else 'FALLA'}**",
        "",
        "| Fuente | Archivos | MB |",
        "|---|---|---|",
        *[f"| {k} | {n} | {b / 1e6:.2f} |" for k, (n, b) in sorted(por_fuente.items())],
        "",
        "## Dónde vive cada copia",
        "",
        "| Copia | Dónde | Qué protege |",
        "|---|---|---|",
        "| 1 | Repositorio en GitHub (historial de Git) | Borrado o daño en una computadora |",
        "| 2 | Clones de los integrantes | Caída de GitHub |",
        "| 3 | Artefacto del flujo `respaldo.yml` (semanal, 90 días) | Borrado o reescritura "
        "del historial del repositorio |",
        "",
    ]
    REPORTE.write_text("\n".join(lineas), encoding="utf-8")
    print(f"{'OK' if ok else 'FALLA'}: {r['archivos']} archivos restaurados de {paquete.name}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
