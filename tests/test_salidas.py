from pathlib import Path

import pytest
from dobles import GuardadorEnMemoria, SalidaEnMemoria, VisorFalso

from identia_python.guardar_reporte import ReporteEnArchivo
from identia_python.modelos import Articulo
from identia_python.navegador import NavegadorWeb
from identia_python.salidas import Salida, SalidaConsola, SalidaHtml

URLS = ["https://a.com", "https://b.com"]
RESULTADOS: list[Articulo | None] = [
    Articulo(titulo="Título A", primer_parrafo="Párrafo A"),
    None,
]


def test_salida_nueva_recibe_urls_y_resultados() -> None:
    salida = SalidaEnMemoria()
    salidas: list[Salida] = [salida]

    for s in salidas:
        s.emitir(URLS, RESULTADOS)

    assert salida.recibido == [(URLS, RESULTADOS)]


def test_salida_consola(capsys: pytest.CaptureFixture[str]) -> None:
    SalidaConsola().emitir(URLS, RESULTADOS)

    salida = capsys.readouterr().out
    assert "Título: Título A" in salida
    assert "Procesadas 1/2 noticias correctamente." in salida


def test_salida_html_sin_abrir(tmp_path: Path, navegador_falso: list[str]) -> None:
    archivo = tmp_path / "reporte.html"

    SalidaHtml(ReporteEnArchivo(archivo)).emitir(URLS, RESULTADOS)

    assert "Título A" in archivo.read_text(encoding="utf-8")
    assert navegador_falso == []


def test_salida_html_abre_el_navegador(
    tmp_path: Path, navegador_falso: list[str]
) -> None:
    archivo = tmp_path / "reporte.html"

    SalidaHtml(ReporteEnArchivo(archivo), NavegadorWeb()).emitir(URLS, RESULTADOS)

    assert navegador_falso == [archivo.resolve().as_uri()]


def test_salida_html_con_dependencias_inyectadas() -> None:
    """Sin disco ni navegador: SalidaHtml solo conoce las abstracciones."""
    guardador = GuardadorEnMemoria()
    visor = VisorFalso()

    SalidaHtml(guardador, visor).emitir(URLS, RESULTADOS)

    assert len(guardador.contenidos) == 1
    assert "Título A" in guardador.contenidos[0]
    assert visor.abiertas == [guardador.ruta]


def test_no_se_puede_instanciar_la_abstraccion() -> None:
    with pytest.raises(TypeError):
        Salida()  # type: ignore[abstract]
