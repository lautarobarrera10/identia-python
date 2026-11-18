from identia_python.modelos import Articulo
from identia_python.resumen import texto_resumen


def test_texto_resumen_cuenta_exitosos() -> None:
    resultados: list[Articulo | None] = [
        Articulo(titulo="a", primer_parrafo="b"),
        None,
        Articulo(titulo="c", primer_parrafo="d"),
    ]

    assert texto_resumen(resultados) == "Procesadas 2/3 noticias correctamente."


def test_texto_resumen_vacio() -> None:
    assert texto_resumen([]) == "Procesadas 0/0 noticias correctamente."
