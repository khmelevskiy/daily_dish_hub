from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from app.core.config import settings


_ZERO = Decimal("0.00")
_CENTS = Decimal("0.01")


def to_decimal(value: Decimal | float | int | str | None, default: Decimal = _ZERO) -> Decimal:
    """Convert input to Decimal rounded to currency precision."""
    if value is None:
        return default
    if isinstance(value, Decimal):
        candidate = value
    else:
        try:
            candidate = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            return default
    try:
        return candidate.quantize(_CENTS, rounding=ROUND_HALF_UP)
    except InvalidOperation:
        return default


def normalize_price_in_dict(d: dict, key: str = "price") -> dict:
    if key in d:
        d[key] = to_decimal(value=d.get(key))

    return d


def normalize_price_in_list(items: list[dict], key: str = "price") -> list[dict]:
    for it in items:
        normalize_price_in_dict(d=it, key=key)

    return items


def decimal_to_float(value: Decimal | float | int | str | None, default: float = 0.0) -> float:
    """Helper for JSON serialization: convert numeric input to float safely."""
    return float(to_decimal(value=value, default=Decimal(str(default))))


def format_price(amount: Decimal | float | int | str) -> str:
    """Format amount using Decimal for currency precision."""
    value = to_decimal(value=amount)

    return f"{value:.2f} {settings.currency_symbol}"
