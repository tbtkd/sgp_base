from datetime import UTC, datetime


def utcnow_naive():
    """Return UTC without tzinfo for compatibility with SQLite DateTime columns."""
    return datetime.now(UTC).replace(tzinfo=None)
