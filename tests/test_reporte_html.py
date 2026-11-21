import re
from html import escape, unescape
from urllib.parse import parse_qs, urlsplit

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


def test_texto_email() -> None:
    urls = ["https://a.com", "https://b.com", "https://c.com"]
    resultados: list[Articulo | None] = [
        Articulo(titulo="Primero", primer_parrafo="Párrafo uno"),
        None,
        Articulo(titulo="Tercero", primer_parrafo="línea 1\nlínea 2"),
    ]

    texto = reporte_html.texto_email(urls, resultados, "01/02/2026 10:00:00")

    assert texto.startswith("Resultados identia-python\n")
    assert "Generado el 01/02/2026 10:00:00" in texto
    assert "Procesadas 2/3 noticias correctamente." in texto
    assert "#1 Primero\nhttps://a.com\nPárrafo uno" in texto
    assert "#2\nhttps://b.com\nNo se pudo procesar esta noticia." in texto
    assert "#3 Tercero\nhttps://c.com\nlínea 1\nlínea 2" in texto
    assert texto.index("#1") < texto.index("#2") < texto.index("#3")


def test_enlace_gmail_codifica_espacios_con_porcentaje_20() -> None:
    enlace = reporte_html.enlace_gmail("Un asunto", "a b\nc")

    assert enlace == (
        "https://mail.google.com/mail/?view=cm&fs=1&su=Un%20asunto&body=a%20b%0Ac"
    )


def test_generar_html_incluye_enlace_gmail() -> None:
    urls = ["https://b.com?x=1&y=2#frag"]
    resultados: list[Articulo | None] = [
        Articulo(titulo="Título <raro> & ?", primer_parrafo="Uno"),
    ]

    html = reporte_html.generar_html(urls, resultados)

    coincidencia = re.search(r'<a class="email" href="([^"]+)"', html)
    assert coincidencia is not None
    partes = urlsplit(unescape(coincidencia.group(1)))
    assert partes.netloc == "mail.google.com"
    campos = parse_qs(partes.query)
    assert campos["view"] == ["cm"]
    assert campos["su"][0].startswith("Reporte identia-python - ")
    assert "#1 Título <raro> & ?\nhttps://b.com?x=1&y=2#frag\nUno" in campos["body"][0]
