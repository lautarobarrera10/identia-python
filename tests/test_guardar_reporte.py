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


def test_reporte_en_archivo_guarda_en_su_archivo(tmp_path: Path) -> None:
    destino = tmp_path / "r.html"

    ruta = guardar_reporte.ReporteEnArchivo(destino).guardar("<p>x</p>")

    assert ruta == destino.resolve()
    assert destino.read_text(encoding="utf-8") == "<p>x</p>"
