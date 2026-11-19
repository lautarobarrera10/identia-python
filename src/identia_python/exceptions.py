"""
Modulo para las excepciones propias.

Todas heredan de IdentiaError: el código que atrapa IdentiaError maneja
cualquier error propio, incluidos los que se agreguen después, sin cambios
(principio de Liskov).
"""


class IdentiaError(Exception):
    """Base de los errores esperables al procesar una noticia."""


class DescargaHtmlError(IdentiaError):
    """Excepción para errores al descargar HTML."""


class ParseoHtmlError(IdentiaError):
    """Excepción para errores al parsear HTML (no se encontró título o párrafo)."""
