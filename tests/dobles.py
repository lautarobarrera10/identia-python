"""
Implementaciones de prueba de las abstracciones del paquete. Muestran que se
pueden agregar subclases sin modificar el paquete (Open/Closed) y, como también
pasan los tests de contrato, que son intercambiables con las de producción
(Liskov).
"""

from bs4 import BeautifulSoup

from identia_python.modelos import Articulo
from identia_python.primer_parrafo import ExtractorParrafo
from identia_python.salidas import Salida
from identia_python.texto_html import texto_o_none
from identia_python.titulo import ExtractorTitulo


class TituloDesdeTwitter(ExtractorTitulo):
    """Fuente nueva agregada sin modificar titulo.py."""

    def extraer(self, soup: BeautifulSoup) -> str | None:
        meta = soup.find("meta", attrs={"name": "twitter:title"})
        contenido = meta.get("content") if meta else None
        return texto_o_none(str(contenido)) if contenido is not None else None


class ParrafoDesdeResumen(ExtractorParrafo):
    """Estrategia nueva agregada sin modificar primer_parrafo.py."""

    def extraer(self, soup: BeautifulSoup, url: str) -> str | None:
        div = soup.find("div", class_="resumen")
        return texto_o_none(div.get_text()) if div else None


class SalidaEnMemoria(Salida):
    """Salida nueva agregada sin modificar salidas.py."""

    def __init__(self) -> None:
        self.recibido: list[tuple[list[str], list[Articulo | None]]] = []

    def emitir(self, urls: list[str], resultados: list[Articulo | None]) -> None:
        # Guarda copias: el contrato prohíbe depender de las listas recibidas
        self.recibido.append((list(urls), list(resultados)))
