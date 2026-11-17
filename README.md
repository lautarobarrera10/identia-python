# identia-python

Descarga noticias a partir de una lista de URLs y extrae de cada una el **título** y el **primer párrafo** (o la bajada).

## Requisitos

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)

## Instalación

```bash
uv sync
```

## Uso

Agregá las URLs en `urls.txt`, una por línea. Las líneas vacías, las que empiezan con `#` y las URLs repetidas se ignoran.

```bash
uv run identia-python              # lee ./urls.txt
uv run identia-python otro.txt     # lee otro archivo
uv run python -m identia_python    # equivalente
uv run identia-python --no-abrir   # genera el HTML sin abrir el navegador
```

Además de la salida por consola, cada ejecución guarda el resultado en `resultados/resultado.html` (se sobrescribe) y lo abre automáticamente en el navegador predeterminado.

Ejemplo de salida:

```
[1/3] https://www.infobae.com/economia/...
  Título: ...
  Primer párrafo: ...

Procesadas 3/3 noticias correctamente.
```

## Cómo funciona

| Módulo | Responsabilidad |
| --- | --- |
| `leer_urls.py` | Lee y limpia la lista de URLs. |
| `descargar.py` | Descarga el HTML (sigue redirecciones, timeout de 15s, envía User-Agent). |
| `parsear.py` | Extrae el título (`<h1>` → `og:title` → `<title>`) y el primer párrafo significativo, priorizando `<article>`. |
| `reporte_html.py` | Genera el reporte HTML, lo guarda y lo abre en el navegador. |
| `cli.py` | Punto de entrada de la línea de comandos. |
| `exceptions.py` | `DescargaHtmlError` y `ParseoHtmlError`. |

Los sitios cuya bajada no está en un `<p>` se configuran en `SELECTORES_POR_SITIO` (`parsear.py`). Por ejemplo, Infobae usa `h2.article-subheadline` y Clarín `h2.storySummary`. Si la bajada viene como lista (`<li>`), cada ítem se devuelve en una línea.

## Desarrollo

```bash
uv run pytest           # tests
uv run ruff check .     # lint
uv run ruff format .    # formato
uv run mypy             # tipos
```
