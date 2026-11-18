import webbrowser
from pathlib import Path

import pytest

from identia_python.navegador import abrir_en_navegador


def test_abrir_en_navegador_usa_uri_file(
    tmp_path: Path, navegador_falso: list[str]
) -> None:
    ruta = tmp_path / "r.html"

    abrir_en_navegador(ruta)

    assert navegador_falso == [ruta.resolve().as_uri()]
    assert navegador_falso[0].startswith("file://")


def test_abrir_en_navegador_avisa_si_falla(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr(webbrowser, "open", lambda url: False)

    abrir_en_navegador(tmp_path / "r.html")

    assert "No se pudo abrir el navegador" in caplog.text
