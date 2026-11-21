import runpy
from collections.abc import Sequence
from pathlib import Path

import httpx
import pytest

from identia_python import cache, cli, guardar_reporte, logging_config, procesamiento
from identia_python.modelos import Articulo
from identia_python.servidor import GeneradorReporte


def _parsear_falso(html: str, url: str) -> Articulo:
    return Articulo(titulo=f"Título de {html}", primer_parrafo="Un párrafo")


async def _descargar_falso(url: str, cliente: httpx.AsyncClient) -> str:
    return f"html-{url}"


def _sin_red(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(procesamiento, "descargar_html", _descargar_falso)
    monkeypatch.setattr(procesamiento, "parsear_articulo", _parsear_falso)


class ServidorFalso:
    """Reemplaza al servidor real: serve_forever simula un Ctrl+C."""

    def __init__(self, host: str, puerto: int, generador: GeneradorReporte) -> None:
        self.server_address = (host, puerto or 54321)
        self.generador = generador
        self.cerrado = False

    def serve_forever(self) -> None:
        raise KeyboardInterrupt

    def server_close(self) -> None:
        self.cerrado = True


@pytest.fixture
def servidores(monkeypatch: pytest.MonkeyPatch) -> list[ServidorFalso]:
    creados: list[ServidorFalso] = []

    def crear(host: str, puerto: int, generador: GeneradorReporte) -> ServidorFalso:
        creados.append(ServidorFalso(host, puerto, generador))
        return creados[-1]

    monkeypatch.setattr(cli, "crear_servidor", crear)
    return creados


def test_levanta_servidor_y_abre_navegador(
    servidores: list[ServidorFalso],
    navegador_falso: list[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    cli.main([])

    (srv,) = servidores
    assert srv.server_address == ("127.0.0.1", 8000)
    assert srv.cerrado
    assert navegador_falso == ["http://127.0.0.1:8000/"]
    err = capsys.readouterr().err
    assert "Servidor en http://127.0.0.1:8000/" in err
    assert "Servidor detenido" in err


def test_host_puerto_y_no_abrir(
    servidores: list[ServidorFalso], navegador_falso: list[str]
) -> None:
    cli.main(["--host", "0.0.0.0", "--puerto", "9000", "--no-abrir"])  # noqa: S104

    assert servidores[0].server_address == ("0.0.0.0", 9000)  # noqa: S104
    assert navegador_falso == []


def test_quiet_no_muestra_info(
    servidores: list[ServidorFalso], capsys: pytest.CaptureFixture[str]
) -> None:
    cli.main(["-q", "--no-abrir"])

    assert capsys.readouterr().err == ""


def test_verbose_y_quiet_son_excluyentes() -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["-v", "-q"])

    assert exc.value.code == 2


def test_escribe_archivo_de_log(servidores: list[ServidorFalso]) -> None:
    cli.main(["-q", "--no-abrir"])

    contenido = logging_config.ARCHIVO_LOG.read_text(encoding="utf-8")
    assert "INFO identia_python.cli: Servidor en" in contenido


def test_ejecutar_como_modulo(monkeypatch: pytest.MonkeyPatch) -> None:
    llamado: list[bool] = []
    monkeypatch.setattr(cli, "main", lambda: llamado.append(True))

    runpy.run_module("identia_python", run_name="__main__")

    assert llamado == [True]


def _generar(urls: Sequence[str], forzar: bool = False) -> str:
    return cli.crear_generador().generar(urls, forzar)


def test_generador_real_guarda_reporte_y_cache(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _sin_red(monkeypatch)

    html = _generar(["https://a.com"])

    assert "Título de html-https://a.com" in html
    assert guardar_reporte.ARCHIVO_HTML.read_text(encoding="utf-8") == html
    assert set(cache.cargar_cache()) == {"https://a.com"}


def test_generador_real_usa_cache_y_forzar(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    cache.guardar_cache(
        {"https://a.com": Articulo(titulo="Guardado", primer_parrafo="De antes")}
    )
    _sin_red(monkeypatch)

    assert "Guardado" in _generar(["https://a.com"])
    assert "Título de html-https://a.com" in _generar(["https://a.com"], forzar=True)
