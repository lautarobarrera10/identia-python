import threading
import urllib.error
import urllib.request
from collections.abc import Iterator
from urllib.parse import urlencode

import pytest
from dobles import GeneradorFalso

from identia_python import servidor


@pytest.fixture
def generador() -> GeneradorFalso:
    return GeneradorFalso()


@pytest.fixture
def base(generador: GeneradorFalso) -> Iterator[str]:
    """Levanta el servidor en un puerto libre y devuelve su url base."""
    srv = servidor.crear_servidor("127.0.0.1", 0, generador)
    hilo = threading.Thread(target=srv.serve_forever, daemon=True)
    hilo.start()
    host, puerto = srv.server_address[:2]
    yield f"http://{host!s}:{puerto}"
    srv.shutdown()
    srv.server_close()
    hilo.join()


def _pedir(url: str, datos: dict[str, str] | None = None) -> tuple[int, str]:
    cuerpo = urlencode(datos).encode() if datos is not None else None
    try:
        with urllib.request.urlopen(url, data=cuerpo) as r:  # noqa: S310
            return r.status, r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


def test_get_raiz_muestra_formulario(base: str) -> None:
    estado, html = _pedir(f"{base}/")

    assert estado == 200
    assert '<textarea name="urls"' in html
    assert 'action="/reporte"' in html


def test_ruta_desconocida_da_404(base: str) -> None:
    assert _pedir(f"{base}/otra")[0] == 404
    assert _pedir(f"{base}/otra", {"urls": "https://a.com"})[0] == 404


def test_post_genera_reporte_con_urls_limpias(
    base: str, generador: GeneradorFalso
) -> None:
    texto = "https://a.com\n# comentario\n\nhttps://a.com\n https://b.com "

    estado, html = _pedir(f"{base}/reporte", {"urls": texto})

    assert estado == 200
    assert html == generador.html
    assert generador.pedidos == [(["https://a.com", "https://b.com"], False)]


def test_post_con_forzar(base: str, generador: GeneradorFalso) -> None:
    _pedir(f"{base}/reporte", {"urls": "https://a.com", "forzar": "1"})

    assert generador.pedidos == [(["https://a.com"], True)]


def test_post_sin_urls_muestra_error(base: str, generador: GeneradorFalso) -> None:
    estado, html = _pedir(f"{base}/reporte", {"urls": "# nada\n\n"})

    assert estado == 400
    assert "No se encontraron urls." in html
    assert "# nada" in html  # conserva lo escrito
    assert generador.pedidos == []


def test_post_demasiado_grande(
    base: str, generador: GeneradorFalso, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(servidor, "MAX_BYTES_FORMULARIO", 10)

    estado, html = _pedir(f"{base}/reporte", {"urls": "https://a.com/larga"})

    assert estado == 413
    assert "demasiado grande" in html
    assert generador.pedidos == []
