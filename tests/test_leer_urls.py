from pathlib import Path

from identia_python.leer_urls import leer_urls


def test_ignora_vacias_comentarios_y_repetidas(tmp_path: Path) -> None:
    archivo = tmp_path / "urls.txt"
    archivo.write_text(
        "# comentario\nhttps://a.com/1\n\n   https://b.com/2   \nhttps://a.com/1\n##\n",
        encoding="utf-8",
    )

    assert leer_urls(archivo) == ["https://a.com/1", "https://b.com/2"]


def test_ignora_bom(tmp_path: Path) -> None:
    archivo = tmp_path / "urls.txt"
    archivo.write_text("https://a.com/1\n", encoding="utf-8-sig")

    assert leer_urls(archivo) == ["https://a.com/1"]


def test_archivo_vacio(tmp_path: Path) -> None:
    archivo = tmp_path / "urls.txt"
    archivo.write_text("", encoding="utf-8")

    assert leer_urls(archivo) == []
