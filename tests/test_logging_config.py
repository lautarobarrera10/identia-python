import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from identia_python.logging_config import LOGGER_RAIZ, configurar_logging


def _handlers() -> list[logging.Handler]:
    return logging.getLogger(LOGGER_RAIZ).handlers


def test_configura_consola_y_archivo(tmp_path: Path) -> None:
    archivo = tmp_path / "sub" / "app.log"

    configurar_logging(logging.WARNING, archivo=archivo)

    consola = [h for h in _handlers() if type(h) is logging.StreamHandler]
    en_archivo = [h for h in _handlers() if isinstance(h, RotatingFileHandler)]
    assert [h.level for h in consola] == [logging.WARNING]
    assert [h.level for h in en_archivo] == [logging.DEBUG]

    logging.getLogger(f"{LOGGER_RAIZ}.algo").debug("mensaje de prueba")
    en_archivo[0].flush()
    assert "DEBUG identia_python.algo: mensaje de prueba" in archivo.read_text(
        encoding="utf-8"
    )


def test_no_duplica_handlers(tmp_path: Path) -> None:
    configurar_logging(archivo=tmp_path / "app.log")
    configurar_logging(archivo=tmp_path / "app.log")

    assert len(_handlers()) == 2


def test_sin_archivo(tmp_path: Path) -> None:
    configurar_logging(archivo=None)

    assert not any(isinstance(h, logging.FileHandler) for h in _handlers())
    assert list(tmp_path.iterdir()) == []
