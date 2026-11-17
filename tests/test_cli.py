import asyncio
import runpy
from pathlib import Path

import httpx
import pytest

from identia_python import cli, logging_config
from identia_python.exceptions import DescargaHtmlError, ParseoHtmlError
from identia_python.parsear import Articulo


def _escribir_urls(tmp_path: Path, contenido: str) -> Path:
    ruta = tmp_path / "urls.txt"
    ruta.write_text(contenido, encoding="utf-8")
    return ruta


def _parsear_falso(html: str, url: str) -> Articulo:
    return Articulo(titulo=f"Título de {html}", primer_parrafo="Un párrafo")


async def _descargar_falso(url: str, cliente: httpx.AsyncClient) -> str:
    return f"html-{url}"


def _sin_red(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "descargar_html", _descargar_falso)
    monkeypatch.setattr(cli, "parsear_articulo", _parsear_falso)


def test_archivo_inexistente(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main([str(tmp_path / "no.txt")])

    assert exc.value.code == 1
    assert "ERROR: No se encontró el archivo de urls" in capsys.readouterr().err


def test_archivo_sin_urls(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    ruta = _escribir_urls(tmp_path, "# solo comentarios\n\n")

    with pytest.raises(SystemExit) as exc:
        cli.main([str(ruta)])

    assert exc.value.code == 1
    assert "no contiene urls" in capsys.readouterr().err


def test_usa_urls_txt_del_directorio_actual_por_defecto(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _escribir_urls(tmp_path, "https://a.com\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["identia-python"])
    _sin_red(monkeypatch)

    cli.main()

    salida = capsys.readouterr()
    assert "INFO: [1/1] https://a.com" in salida.err
    assert "Título de html-https://a.com" in salida.out
    assert "Procesadas 1/1 noticias correctamente." in salida.out


def test_procesa_urls_y_cuenta_errores(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    ruta = _escribir_urls(
        tmp_path,
        "https://ok.com\nhttps://descarga.com\nhttps://parseo.com\nhttps://raro.com\n",
    )

    async def descargar_falso(url: str, cliente: httpx.AsyncClient) -> str:
        if url == "https://descarga.com":
            raise DescargaHtmlError("falló la descarga")
        if url == "https://raro.com":
            raise ValueError("url inválida")
        return url

    def parsear_falso(html: str, url: str) -> Articulo:
        if url == "https://parseo.com":
            raise ParseoHtmlError("sin título")
        return _parsear_falso(html, url)

    monkeypatch.setattr(cli, "descargar_html", descargar_falso)
    monkeypatch.setattr(cli, "parsear_articulo", parsear_falso)

    cli.main([str(ruta)])

    salida = capsys.readouterr()
    assert "Título de https://ok.com" in salida.out
    assert "Primer párrafo: Un párrafo" in salida.out
    assert "Procesadas 1/4 noticias correctamente." in salida.out
    assert "ERROR: falló la descarga" in salida.err
    assert "ERROR: sin título" in salida.err
    assert "ERROR: Error inesperado: ValueError: url inválida" in salida.err
    # El traceback solo se muestra en consola con -v
    assert "Traceback" not in salida.err


def test_salida_respeta_orden_del_archivo(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    urls = ["https://a.com", "https://b.com", "https://c.com"]
    ruta = _escribir_urls(tmp_path, "\n".join(urls) + "\n")
    terminadas: list[str] = []

    async def descargar_falso(url: str, cliente: httpx.AsyncClient) -> str:
        # La primera url tarda más: las descargas terminan en orden inverso
        await asyncio.sleep(0.01 * (len(urls) - urls.index(url)))
        terminadas.append(url)
        return url

    monkeypatch.setattr(cli, "descargar_html", descargar_falso)
    monkeypatch.setattr(cli, "parsear_articulo", _parsear_falso)

    cli.main([str(ruta), "-q"])

    assert terminadas == list(reversed(urls))
    salida = capsys.readouterr().out
    posiciones = [salida.index(f"Título de {url}") for url in urls]
    assert posiciones == sorted(posiciones)


def test_verbose_muestra_debug(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    ruta = _escribir_urls(tmp_path, "https://a.com\nhttps://a.com\n")
    _sin_red(monkeypatch)

    cli.main([str(ruta), "-v"])

    assert "DEBUG: Leídas 1 urls" in capsys.readouterr().err


def test_quiet_oculta_info(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    ruta = _escribir_urls(tmp_path, "https://a.com\n")
    _sin_red(monkeypatch)

    cli.main([str(ruta), "-q"])

    salida = capsys.readouterr()
    assert salida.err == ""
    assert "Procesadas 1/1 noticias correctamente." in salida.out


def test_verbose_y_quiet_son_excluyentes(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main([str(tmp_path / "urls.txt"), "-v", "-q"])

    assert exc.value.code == 2


def test_escribe_archivo_de_log(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ruta = _escribir_urls(tmp_path, "https://a.com\n")
    _sin_red(monkeypatch)

    cli.main([str(ruta), "-q"])

    contenido = logging_config.ARCHIVO_LOG.read_text(encoding="utf-8")
    assert "INFO identia_python.cli: [1/1] https://a.com" in contenido
    assert "DEBUG identia_python.leer_urls: Leídas 1 urls" in contenido


def test_ejecutar_como_modulo(monkeypatch: pytest.MonkeyPatch) -> None:
    llamado: list[bool] = []
    monkeypatch.setattr(cli, "main", lambda: llamado.append(True))

    runpy.run_module("identia_python", run_name="__main__")

    assert llamado == [True]
