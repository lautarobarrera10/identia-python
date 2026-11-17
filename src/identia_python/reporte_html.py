"""
Generación del reporte HTML con los resultados y apertura en el navegador.
"""

import logging
import webbrowser
from datetime import datetime
from html import escape
from pathlib import Path

from identia_python.parsear import Articulo

ARCHIVO_HTML = Path("resultados/resultado.html")

logger = logging.getLogger(__name__)

ESTILOS = """
:root {
  --fondo: #f6f7f9; --tarjeta: #ffffff; --texto: #1d2330; --suave: #5b6475;
  --borde: #e2e5ea; --link: #1a5fb4; --error: #b42318; --error-fondo: #fdecea;
}
@media (prefers-color-scheme: dark) {
  :root {
    --fondo: #14171c; --tarjeta: #1d2128; --texto: #e6e8eb; --suave: #9aa3b2;
    --borde: #2c323c; --link: #78aeff; --error: #ff8a80; --error-fondo: #3a1f1f;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; padding: 32px 16px; background: var(--fondo); color: var(--texto);
  font: 16px/1.55 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}
main { max-width: 820px; margin: 0 auto; }
h1 { margin: 0 0 4px; font-size: 1.6rem; }
.meta { color: var(--suave); margin: 0 0 24px; }
article {
  background: var(--tarjeta); border: 1px solid var(--borde); border-radius: 10px;
  padding: 18px 20px; margin-bottom: 16px;
}
article.error { background: var(--error-fondo); }
.numero { color: var(--suave); font-size: .85rem; }
h2 { margin: 4px 0 8px; font-size: 1.2rem; line-height: 1.3; }
a.url { color: var(--link); font-size: .85rem; word-break: break-all; }
p { margin: 10px 0 0; }
.fallo { color: var(--error); font-weight: 600; }
"""


def _tarjeta(i: int, url: str, articulo: Articulo | None) -> str:
    enlace = f'<a class="url" href="{escape(url)}" target="_blank">{escape(url)}</a>'
    if articulo is None:
        return (
            f'<article class="error"><div class="numero">#{i}</div>{enlace}'
            '<p class="fallo">No se pudo procesar esta noticia.</p></article>'
        )
    parrafo = "<br>".join(
        escape(linea) for linea in articulo.primer_parrafo.split("\n")
    )
    return (
        f'<article><div class="numero">#{i}</div>'
        f"<h2>{escape(articulo.titulo)}</h2>{enlace}<p>{parrafo}</p></article>"
    )


def generar_html(urls: list[str], resultados: list[Articulo | None]) -> str:
    """Arma una página HTML autocontenida con un resultado por url, en orden."""
    ok = len(urls) - resultados.count(None)
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    resumen = f"Procesadas {ok}/{len(urls)} noticias correctamente."
    tarjetas = "\n".join(
        _tarjeta(i, url, articulo)
        for i, (url, articulo) in enumerate(zip(urls, resultados, strict=True), 1)
    )
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Resultados identia-python</title>
<style>{ESTILOS}</style>
</head>
<body>
<main>
<h1>Resultados</h1>
<p class="meta">Generado el {fecha} · {resumen}</p>
{tarjetas}
</main>
</body>
</html>
"""


def guardar_html(contenido: str, archivo: Path | None = None) -> Path:
    """Escribe el HTML (por defecto en ARCHIVO_HTML) y devuelve la ruta absoluta."""
    destino = (archivo or ARCHIVO_HTML).resolve()
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(contenido, encoding="utf-8")
    return destino


def abrir_en_navegador(ruta: Path) -> None:
    """Abre el archivo en el navegador predeterminado."""
    if not webbrowser.open(ruta.resolve().as_uri()):
        logger.warning("No se pudo abrir el navegador. Abrí manualmente: %s", ruta)
