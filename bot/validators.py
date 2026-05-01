"""Input validation for CLI arguments before they reach the API layer."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_LIMIT"}


class ValidationError(ValueError):
    """Raised when CLI input fails validation."""


def normalize_symbol(symbol: str) -> str:
    if not symbol or not symbol.strip():
        raise ValidationError("symbol must be a non-empty string (e.g. BTCUSDT)")
    s = symbol.strip().upper()
    if not s.isalnum():
        raise ValidationError(f"symbol '{symbol}' must be alphanumeric")
    if len(s) < 5:
        raise ValidationError(f"symbol '{symbol}' looks too short")
    return s


def normalize_side(side: str) -> str:
    s = (side or "").strip().upper()
    if s not in VALID_SIDES:
        raise ValidationError(f"side must be one of {sorted(VALID_SIDES)}, got '{side}'")
    return s


def normalize_order_type(order_type: str) -> str:
    t = (order_type or "").strip().upper().replace("-", "_")
    if t not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"order type must be one of {sorted(VALID_ORDER_TYPES)}, got '{order_type}'"
        )
    return t


def positive_decimal(value, field: str) -> Decimal:
    if value is None:
        raise ValidationError(f"{field} is required")
    try:
        d = Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise ValidationError(f"{field} must be a number, got '{value}'")
    if d <= 0:
        raise ValidationError(f"{field} must be greater than 0, got {d}")
    return d


def require_price_for_limit(order_type: str, price) -> Decimal | None:
    """LIMIT and STOP_LIMIT both require a price; MARKET must not have one."""
    if order_type in {"LIMIT", "STOP_LIMIT"}:
        return positive_decimal(price, "price")
    if price is not None:
        raise ValidationError("price must not be set for MARKET orders")
    return None


def require_stop_price(order_type: str, stop_price) -> Decimal | None:
    if order_type == "STOP_LIMIT":
        return positive_decimal(stop_price, "stop_price")
    if stop_price is not None:
        raise ValidationError("stop_price is only valid for STOP_LIMIT orders")
    return None
