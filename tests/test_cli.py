import runpy
from pathlib import Path

import pytest

from identia_python import cli
from identia_python.exceptions import DescargaHtmlError, ParseoHtmlError
from identia_python.parsear import Articulo


def _escribir_urls(tmp_path: Path, contenido: str) -> Path:
    ruta = tmp_path / "urls.txt"
    ruta.write_text(contenido, encoding="utf-8")
    return ruta


def _parsear_falso(html: str, url: str) -> Articulo:
    return Articulo(titulo=f"Título de {html}", primer_parrafo="Un párrafo")


def test_archivo_inexistente(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("sys.argv", ["identia-python", str(tmp_path / "no.txt")])

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 1
    assert "No se encontró el archivo de urls" in capsys.readouterr().err


def test_archivo_sin_urls(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    ruta = _escribir_urls(tmp_path, "# solo comentarios\n\n")
    monkeypatch.setattr("sys.argv", ["identia-python", str(ruta)])

    with pytest.raises(SystemExit) as exc:
        cli.main()

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
    monkeypatch.setattr(cli, "descargar_html", lambda url: "html-a")
    monkeypatch.setattr(cli, "parsear_articulo", _parsear_falso)

    cli.main()

    salida = capsys.readouterr().out
    assert "[1/1] https://a.com" in salida
    assert "Título de html-a" in salida
    assert "Procesadas 1/1 noticias correctamente." in salida


def test_procesa_urls_y_cuenta_errores(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    ruta = _escribir_urls(
        tmp_path,
        "https://ok.com\nhttps://descarga.com\nhttps://parseo.com\nhttps://raro.com\n",
    )
    monkeypatch.setattr("sys.argv", ["identia-python", str(ruta)])

    def descargar_falso(url: str) -> str:
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

    cli.main()

    salida = capsys.readouterr().out
    assert "Título de https://ok.com" in salida
    assert "Primer párrafo: Un párrafo" in salida
    assert "Error: falló la descarga" in salida
    assert "Error: sin título" in salida
    assert "Error inesperado: ValueError: url inválida" in salida
    assert "Procesadas 1/4 noticias correctamente." in salida


def test_ejecutar_como_modulo(monkeypatch: pytest.MonkeyPatch) -> None:
    llamado: list[bool] = []
    monkeypatch.setattr(cli, "main", lambda: llamado.append(True))

    runpy.run_module("identia_python", run_name="__main__")

    assert llamado == [True]
