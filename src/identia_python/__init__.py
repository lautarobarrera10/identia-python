import sys
from pathlib import Path

from .exception import DescargaHtmlError, ParseoHtmlError
from .utils.descargar import descargar_html
from .utils.leer_urls import leer_urls
from .utils.parsear import parsear_articulo

ARCHIVO_URLS = "urls.txt"


def main() -> None:
    # Por defecto lee urls.txt en la raíz del proyecto (directorio desde donde se ejecuta);
    # opcionalmente se puede pasar otra ruta: `identia-python otro_archivo.txt`
    ruta = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd() / ARCHIVO_URLS

    if not ruta.is_file():
        print(f"No se encontró el archivo de urls: {ruta}", file=sys.stderr)
        sys.exit(1)

    urls = leer_urls(ruta)
    if not urls:
        print(f"El archivo {ruta} no contiene urls.", file=sys.stderr)
        sys.exit(1)

    errores = 0
    for i, url in enumerate(urls, start=1):
        print(f"[{i}/{len(urls)}] {url}")
        try:
            html = descargar_html(url)
            articulo = parsear_articulo(html, url)
        except (DescargaHtmlError, ParseoHtmlError) as e:
            errores += 1
            print(f"  Error: {e}\n")
            continue
        except Exception as e:  # p. ej. errores de red de httpx o url inválida
            errores += 1
            print(f"  Error inesperado: {type(e).__name__}: {e}\n")
            continue

        print("  Título:", articulo.titulo)
        print("  Primer párrafo:", articulo.primer_parrafo, "\n")

    print(f"Procesadas {len(urls) - errores}/{len(urls)} noticias correctamente.")
