from __future__ import annotations
from app.config import settings


def normalize_to_usd(value: float | None, currency: str) -> float | None:
    """Convert valuation to USD millions.

    KRW values in the data are in 억 (hundred million won).
    USD values are already in millions.
    """
    if value is None:
        return None
    if currency == "USD":
        return value  # Already in millions
    if currency == "KRW":
        # value is in 억 (hundred million KRW)
        # 1억 KRW = 100,000,000 KRW
        krw_total = value * 100_000_000
        usd = krw_total / settings.KRW_TO_USD_RATE
        return round(usd / 1_000_000, 2)  # Convert to millions
    return value
