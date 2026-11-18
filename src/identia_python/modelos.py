"""
Modelos de datos del dominio.
"""

from dataclasses import dataclass


@dataclass
class Articulo:
    titulo: str
    primer_parrafo: str
