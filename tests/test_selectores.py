import pytest

from identia_python.selectores import selector_para_url


@pytest.mark.parametrize(
    ("url", "esperado"),
    [
        ("https://www.infobae.com/x", ("h2", "article-subheadline")),
        ("https://clarin.com/x", ("h2", "storySummary")),
        ("https://WWW.CLARIN.COM/x", ("h2", "storySummary")),
        ("https://noclarin.com/x", None),
        ("https://ejemplo.com/x", None),
        ("no es una url", None),
    ],
)
def test_selector_para_url(url: str, esperado: tuple[str, str] | None) -> None:
    assert selector_para_url(url) == esperado
