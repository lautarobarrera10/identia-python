import asyncio
import runpy
from pathlib import Path

import httpx
import pytest

from identia_python import cache, cli, guardar_reporte, logging_config, procesamiento
from identia_python.exceptions import DescargaHtmlError, ParseoHtmlError
from identia_python.modelos import Articulo


def _escribir_urls(tmp_path: Path, contenido: str) -> Path:
    ruta = tmp_path / "urls.txt"
    ruta.write_text(contenido, encoding="utf-8")
    return ruta


def _parsear_falso(html: str, url: str) -> Articulo:
    return Articulo(titulo=f"Título de {html}", primer_parrafo="Un párrafo")


async def _descargar_falso(url: str, cliente: httpx.AsyncClient) -> str:
    return f"html-{url}"


def _sin_red(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(procesamiento, "descargar_html", _descargar_falso)
    monkeypatch.setattr(procesamiento, "parsear_articulo", _parsear_falso)


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

    monkeypatch.setattr(procesamiento, "descargar_html", descargar_falso)
    monkeypatch.setattr(procesamiento, "parsear_articulo", parsear_falso)

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

    monkeypatch.setattr(procesamiento, "descargar_html", descargar_falso)
    monkeypatch.setattr(procesamiento, "parsear_articulo", _parsear_falso)

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
    assert "INFO identia_python.procesamiento: [1/1] https://a.com" in contenido
    assert "DEBUG identia_python.leer_urls: Leídas 1 urls" in contenido


def test_ejecutar_como_modulo(monkeypatch: pytest.MonkeyPatch) -> None:
    llamado: list[bool] = []
    monkeypatch.setattr(cli, "main", lambda: llamado.append(True))

    runpy.run_module("identia_python", run_name="__main__")

    assert llamado == [True]


def test_genera_html_y_lo_abre(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, navegador_falso: list[str]
) -> None:
    ruta = _escribir_urls(tmp_path, "https://a.com\n")
    _sin_red(monkeypatch)

    cli.main([str(ruta), "-q"])

    html = guardar_reporte.ARCHIVO_HTML.read_text(encoding="utf-8")
    assert "Título de html-https://a.com" in html
    assert "Procesadas 1/1 noticias correctamente." in html
    assert navegador_falso == [guardar_reporte.ARCHIVO_HTML.resolve().as_uri()]


def test_no_abrir_solo_genera_html(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, navegador_falso: list[str]
) -> None:
    ruta = _escribir_urls(tmp_path, "https://a.com\n")
    _sin_red(monkeypatch)

    cli.main([str(ruta), "-q", "--no-abrir"])

    assert guardar_reporte.ARCHIVO_HTML.is_file()
    assert navegador_falso == []


def test_urls_en_cache_no_se_descargan(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cache.guardar_cache(
        {"https://a.com": Articulo(titulo="Guardado", primer_parrafo="De antes")}
    )
    ruta = _escribir_urls(tmp_path, "https://a.com\nhttps://b.com\n")
    descargadas: list[str] = []

    async def descargar_falso(url: str, cliente: httpx.AsyncClient) -> str:
        descargadas.append(url)
        return f"html-{url}"

    monkeypatch.setattr(procesamiento, "descargar_html", descargar_falso)
    monkeypatch.setattr(procesamiento, "parsear_articulo", _parsear_falso)

    cli.main([str(ruta)])

    assert descargadas == ["https://b.com"]
    salida = capsys.readouterr()
    assert "Título: Guardado" in salida.out
    assert "Título de html-https://b.com" in salida.out
    assert "Procesadas 2/2 noticias correctamente." in salida.out
    assert "1/2 urls ya procesadas, se usan del caché" in salida.err
    assert set(cache.cargar_cache()) == {"https://a.com", "https://b.com"}


def test_todo_en_cache_no_descarga_nada(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cache.guardar_cache(
        {"https://a.com": Articulo(titulo="Guardado", primer_parrafo="De antes")}
    )
    ruta = _escribir_urls(tmp_path, "https://a.com\n")

    async def no_descargar(url: str, cliente: httpx.AsyncClient) -> str:
        raise AssertionError("no debería descargar")

    monkeypatch.setattr(procesamiento, "descargar_html", no_descargar)

    cli.main([str(ruta)])

    salida = capsys.readouterr()
    assert "Título: Guardado" in salida.out
    assert "no se descarga nada" in salida.err
    assert "Guardado" in guardar_reporte.ARCHIVO_HTML.read_text(encoding="utf-8")


def test_errores_no_se_guardan_en_cache(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ruta = _escribir_urls(tmp_path, "https://ok.com\nhttps://mal.com\n")

    async def descargar_falso(url: str, cliente: httpx.AsyncClient) -> str:
        if url == "https://mal.com":
            raise DescargaHtmlError("falló")
        return url

    monkeypatch.setattr(procesamiento, "descargar_html", descargar_falso)
    monkeypatch.setattr(procesamiento, "parsear_articulo", _parsear_falso)

    cli.main([str(ruta), "-q"])

    assert set(cache.cargar_cache()) == {"https://ok.com"}


def test_forzar_ignora_cache_y_conserva_otras_urls(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cache.guardar_cache(
        {
            "https://a.com": Articulo(titulo="Viejo", primer_parrafo="x"),
            "https://otra.com": Articulo(titulo="Otra", primer_parrafo="y"),
        }
    )
    ruta = _escribir_urls(tmp_path, "https://a.com\n")
    _sin_red(monkeypatch)

    cli.main([str(ruta), "-q", "--forzar"])

    assert "Título de html-https://a.com" in capsys.readouterr().out
    guardado = cache.cargar_cache()
    assert guardado["https://a.com"].titulo == "Título de html-https://a.com"
    assert guardado["https://otra.com"].titulo == "Otra"
