from __future__ import annotations

from decimal import Decimal
from typing import Any, Iterable


_ANNUALIZATION_FACTORS = {
    "EUR_per_month": Decimal(12),
    "EUR_per_night": Decimal(365),
}


def calculate_annual_gross_revenue(
    amount: Decimal,
    unit: str,
) -> Decimal:
    """Annualize a positive EUR rent input without occupancy or cost adjustments."""
    if not amount.is_finite() or amount <= 0:
        raise ValueError("Revenue input must be a finite positive amount")
    try:
        factor = _ANNUALIZATION_FACTORS[unit]
    except KeyError as exc:
        raise ValueError(f"Unsupported revenue input unit: {unit}") from exc
    return amount * factor


def eligible_revenue_records(
    source_name: str,
    silver_records: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    eligible: list[dict[str, Any]] = []
    expected_unit = {
        "kamernet": "EUR_per_month",
        "airbnb": "EUR_per_night",
    }.get(source_name)
    if expected_unit is None:
        raise ValueError(f"Unsupported revenue source: {source_name}")

    for record in silver_records:
        amount = record.get("revenue_input_amount")
        if (
            record.get("source_name") != source_name
            or not record.get("source_listing_key")
            or record.get("location_scope") != "amsterdam"
            or record.get("currency_code") != "EUR"
            or record.get("revenue_input_unit") != expected_unit
            or not isinstance(amount, Decimal)
            or not amount.is_finite()
            or amount <= 0
        ):
            continue
        if source_name == "kamernet" and record.get("status") != "true":
            continue
        eligible.append(record)
    return eligible
