from html import escape

from identia_python import reporte_html
from identia_python.modelos import Articulo


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
