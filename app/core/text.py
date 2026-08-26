"""Normalización local de texto para búsquedas clínicas no sensibles a acentos."""

import unicodedata


def search_key(value):
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(character for character in normalized if not unicodedata.combining(character)).casefold()


def search_terms(value):
    """Devuelve palabras comparables sin depender de mayúsculas o acentos."""
    return tuple(term for term in search_key(value).split() if term)
