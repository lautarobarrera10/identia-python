import logging
import webbrowser
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

from identia_python import cache, logging_config, reporte_html

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def leer_fixture() -> Callable[[str], str]:
    def _leer(nombre: str) -> str:
        return (FIXTURES / nombre).read_text(encoding="utf-8")

    return _leer


@pytest.fixture(autouse=True)
def aislar_logging(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    """
    Evita que los tests escriban en logs/ del repo y deja el logger del paquete
    como estaba al terminar cada test (sin handlers, cerrando el archivo).
    """
    monkeypatch.setattr(logging_config, "ARCHIVO_LOG", tmp_path / "logs" / "test.log")
    monkeypatch.setattr(
        reporte_html, "ARCHIVO_HTML", tmp_path / "resultados" / "resultado.html"
    )
    monkeypatch.setattr(cache, "ARCHIVO_CACHE", tmp_path / "resultados" / "cache.json")
    yield
    logger = logging.getLogger(logging_config.LOGGER_RAIZ)
    for handler in list(logger.handlers):
        if not isinstance(handler, logging.NullHandler):
            logger.removeHandler(handler)
            handler.close()
    logger.setLevel(logging.NOTSET)


@pytest.fixture(autouse=True)
def navegador_falso(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Evita que los tests abran el navegador real; registra las urls abiertas."""
    abiertas: list[str] = []

    def abrir(url: str) -> bool:
        abiertas.append(url)
        return True

    monkeypatch.setattr(webbrowser, "open", abrir)
    return abiertas
