"""
Implementaciones de prueba de las abstracciones del paquete. Muestran que se
pueden agregar subclases sin modificar el paquete (Open/Closed) y, como también
pasan los tests de contrato, que son intercambiables con las de producción
(Liskov).

Los dobles de ClienteHttp y del caché implementan solo los métodos del rol que
cumplen: alcanza con eso para usarlos (segregación de interfaces).

ProcesadorFalso, GuardadorEnMemoria y VisorFalso reemplazan a los detalles
concretos (red, disco, navegador): como el código de alto nivel recibe sus
dependencias, no hace falta monkeypatch (inversión de dependencias).
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

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

    def emitir(
        self, urls: Sequence[str], resultados: Sequence[Articulo | None]
    ) -> None:
        # Guarda copias: el contrato prohíbe depender de las listas recibidas
        self.recibido.append((list(urls), list(resultados)))


@dataclass
class RespuestaFalsa:
    """Solo los tres datos que descargar_html lee de una respuesta."""

    status_code: int = 200
    text: str = ""

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300


@dataclass
class ClienteFalso:
    """Cliente HTTP sin httpx: solo tiene get, que es lo que pide ClienteHttp."""

    respuesta: RespuestaFalsa = field(default_factory=RespuestaFalsa)
    pedidas: list[str] = field(default_factory=list)

    async def get(self, url: str) -> RespuestaFalsa:
        self.pedidas.append(url)
        return self.respuesta


@dataclass
class CacheSoloEscritura:
    """Cumple EscritorCache y nada más: no se puede leer."""

    escrito: dict[str, Articulo] = field(default_factory=dict)

    def actualizar(self, nuevos: dict[str, Articulo]) -> None:
        self.escrito.update(nuevos)


@dataclass
class CacheEnMemoria:
    """Cumple LectorCache y EscritorCache, sin tocar el disco."""

    datos: dict[str, Articulo] = field(default_factory=dict)

    def cargar(self) -> dict[str, Articulo]:
        return dict(self.datos)

    def actualizar(self, nuevos: dict[str, Articulo]) -> None:
        self.datos.update(nuevos)


@dataclass
class ProcesadorFalso:
    """Cumple ProcesadorUrls sin red: devuelve el artículo configurado o None."""

    articulos: dict[str, Articulo] = field(default_factory=dict)
    pedidas: list[str] = field(default_factory=list)

    async def procesar(self, urls: Sequence[str]) -> list[Articulo | None]:
        self.pedidas.extend(urls)
        return [self.articulos.get(url) for url in urls]


@dataclass
class GuardadorEnMemoria:
    """Cumple GuardadorReporte sin tocar el disco."""

    ruta: Path = Path("reporte-en-memoria.html")
    contenidos: list[str] = field(default_factory=list)

    def guardar(self, contenido: str) -> Path:
        self.contenidos.append(contenido)
        return self.ruta


@dataclass
class VisorFalso:
    """Cumple Visor sin abrir nada: registra las rutas."""

    abiertas: list[Path] = field(default_factory=list)

    def abrir(self, ruta: Path) -> None:
        self.abiertas.append(ruta)
