import webbrowser

import pytest

from identia_python.navegador import abrir_url


def test_abrir_url(navegador_falso: list[str]) -> None:
    abrir_url("http://127.0.0.1:8000/")

    assert navegador_falso == ["http://127.0.0.1:8000/"]


def test_abrir_url_avisa_si_falla(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(webbrowser, "open", lambda url: False)

    abrir_url("http://127.0.0.1:8000/")

    assert "No se pudo abrir el navegador" in caplog.text
