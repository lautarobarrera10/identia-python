from collections.abc import Callable
from typing import Any

import httpx
import pytest

from identia_python.descargar import descargar_html
from identia_python.exceptions import DescargaHtmlError


def _usar_transporte(
    monkeypatch: pytest.MonkeyPatch, handler: Callable[[httpx.Request], httpx.Response]
) -> None:
    """Reemplaza httpx.get por uno que usa un transporte falso (sin red)."""
    cliente = httpx.Client(transport=httpx.MockTransport(handler))

    def get_falso(url: str, **kwargs: Any) -> httpx.Response:
        return cliente.get(url, **kwargs)

    monkeypatch.setattr(httpx, "get", get_falso)


def test_devuelve_html(monkeypatch: pytest.MonkeyPatch) -> None:
    _usar_transporte(monkeypatch, lambda req: httpx.Response(200, text="<p>ok</p>"))

    assert descargar_html("https://x.com") == "<p>ok</p>"


def test_sigue_redirecciones(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(req: httpx.Request) -> httpx.Response:
        if req.url.path == "/vieja":
            return httpx.Response(301, headers={"Location": "https://x.com/nueva"})
        return httpx.Response(200, text="destino")

    _usar_transporte(monkeypatch, handler)

    assert descargar_html("https://x.com/vieja") == "destino"


def test_envia_user_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    recibido: dict[str, str] = {}

    def handler(req: httpx.Request) -> httpx.Response:
        recibido["ua"] = req.headers["User-Agent"]
        return httpx.Response(200, text="")

    _usar_transporte(monkeypatch, handler)
    descargar_html("https://x.com")

    assert recibido["ua"].startswith("Mozilla/5.0")


def test_error_por_status(monkeypatch: pytest.MonkeyPatch) -> None:
    _usar_transporte(monkeypatch, lambda req: httpx.Response(404))

    with pytest.raises(DescargaHtmlError, match="status code: 404"):
        descargar_html("https://x.com")


def test_error_de_red(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(req: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("sin conexión", request=req)

    _usar_transporte(monkeypatch, handler)

    with pytest.raises(DescargaHtmlError, match="Error de red"):
        descargar_html("https://x.com")
