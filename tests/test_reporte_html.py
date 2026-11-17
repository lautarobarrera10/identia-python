import webbrowser
from html import escape
from pathlib import Path

import pytest

from identia_python import reporte_html
from identia_python.parsear import Articulo


def test_generar_html_escapa_y_respeta_orden() -> None:
    urls = ["https://a.com", "https://b.com?x=1&y=2", "https://c.com"]
    resultados: list[Articulo | None] = [
        Articulo(titulo="<script>alert(1)</script>", primer_parrafo="Uno"),
        None,
        Articulo(titulo="Tercero", primer_parrafo="línea 1\nlínea <2>"),
    ]

    html = reporte_html.generar_html(urls, resultados)

    assert html.startswith("<!doctype html>")
    assert '<meta charset="utf-8">' in html
    assert "<script>alert" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert 'href="https://b.com?x=1&amp;y=2"' in html
    assert "No se pudo procesar esta noticia." in html
    assert "línea 1<br>línea &lt;2&gt;" in html
    assert "Procesadas 2/3 noticias correctamente." in html
    posiciones = [html.index(f'href="{escape(u)}"') for u in urls]
    assert posiciones == sorted(posiciones)


def test_guardar_html_crea_carpeta(tmp_path: Path) -> None:
    destino = tmp_path / "nueva" / "reporte.html"

    ruta = reporte_html.guardar_html("<p>hola ñ</p>", destino)

    assert ruta == destino.resolve()
    assert destino.read_text(encoding="utf-8") == "<p>hola ñ</p>"


def test_guardar_html_usa_ruta_por_defecto() -> None:
    ruta = reporte_html.guardar_html("x")

    assert ruta == reporte_html.ARCHIVO_HTML.resolve()
    assert ruta.is_file()


def test_abrir_en_navegador_usa_uri_file(
    tmp_path: Path, navegador_falso: list[str]
) -> None:
    ruta = tmp_path / "r.html"

    reporte_html.abrir_en_navegador(ruta)

    assert navegador_falso == [ruta.resolve().as_uri()]
    assert navegador_falso[0].startswith("file://")


def test_abrir_en_navegador_avisa_si_falla(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr(webbrowser, "open", lambda url: False)

    reporte_html.abrir_en_navegador(tmp_path / "r.html")

    assert "No se pudo abrir el navegador" in caplog.text
