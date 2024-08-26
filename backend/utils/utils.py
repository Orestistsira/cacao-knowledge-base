from datetime import datetime, timezone


def get_current_datetime_str() -> str:
    return datetime.now(timezone.utc).isoformat("T").replace("+00:00", "Z")