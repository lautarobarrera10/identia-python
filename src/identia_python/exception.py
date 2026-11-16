"""
Modulo para las excepciones propias
"""


class DescargaHtmlError(Exception):
    """Excepción para errores al descargar HTML."""


class ParseoHtmlError(Exception):
    """Excepción para errores al parsear HTML (no se encontró título o párrafo)."""
