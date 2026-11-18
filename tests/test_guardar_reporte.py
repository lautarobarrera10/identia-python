from pathlib import Path

from identia_python import guardar_reporte


def test_guardar_html_crea_carpeta(tmp_path: Path) -> None:
    destino = tmp_path / "nueva" / "reporte.html"

    ruta = guardar_reporte.guardar_html("<p>hola ñ</p>", destino)

    assert ruta == destino.resolve()
    assert destino.read_text(encoding="utf-8") == "<p>hola ñ</p>"


def test_guardar_html_usa_ruta_por_defecto() -> None:
    ruta = guardar_reporte.guardar_html("x")

    assert ruta == guardar_reporte.ARCHIVO_HTML.resolve()
    assert ruta.is_file()
