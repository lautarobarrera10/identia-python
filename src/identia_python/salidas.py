"""
Salidas de los resultados (consola, reporte HTML, ...).

Cada destino es una Salida. Para agregar uno nuevo (JSON, CSV, ...) se crea
otra subclase y se la registra en la lista de salidas del cli, sin modificar
el código que las recorre (principio Open/Closed).
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path

from identia_python import guardar_reporte
from identia_python.modelos import Articulo
from identia_python.navegador import abrir_en_navegador
from identia_python.reporte_html import generar_html
from identia_python.salida_consola import imprimir_resultados

logger = logging.getLogger(__name__)


class Salida(ABC):
    """Destino al que se envían los resultados de una ejecución."""

    @abstractmethod
    def emitir(self, urls: list[str], resultados: list[Articulo | None]) -> None:
        """
        Presenta los resultados (uno por url, en el mismo orden).

        Contrato que toda subclase debe respetar:
        - Precondición: len(urls) == len(resultados). Las listas pueden estar
          vacías o tener solo None; una subclase no puede exigir más que esto.
        - Postcondición: no modifica las listas recibidas y devuelve None.
        """


class SalidaConsola(Salida):
    """Imprime los resultados y el resumen por stdout."""

    def emitir(self, urls: list[str], resultados: list[Articulo | None]) -> None:
        imprimir_resultados(urls, resultados)


class SalidaHtml(Salida):
    """Guarda un reporte HTML y, opcionalmente, lo abre en el navegador."""

    def __init__(self, archivo: Path, abrir: bool = True) -> None:
        self.archivo = archivo
        self.abrir = abrir

    def emitir(self, urls: list[str], resultados: list[Articulo | None]) -> None:
        ruta = guardar_reporte.guardar_html(
            generar_html(urls, resultados), self.archivo
        )
        logger.info("Resultado guardado en %s", ruta)
        if self.abrir:
            abrir_en_navegador(ruta)
