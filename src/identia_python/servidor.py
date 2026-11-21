"""
Servidor web local con el formulario para generar reportes.

Es código de alto nivel: atiende los pedidos HTTP pero no sabe cómo se
obtienen las noticias ni dónde se guarda el reporte. Depende solo de
GeneradorReporte, definido acá; la implementación concreta la arma el cli
(principio de inversión de dependencias).
"""

import logging
from collections.abc import Sequence
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Protocol
from urllib.parse import parse_qs, urlsplit

from identia_python.limpiar_urls import limpiar_urls
from identia_python.pagina_formulario import RUTA_REPORTE, generar_formulario

logger = logging.getLogger(__name__)

# Evita leer cuerpos enormes: un formulario con miles de urls entra de sobra
MAX_BYTES_FORMULARIO = 1_000_000


class GeneradorReporte(Protocol):
    def generar(self, urls: Sequence[str], forzar: bool) -> str:
        """Procesa las urls y devuelve el reporte HTML."""
        ...


def crear_handler(generador: GeneradorReporte) -> type[BaseHTTPRequestHandler]:
    """Crea la clase que atiende los pedidos usando el generador recibido."""

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # nombre impuesto por http.server
            if urlsplit(self.path).path == "/":
                self._responder(HTTPStatus.OK, generar_formulario())
            else:
                self._no_encontrado()

        def do_POST(self) -> None:
            if urlsplit(self.path).path != RUTA_REPORTE:
                self._no_encontrado()
                return

            largo = int(self.headers.get("Content-Length") or 0)
            if largo > MAX_BYTES_FORMULARIO:
                self._responder(
                    HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                    generar_formulario("El formulario es demasiado grande."),
                )
                return

            cuerpo = self.rfile.read(largo).decode("utf-8", errors="replace")
            campos = parse_qs(cuerpo)
            texto = campos.get("urls", [""])[0]
            forzar = "forzar" in campos
            urls = limpiar_urls(texto)
            if not urls:
                self._responder(
                    HTTPStatus.BAD_REQUEST,
                    generar_formulario("No se encontraron urls.", texto),
                )
                return

            logger.info("Generando reporte de %d urls", len(urls))
            self._responder(HTTPStatus.OK, generador.generar(urls, forzar))

        def _no_encontrado(self) -> None:
            self._responder(HTTPStatus.NOT_FOUND, "<h1>Página no encontrada</h1>")

        def _responder(self, estado: HTTPStatus, html: str) -> None:
            contenido = html.encode("utf-8")
            self.send_response(estado)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(contenido)))
            self.end_headers()
            self.wfile.write(contenido)

        def log_message(self, format: str, *args: Any) -> None:
            # Los accesos van al log del paquete (archivo) y no a stderr
            logger.debug("%s - %s", self.address_string(), format % args)

    return Handler


def crear_servidor(
    host: str, puerto: int, generador: GeneradorReporte
) -> ThreadingHTTPServer:
    """Crea el servidor (cada pedido se atiende en su propio thread)."""
    return ThreadingHTTPServer((host, puerto), crear_handler(generador))
