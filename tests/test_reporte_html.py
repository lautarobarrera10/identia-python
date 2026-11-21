import json
import re
from datetime import datetime
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
    assert "línea 1<br>línea &lt;2&gt;" in html
    assert "Procesadas 2/3 noticias correctamente." in html
    posiciones = [html.index(f'href="{escape(u)}"') for u in urls]
    assert posiciones == sorted(posiciones)


def test_generar_html_formato_de_cada_noticia() -> None:
    urls = ["https://www.lanacion.com.ar/a", "https://www.clarin.com/b"]
    resultados: list[Articulo | None] = [
        Articulo(titulo="Uno", primer_parrafo="Bajada"),
        None,
    ]

    html = reporte_html.generar_html(urls, resultados)
    dia = datetime.now().strftime("%d-%m-%Y")

    assert f'<p class="medio"><b>LA NACIÓN</b> · {dia}</p>' in html
    assert (
        '<h2><a href="https://www.lanacion.com.ar/a" target="_blank">Uno</a></h2>'
        "<p>Bajada</p>" in html
    )
    assert (
        '<article class="error"><p class="medio"><b>CLARÍN</b>' in html
        and ">No se pudo procesar esta noticia</a></h2></article>" in html
    )
    # Sin numeración ni url visible
    assert ">#" not in html
    assert ">https://" not in html


MOMENTO = datetime(2026, 2, 1, 10, 0, 0)


def test_texto_email() -> None:
    urls = [
        "https://www.lanacion.com.ar/a",
        "https://www.clarin.com/b",
        "https://c.com/x",
    ]
    resultados: list[Articulo | None] = [
        Articulo(titulo="Primero", primer_parrafo="Párrafo uno"),
        None,
        Articulo(titulo="Tercero", primer_parrafo="línea 1\nlínea 2"),
    ]

    texto = reporte_html.texto_email(urls, resultados, MOMENTO)

    assert texto.startswith("LA NACIÓN · 01-02-2026\n")
    assert "Resultados" not in texto
    assert "Generado el" not in texto
    assert (
        "LA NACIÓN · 01-02-2026\nPrimero\nhttps://www.lanacion.com.ar/a\nPárrafo uno"
        in texto
    )
    assert (
        "CLARÍN · 01-02-2026\nNo se pudo procesar esta noticia.\n"
        "https://www.clarin.com/b" in texto
    )
    assert "C.COM · 01-02-2026\nTercero\nhttps://c.com/x\nlínea 1\nlínea 2" in texto
    assert "#" not in texto
    assert texto.index("Primero") < texto.index("CLARÍN") < texto.index("Tercero")


def test_html_email_formato_de_cada_noticia() -> None:
    urls = ["https://www.lanacion.com.ar/a?x=1&y=2", "https://www.clarin.com/b"]
    resultados: list[Articulo | None] = [
        Articulo(titulo="<b>Uno</b>", primer_parrafo="línea 1\nlínea <2>"),
        None,
    ]

    html = reporte_html.html_email(urls, resultados, MOMENTO)

    assert "<style" not in html
    # Sin numeración: ningún texto visible empieza con "#"
    assert ">#" not in html
    assert '<b style="color:#1d2330">LA NACIÓN</b> · 01-02-2026' in html
    assert '<b style="color:#1d2330">CLARÍN</b> · 01-02-2026' in html
    # El título es un enlace común, sin estilo propio
    assert (
        '<a href="https://www.lanacion.com.ar/a?x=1&amp;y=2">'
        "&lt;b&gt;Uno&lt;/b&gt;</a>" in html
    )
    assert "línea 1<br>línea &lt;2&gt;" in html
    assert ">No se pudo procesar esta noticia</a>" in html
    # La url solo aparece como destino del enlace, nunca como texto visible
    assert ">https://" not in html
    # Sin encabezado
    assert "<h1" not in html
    assert "Generado el" not in html
    assert "Procesadas" not in html
    assert html.index("LA NACIÓN") < html.index("CLARÍN")


def test_enlace_gmail_solo_lleva_asunto() -> None:
    enlace = reporte_html.enlace_gmail("Un asunto & más")

    assert enlace == (
        "https://mail.google.com/mail/?view=cm&fs=1&su=Un%20asunto%20%26%20m%C3%A1s"
    )


def test_generar_html_incluye_boton_gmail_y_datos_para_copiar() -> None:
    urls = ["https://b.com?x=1&y=2#frag"]
    resultados: list[Articulo | None] = [
        Articulo(titulo="</script><script>alert(1)</script>", primer_parrafo="Uno"),
    ]

    html = reporte_html.generar_html(urls, resultados)

    boton = re.search(r'id="enviar-email" href="([^"]+)"', html)
    assert boton is not None
    partes = urlsplit(unescape(boton.group(1)))
    assert partes.netloc == "mail.google.com"
    campos = parse_qs(partes.query)
    assert campos["view"] == ["cm"]
    assert campos["su"][0].startswith("Reporte identia-python - ")
    assert "body" not in campos

    bloque = re.search(
        r'<script type="application/json" id="datos-email">(.*?)</script>',
        html,
        re.DOTALL,
    )
    assert bloque is not None
    assert "<" not in bloque.group(1)
    datos = json.loads(bloque.group(1))
    assert "&lt;/script&gt;&lt;script&gt;alert(1)" in datos["html"]
    assert "</script><script>alert(1)</script>\nhttps://b.com" in datos["texto"]
