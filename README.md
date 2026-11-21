# identia-python

Interfaz web local para generar reportes de noticias: pegás una lista de URLs y de cada una se extrae el **título** y el **primer párrafo** (o la bajada).

## Requisitos

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)

## Instalación

```bash
make install    # o: uv sync
```

## Uso

```bash
make run                                # levanta la interfaz web en http://127.0.0.1:8000
uv run identia-python --puerto 9000     # otro puerto
uv run identia-python --no-abrir        # no abre el navegador al iniciar
uv run identia-python -v                # muestra mensajes de depuración (-q: solo advertencias)
```

Al iniciar se abre el navegador con un formulario:

1. Pegá las URLs, una por línea. Las líneas vacías, las que empiezan con `#` y las URLs repetidas se ignoran.
2. Tocá **Generar reporte**. El reporte se muestra en la misma página, con un enlace **← Nuevo reporte** para volver al formulario.
3. Para detener el servidor, `Ctrl+C` en la terminal.

Cada reporte también se guarda en `resultados/resultado.html` (se sobrescribe).

Las noticias procesadas correctamente se guardan en `resultados/cache.json`. En los siguientes reportes, las URLs que ya están en el caché no se vuelven a descargar: se muestra lo guardado y solo se procesan las URLs nuevas (o las que fallaron antes). Para volver a procesar todo, marcá **Ignorar el caché** en el formulario o borrá el archivo.

Los mensajes se muestran en la terminal y se guardan con más detalle en `logs/identia.log`.

## Cómo funciona

Cada módulo tiene una única responsabilidad (principio S de SOLID):

| Módulo | Responsabilidad |
| --- | --- |
| `cli.py` | Interpreta los argumentos, arma las dependencias concretas (raíz de composición) y levanta el servidor. |
| `servidor.py` | Servidor web local (`http.server`): formulario en `GET /` y reporte en `POST /reporte`. |
| `pagina_formulario.py` | Genera la página del formulario. |
| `limpiar_urls.py` | Limpia la lista de URLs (vacías, comentarios, repetidas). |
| `generador.py` | Obtiene los resultados, arma el reporte HTML y lo guarda (`GeneradorConCache`). |
| `resultados.py` | Decide qué URLs salen del caché y cuáles se procesan. |
| `procesamiento.py` | Procesa las URLs en paralelo (descarga + parseo) con límite de concurrencia. |
| `descargar.py` | Descarga el HTML (sigue redirecciones, timeout de 15s, envía User-Agent). |
| `parsear.py` | Arma el `Articulo` a partir del HTML y valida que esté completo. |
| `titulo.py` | Extrae el título con extractores intercambiables (`<h1>` → `og:title` → `<title>`). |
| `primer_parrafo.py` | Extrae la bajada o el primer párrafo significativo, priorizando `<article>`, con extractores intercambiables. |
| `selectores.py` | Selectores de bajada específicos por sitio. |
| `texto_html.py` | Normaliza el texto de los elementos HTML. |
| `modelos.py` | Modelo `Articulo`. |
| `cache.py` | Guarda y lee los artículos ya procesados (`resultados/cache.json`). |
| `reporte_html.py` | Genera el contenido del reporte HTML. |
| `resumen.py` | Texto del resumen del reporte ("Procesadas X/Y…"). |
| `guardar_reporte.py` | Escribe el reporte en `resultados/resultado.html`. |
| `navegador.py` | Abre la interfaz en el navegador al iniciar. |
| `logging_config.py` | Configura el logging. |
| `exceptions.py` | `DescargaHtmlError` y `ParseoHtmlError`. |

Los sitios cuya bajada no está en un `<p>` se configuran en `SELECTORES_POR_SITIO` (`selectores.py`). Por ejemplo, Infobae usa `h2.article-subheadline` y Clarín `h2.storySummary`. Si la bajada viene como lista (`<li>`), cada ítem se devuelve en una línea.

### Extensión sin modificar código (principio O de SOLID)

Los puntos de variación están definidos como clases abstractas (`abc.ABC`). Para agregar comportamiento se crea una subclase nueva y se la registra; el código que las recorre no cambia.

| Abstracción | Implementaciones | Dónde se registra |
| --- | --- | --- |
| `ExtractorTitulo` (`titulo.py`) | `TituloDesdeH1`, `TituloDesdeOgTitle`, `TituloDesdeTitle` | `EXTRACTORES_TITULO` (en orden de prioridad) |
| `ExtractorParrafo` (`primer_parrafo.py`) | `ParrafoPorSelectorDeSitio`, `PrimerParrafoSignificativo` | `extractores_por_defecto()` |

Por ejemplo, una nueva fuente de título (`twitter:title`):

```python
from bs4 import BeautifulSoup

from identia_python.texto_html import texto_o_none
from identia_python.titulo import ExtractorTitulo


class TituloDesdeTwitter(ExtractorTitulo):
    def extraer(self, soup: BeautifulSoup) -> str | None:
        meta = soup.find("meta", attrs={"name": "twitter:title"})
        contenido = meta.get("content") if meta else None
        return texto_o_none(str(contenido)) if contenido is not None else None
```

y sumarla a `EXTRACTORES_TITULO`.

