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
uv run identia-python --forzar     # ignora el caché y vuelve a procesar todo
```

Además de la salida por consola, cada ejecución guarda el resultado en `resultados/resultado.html` (se sobrescribe) y lo abre automáticamente en el navegador predeterminado.

Las noticias procesadas correctamente se guardan en `resultados/cache.json`. En las siguientes ejecuciones, las URLs que ya están en el caché no se vuelven a descargar: se muestra lo guardado y solo se procesan las URLs nuevas (o las que fallaron antes). Para volver a procesar todo, usá `--forzar` o borrá el archivo.

Ejemplo de salida:

```
[1/3] https://www.infobae.com/economia/...
  Título: ...
  Primer párrafo: ...

Procesadas 3/3 noticias correctamente.
```

## Cómo funciona

Cada módulo tiene una única responsabilidad (principio S de SOLID):

| Módulo | Responsabilidad |
| --- | --- |
| `cli.py` | Interpreta los argumentos y coordina los pasos. |
| `leer_urls.py` | Lee y limpia la lista de URLs. |
| `resultados.py` | Decide qué URLs salen del caché y cuáles se procesan. |
| `procesamiento.py` | Procesa las URLs en paralelo (descarga + parseo) con límite de concurrencia. |
| `descargar.py` | Descarga el HTML (sigue redirecciones, timeout de 15s, envía User-Agent). |
| `parsear.py` | Arma el `Articulo` a partir del HTML y valida que esté completo. |
| `titulo.py` | Extrae el título con extractores intercambiables (`<h1>` → `og:title` → `<title>`). |
| `primer_parrafo.py` | Extrae la bajada o el primer párrafo significativo, priorizando `<article>`, con extractores intercambiables. |
| `salidas.py` | Destinos de los resultados (`SalidaConsola`, `SalidaHtml`). |
| `selectores.py` | Selectores de bajada específicos por sitio. |
| `texto_html.py` | Normaliza el texto de los elementos HTML. |
| `modelos.py` | Modelo `Articulo`. |
| `cache.py` | Guarda y lee los artículos ya procesados (`resultados/cache.json`). |
| `salida_consola.py` | Imprime los resultados por consola. |
| `reporte_html.py` | Genera el contenido del reporte HTML. |
| `guardar_reporte.py` | Escribe el reporte en `resultados/resultado.html`. |
| `navegador.py` | Abre el reporte en el navegador. |
| `resumen.py` | Texto del resumen ("Procesadas X/Y…"), compartido por consola y HTML. |
| `logging_config.py` | Configura el logging. |
| `exceptions.py` | `DescargaHtmlError` y `ParseoHtmlError`. |

Los sitios cuya bajada no está en un `<p>` se configuran en `SELECTORES_POR_SITIO` (`selectores.py`). Por ejemplo, Infobae usa `h2.article-subheadline` y Clarín `h2.storySummary`. Si la bajada viene como lista (`<li>`), cada ítem se devuelve en una línea.

### Extensión sin modificar código (principio O de SOLID)

Los puntos de variación están definidos como clases abstractas (`abc.ABC`). Para agregar comportamiento se crea una subclase nueva y se la registra; el código que las recorre no cambia.

| Abstracción | Implementaciones | Dónde se registra |
| --- | --- | --- |
| `ExtractorTitulo` (`titulo.py`) | `TituloDesdeH1`, `TituloDesdeOgTitle`, `TituloDesdeTitle` | `EXTRACTORES_TITULO` (en orden de prioridad) |
| `ExtractorParrafo` (`primer_parrafo.py`) | `ParrafoPorSelectorDeSitio`, `PrimerParrafoSignificativo` | `extractores_por_defecto()` |
| `Salida` (`salidas.py`) | `SalidaConsola`, `SalidaHtml` | `_crear_salidas()` en `cli.py` |

Por ejemplo, para exportar los resultados a JSON:

```python
import json
from pathlib import Path

from identia_python.salidas import Salida


class SalidaJson(Salida):
    def __init__(self, archivo: Path) -> None:
        self.archivo = archivo

    def emitir(self, urls, resultados) -> None:
        datos = {
            url: vars(articulo) if articulo else None
            for url, articulo in zip(urls, resultados, strict=True)
        }
        self.archivo.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
```

y sumar `SalidaJson(Path("resultados/resultado.json"))` a la lista de `_crear_salidas()`. Del mismo modo, una nueva fuente de título (p. ej. `twitter:title`) es una subclase de `ExtractorTitulo` agregada a `EXTRACTORES_TITULO`.

## Desarrollo

```bash
uv run pytest           # tests
uv run ruff check .     # lint
uv run ruff format .    # formato
uv run mypy             # tipos
```
