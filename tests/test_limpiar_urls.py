from identia_python.limpiar_urls import limpiar_urls


def test_ignora_vacias_comentarios_y_repetidas() -> None:
    texto = (
        "# comentario\nhttps://a.com/1\n\n   https://b.com/2   \nhttps://a.com/1\n##\n"
    )

    assert limpiar_urls(texto) == ["https://a.com/1", "https://b.com/2"]


def test_acepta_fin_de_linea_de_windows() -> None:
    texto = "https://a.com/1\r\n# no\r\n\r\nhttps://b.com/2\r\n"

    assert limpiar_urls(texto) == ["https://a.com/1", "https://b.com/2"]


def test_ignora_bom() -> None:
    assert limpiar_urls("﻿https://a.com/1") == ["https://a.com/1"]


def test_texto_vacio() -> None:
    assert limpiar_urls("") == []