### Subclases intercambiables (principio L de SOLID)

Cualquier subclase tiene que poder reemplazar a otra sin que el código que la usa lo note. Para eso cada abstracción documenta un contrato en su docstring y todas las implementaciones lo cumplen:

| Abstracción | Acepta | Garantiza | No puede |
| --- | --- | --- | --- |
| `ExtractorTitulo.extraer(soup)` | Cualquier soup, aunque esté vacío o le falten etiquetas. | Texto no vacío y con los espacios normalizados, o `None`. | Devolver `""` ni lanzar excepciones si falta la etiqueta. |
| `ExtractorParrafo.extraer(soup, url)` | Cualquier soup y cualquier url, aunque sea de un sitio sin selector o esté mal formada. | Texto no vacío (una o más líneas, cada una normalizada), o `None`. | Devolver `""` ni lanzar excepciones si falta el elemento. |

Gracias a esto, `obtener_titulo` y `obtener_primer_parrafo` confían en el contrato (`is not None`) en lugar de defenderse de resultados raros.

Los errores propios heredan de `IdentiaError` (`DescargaHtmlError`, `ParseoHtmlError`). `procesamiento.py` atrapa `IdentiaError`, así que un error nuevo que herede de ella se maneja sin cambios.

Toda subclase nueva tiene que pasar los tests de `tests/test_contratos.py`. Para sumarla, agregala a `EXTRACTORES_TITULO` o `EXTRACTORES_PARRAFO` en ese archivo. Las implementaciones de ejemplo que usan los tests están en `tests/dobles.py`.

### Interfaces chicas por rol (principio I de SOLID)

Ningún código depende de métodos que no usa. Cada cliente pide una interfaz mínima (`typing.Protocol`) con solo lo que necesita. Como los Protocols son estructurales, cualquier objeto con esos métodos los cumple sin heredar de nada; `httpx.AsyncClient`, por ejemplo, cumple `ClienteHttp` tal como viene.

| Cliente | Depende de | En lugar de |
| --- | --- | --- |
| `descargar_html`, `procesar_url` | `ClienteHttp` (`get`) y `RespuestaHttp` (`is_success`, `status_code`, `text`) | `httpx.AsyncClient` y `httpx.Response` enteros |
| `obtener_resultados` | `LectorCache` (`cargar`) y `EscritorCache` (`actualizar`), por separado (definidos en `resultados.py`) | todas las funciones del módulo `cache` |
| `generar_html`, `texto_resumen` | `Sequence` (solo lectura) | `list` (que también permite modificarla) |

Así los dobles de prueba de `tests/dobles.py` implementan solo el rol que cumplen. Por ejemplo, con **Ignorar el caché** el caché no se lee, y `obtener_resultados` funciona con `CacheSoloEscritura`, que no tiene `cargar`.

### Dependencias invertidas (principio D de SOLID)

El código de alto nivel (las reglas: qué sale del caché, cómo se arma el reporte, cómo se atiende un pedido) no depende de los detalles (disco, red). Cada módulo de alto nivel **define** las abstracciones que necesita (`typing.Protocol`) y recibe las implementaciones concretas desde afuera. El único lugar que conoce los concretos es `cli.py` (la raíz de composición), que los crea y se los pasa.

| Alto nivel | Depende de (abstracción propia) | Implementación concreta (armada en `cli.py`) |
| --- | --- | --- |
| servidor web (`servidor.py`) | `GeneradorReporte` | `GeneradorConCache` |
| `GeneradorConCache` (`generador.py`) | `LectorCache`, `EscritorCache`, `ProcesadorUrls`, `GuardadorReporte` | `CacheJson`, `ProcesadorHttp`, `ReporteEnArchivo` |
| `obtener_resultados` (`resultados.py`) | `LectorCache`, `EscritorCache`, `ProcesadorUrls` | `CacheJson`, `ProcesadorHttp` |
| `ProcesadorHttp` (`procesamiento.py`) | una fábrica de `ClienteHttp` | `crear_cliente` (httpx) |

La flecha de dependencia apunta hacia las abstracciones: `CacheJson` y `ReporteEnArchivo` cumplen los Protocols sin importarlos, y `servidor.py`, `generador.py` y `resultados.py` no importan ningún módulo de detalle (lo verifica `tests/test_dependencias.py`).

Así se puede cambiar un detalle sin tocar las reglas (p. ej. un caché en SQLite, o guardar el reporte en S3) y los tests reemplazan red, disco y procesamiento pasando dobles (`ProcesadorFalso`, `CacheEnMemoria`, `GuardadorEnMemoria`, `GeneradorFalso`, en `tests/dobles.py`) en lugar de usar `monkeypatch`:

```python
from identia_python.generador import GeneradorConCache

cache = CacheEnMemoria()
generador = GeneradorConCache(
    lector=cache,
    escritor=cache,
    procesador=ProcesadorFalso(),
    guardador=GuardadorEnMemoria(),
)
html = generador.generar(urls, forzar=False)
```

## Desarrollo

```bash
make test               # tests (o: uv run pytest)
uv run ruff check .     # lint
uv run ruff format .    # formato
uv run mypy             # tipos
```
