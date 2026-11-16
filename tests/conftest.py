from collections.abc import Callable
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def leer_fixture() -> Callable[[str], str]:
    def _leer(nombre: str) -> str:
        return (FIXTURES / nombre).read_text(encoding="utf-8")

    return _leer
