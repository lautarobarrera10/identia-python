"""
Extracción de texto legible a partir de elementos HTML.
"""

from bs4 import Tag


def texto_o_none(texto: str | None) -> str | None:
    """
    Normaliza los espacios del texto y devuelve None si queda vacío. Ayuda a
    los extractores a cumplir su contrato: texto no vacío o None, nunca "".
    """
    if texto is None:
        return None
    return " ".join(texto.split()) or None


def texto_normalizado(elemento: Tag) -> str:
    """Texto del elemento con los espacios y saltos de línea normalizados."""
    # Sin separador para no meter espacios antes de la puntuación en <b>, <a>, etc.
    return " ".join(elemento.get_text().split())


def texto_de_bajada(elemento: Tag) -> str:
    """
    Texto de la bajada. Si viene como lista (p. ej. Clarín usa <ul><li>),
    devuelve un ítem por línea para que no queden pegados.
    """
    items = [texto_normalizado(li) for li in elemento.find_all("li")]
    items = [item for item in items if item]
    if items:
        return "\n".join(items)
    return texto_normalizado(elemento)
