#!/usr/bin/env python3
"""Small, fast unit tests for utility helpers.

These tests do not require a running server.
"""

import sys
from decimal import Decimal

import pytest


def test_sanitize_filename_for_header_basic():
    from app.api.public_images import _sanitize_filename_for_header

    assert _sanitize_filename_for_header("") == "file"
    assert _sanitize_filename_for_header("normal.jpg") == "normal.jpg"
    # Control chars and path separators are removed/replaced
    assert _sanitize_filename_for_header("..\\evil/\r\nname.png") == "evil_name.png"
    # Quotes and non-ASCII become safe
    assert _sanitize_filename_for_header("\"soup' .png") == "____.png" or _sanitize_filename_for_header(
        "\"soup' .png"
    ).endswith(".png")
    # Hidden files are normalized
    assert _sanitize_filename_for_header(".env") == "env"


def test_sanitize_filename_truncation_preserves_extension():
    from app.api.public_images import _sanitize_filename_for_header

    name = "a" * 120 + ".jpeg"
    out = _sanitize_filename_for_header(name, max_len=30)
    assert out.endswith(".jpeg")
    assert len(out) <= 30


def test_format_price_uses_currency_symbol(monkeypatch):
    from app.core.config import settings
    from app.services.formatting import format_price

    # Ensure stable symbol for test
    old = settings.currency_symbol
    try:
        monkeypatch.setattr(settings, "currency_symbol", "$", raising=False)
        assert format_price(12.3) == "12.30 $"
        assert format_price("7") == "7.00 $"
        # Invalid input falls back to 0.00
        assert format_price(None) == "0.00 $"  # type: ignore
    finally:
        # Restore symbol to avoid side-effects
        monkeypatch.setattr(settings, "currency_symbol", old, raising=False)


def test_user_create_schema_requires_long_password():
    from pydantic import ValidationError

    from app.schemas.auth import UserCreate

    # Build passwords at runtime to avoid literal secrets in source
    short_pw = "Short7"  # pragma: allowlist secret
    long_pw = "LongPass9"  # pragma: allowlist secret

    with pytest.raises(ValidationError):
        UserCreate(username="tester", password=short_pw, is_admin=False)

    valid = UserCreate(username="tester", password=long_pw, is_admin=False)
    assert valid.password == long_pw


def test_item_price_column_uses_decimal():
    from app.models.item import Item

    price_column = Item.__table__.c.price
    assert price_column.type.python_type is Decimal


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
