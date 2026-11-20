import asyncio
import logging
from collections.abc import Callable

import httpx
import pytest
from dobles import ClienteFalso, RespuestaFalsa

from identia_python.descargar import ClienteHttp, crear_cliente, descargar_html
from identia_python.exceptions import DescargaHtmlError


def _descargar(url: str, handler: Callable[[httpx.Request], httpx.Response]) -> str:
    """Descarga usando el cliente real pero con un transporte falso (sin red)."""

    async def _correr() -> str:
        async with crear_cliente(transport=httpx.MockTransport(handler)) as cliente:
            return await descargar_html(url, cliente)

    return asyncio.run(_correr())


def test_devuelve_html() -> None:
    assert (
        _descargar("https://x.com", lambda req: httpx.Response(200, text="<p>ok</p>"))
        == "<p>ok</p>"
    )


def test_sigue_redirecciones() -> None:
    def handler(req: httpx.Request) -> httpx.Response:
        if req.url.path == "/vieja":
            return httpx.Response(301, headers={"Location": "https://x.com/nueva"})
        return httpx.Response(200, text="destino")

    assert _descargar("https://x.com/vieja", handler) == "destino"


def test_envia_user_agent() -> None:
    recibido: dict[str, str] = {}

    def handler(req: httpx.Request) -> httpx.Response:
        recibido["ua"] = req.headers["User-Agent"]
        return httpx.Response(200, text="")

    _descargar("https://x.com", handler)

    assert recibido["ua"].startswith("Mozilla/5.0")


def test_error_por_status() -> None:
    with pytest.raises(DescargaHtmlError, match="status code: 404"):
        _descargar("https://x.com", lambda req: httpx.Response(404))


def test_error_de_red() -> None:
    def handler(req: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("sin conexión", request=req)

    with pytest.raises(DescargaHtmlError, match="Error de red"):
        _descargar("https://x.com", handler)


def test_loguea_warning_antes_de_fallar(caplog: pytest.LogCaptureFixture) -> None:
    with pytest.raises(DescargaHtmlError):
        _descargar("https://x.com", lambda req: httpx.Response(500))

    assert ("identia_python.descargar", logging.WARNING) in [
        (r.name, r.levelno) for r in caplog.records
    ]
    assert "Status 500 al descargar https://x.com" in caplog.text


# --- Segregación de interfaces: alcanza con un objeto que tenga get ----------


def test_funciona_con_cualquier_cliente_que_tenga_get() -> None:
    cliente = ClienteFalso(RespuestaFalsa(200, "<p>falso</p>"))

    assert asyncio.run(descargar_html("https://x.com", cliente)) == "<p>falso</p>"
    assert cliente.pedidas == ["https://x.com"]


def test_error_por_status_con_cliente_falso() -> None:
    cliente = ClienteFalso(RespuestaFalsa(503))

    with pytest.raises(DescargaHtmlError, match="status code: 503"):
        asyncio.run(descargar_html("https://x.com", cliente))


def test_httpx_cumple_cliente_http() -> None:
    # Lo chequea mypy: si httpx.AsyncClient no cumpliera, esta línea no tipa
    real = crear_cliente()
    cliente: ClienteHttp = real
    assert cliente is real
    asyncio.run(real.aclose())
