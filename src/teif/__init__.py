"""
TEIF Module
===========

Module de génération XML conforme au standard TEIF (Tunisian Electronic Invoice Format).
"""

from .generator import TEIFGenerator
from .sections.signature import create_signature, add_signature, SignatureError

__all__ = [
    'TEIFGenerator',
    'create_signature',
    'add_signature',
    'SignatureError'
]
