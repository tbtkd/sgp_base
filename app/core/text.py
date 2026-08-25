"""Normalización local de texto para búsquedas clínicas no sensibles a acentos."""

import unicodedata


def search_key(value):
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(character for character in normalized if not unicodedata.combining(character)).casefold()
