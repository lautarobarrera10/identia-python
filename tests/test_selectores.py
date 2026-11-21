import pytest

from identia_python.selectores import selector_para_url


@pytest.mark.parametrize(
    ("url", "esperado"),
    [
        ("https://www.infobae.com/x", ("h2", "article-subheadline")),
        ("https://clarin.com/x", ("h2", "storySummary")),
        ("https://WWW.CLARIN.COM/x", ("h2", "storySummary")),
        ("https://urgente24.com/dinero/x", ("div", "article-sub-title-p")),
        ("https://www.cronista.com/x", ("h2", "article-head__subtitle")),
        ("https://www.pagina12.com.ar/x", ("h3", "p12Header")),
        ("https://www.lanacion.com.ar/x", ("h2", "--bajada")),
        ("https://noticias.perfil.com/x", ("p", "headline")),
        ("https://noclarin.com/x", None),
        ("https://ejemplo.com/x", None),
        ("no es una url", None),
    ],
)
def test_selector_para_url(url: str, esperado: tuple[str, str] | None) -> None:
    assert selector_para_url(url) == esperado
