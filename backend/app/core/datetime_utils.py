from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo
from app.core.config import settings


def get_clinic_timezone() -> ZoneInfo:
    """Returns the configured clinic timezone object (default: Asia/Kolkata)."""
    return ZoneInfo(settings.CLINIC_TIMEZONE)


def slot_to_utc_datetime(slot_date: date, slot_time: time) -> datetime:
    """
    Converts a clinic local slot date and time (Asia/Kolkata / IST) into
    the exact timezone-aware UTC instant for PostgreSQL storage.

    Example:
        slot_date = 2026-11-11
        slot_time = 16:00:00 (04:00 PM IST)
        -> returns 2026-11-11 10:30:00+00:00 (10:30 AM UTC)
    """
    clinic_tz = get_clinic_timezone()
    local_dt = datetime.combine(slot_date, slot_time).replace(tzinfo=clinic_tz)
    return local_dt.astimezone(timezone.utc)


def utc_to_clinic_datetime(dt: datetime) -> datetime:
    """
    Converts a timezone-aware UTC datetime into clinic local datetime (Asia/Kolkata).
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(get_clinic_timezone())


def ensure_utc(dt: datetime) -> datetime:
    """
    Ensures a datetime is timezone-aware and normalized to UTC.
    If naive, explicitly attaches UTC. If timezone-aware, converts to UTC.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

