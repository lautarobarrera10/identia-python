"""
Generación del reporte HTML a partir de una lista de urls.

GeneradorConCache cumple GeneradorReporte (servidor.py). No sabe cómo se
guarda el caché, cómo se descargan las noticias ni dónde se guarda el reporte:
recibe esas dependencias desde el cli (principio de inversión de
dependencias).
"""

import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from identia_python.reporte_html import generar_html
from identia_python.resultados import (
    EscritorCache,
    LectorCache,
    ProcesadorUrls,
    obtener_resultados,
)

logger = logging.getLogger(__name__)


class GuardadorReporte(Protocol):
    def guardar(self, contenido: str) -> Path:
        """Guarda el reporte y devuelve dónde quedó."""
        ...


class GeneradorConCache:
    """Obtiene los resultados (usando el caché), arma el reporte y lo guarda."""

    def __init__(
        self,
        *,
        lector: LectorCache,
        escritor: EscritorCache,
        procesador: ProcesadorUrls,
        guardador: GuardadorReporte,
        volver: str = "/",
    ) -> None:
        self.lector = lector
        self.escritor = escritor
        self.procesador = procesador
        self.guardador = guardador
        self.volver = volver

    def generar(self, urls: Sequence[str], forzar: bool) -> str:
        resultados = obtener_resultados(
            list(urls),
            forzar,
            lector=self.lector,
            escritor=self.escritor,
            procesador=self.procesador,
        )
        html = generar_html(urls, resultados, volver=self.volver)
        ruta = self.guardador.guardar(html)
        logger.info("Resultado guardado en %s", ruta)
        return html
