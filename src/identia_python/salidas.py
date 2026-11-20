"""
Salidas de los resultados (consola, reporte HTML, ...).

Cada destino es una Salida. Para agregar uno nuevo (JSON, CSV, ...) se crea
otra subclase y se la registra en la lista de salidas del cli, sin modificar
el código que las recorre (principio Open/Closed).

SalidaHtml no depende del disco ni del navegador sino de GuardadorReporte y
Visor, definidos acá; las implementaciones concretas las arma el cli
(principio de inversión de dependencias).
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from identia_python.modelos import Articulo
from identia_python.reporte_html import generar_html
from identia_python.salida_consola import imprimir_resultados

logger = logging.getLogger(__name__)


class Salida(ABC):
    """Destino al que se envían los resultados de una ejecución."""

    @abstractmethod
    def emitir(
        self, urls: Sequence[str], resultados: Sequence[Articulo | None]
    ) -> None:
        """
        Presenta los resultados (uno por url, en el mismo orden). Recibe
        Sequence y no list: solo puede leerlas (segregación de interfaces).

        Contrato que toda subclase debe respetar:
        - Precondición: len(urls) == len(resultados). Las listas pueden estar
          vacías o tener solo None; una subclase no puede exigir más que esto.
        - Postcondición: no modifica las listas recibidas y devuelve None.
        """


class SalidaConsola(Salida):
    """Imprime los resultados y el resumen por stdout."""

    def emitir(
        self, urls: Sequence[str], resultados: Sequence[Articulo | None]
    ) -> None:
        imprimir_resultados(urls, resultados)


class GuardadorReporte(Protocol):
    def guardar(self, contenido: str) -> Path:
        """Guarda el reporte y devuelve dónde quedó."""
        ...


class Visor(Protocol):
    def abrir(self, ruta: Path) -> None:
        """Muestra el reporte guardado en la ruta."""
        ...


class SalidaHtml(Salida):
    """
    Genera un reporte HTML, lo guarda y, si hay visor, lo abre. No sabe dónde
    se guarda ni cómo se abre: lo decide el guardador y el visor que recibe.
    """

    def __init__(self, guardador: GuardadorReporte, visor: Visor | None = None) -> None:
        self.guardador = guardador
        self.visor = visor

    def emitir(
        self, urls: Sequence[str], resultados: Sequence[Articulo | None]
    ) -> None:
        ruta = self.guardador.guardar(generar_html(urls, resultados))
        logger.info("Resultado guardado en %s", ruta)
        if self.visor is not None:
            self.visor.abrir(ruta)
