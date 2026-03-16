from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation

from django import template
from django.utils import timezone


register = template.Library()
WEEKDAY_NAMES = [
    "Thứ hai",
    "Thứ ba",
    "Thứ tư",
    "Thứ năm",
    "Thứ sáu",
    "Thứ bảy",
    "Chủ nhật",
]


@register.filter
def vnd(value):
    if value in (None, ""):
        return "-"

    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return value

    rounded = int(amount.quantize(Decimal("1")))
    formatted = f"{rounded:,}".replace(",", ".")
    return f"{formatted} VNĐ"


@register.filter
def duration_vi(value):
    if value in (None, ""):
        return "-"

    if not isinstance(value, timedelta):
        return value

    total_minutes = int(value.total_seconds() // 60)
    if total_minutes <= 0:
        return "0 phút"

    hours, minutes = divmod(total_minutes, 60)
    parts = []
    if hours:
        parts.append(f"{hours} giờ")
    if minutes:
        parts.append(f"{minutes} phút")
    return " ".join(parts)


def _normalize_datetime(value):
    if isinstance(value, datetime):
        return timezone.localtime(value) if timezone.is_aware(value) else value
    return None


def _normalize_date(value):
    if isinstance(value, datetime):
        normalized = _normalize_datetime(value)
        return normalized.date() if normalized else None
    if isinstance(value, date):
        return value
    return None


def _normalize_time(value):
    if isinstance(value, datetime):
        normalized = _normalize_datetime(value)
        return normalized.time().replace(tzinfo=None) if normalized else None
    if isinstance(value, time):
        return value.replace(tzinfo=None) if value.tzinfo else value
    return None


@register.filter
def vi_date(value):
    normalized = _normalize_date(value)
    if not normalized:
        return "-"
    return normalized.strftime("%d/%m/%Y")


@register.filter
def vi_time(value):
    normalized = _normalize_time(value)
    if not normalized:
        return "-"
    return normalized.strftime("%H:%M")


@register.filter
def vi_date_long(value):
    normalized = _normalize_date(value)
    if not normalized:
        return "-"
    weekday = WEEKDAY_NAMES[normalized.weekday()]
    return f"{weekday}, {normalized.strftime('%d/%m/%Y')}"


@register.filter
def vi_datetime(value):
    normalized = _normalize_datetime(value)
    if not normalized:
        return "-"
    return normalized.strftime("%d/%m/%Y %H:%M")
