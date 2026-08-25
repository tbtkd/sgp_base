from datetime import datetime, timezone


def utcnow_naive():
    """Return UTC without tzinfo for compatibility with SQLite DateTime columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
