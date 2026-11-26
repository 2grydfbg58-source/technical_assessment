from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable

import pyarrow as pa
import pyarrow.parquet as pq

from .revenue import calculate_annual_gross_revenue, eligible_revenue_records


_MONEY_FIELDS = (
    "annual_gross_revenue_eur",
    "revenue_input_amount_eur",
)


def build_gold_products(
    kamernet_silver: Iterable[dict[str, Any]],
    airbnb_silver: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    properties = _build_property_revenue(kamernet_silver, airbnb_silver)
    postcode_revenue, source_comparison = _build_postcode_products(properties)
    reconciliation = _build_reconciliation(properties)
    return {
        "property_revenue": properties,
        "postcode_revenue": postcode_revenue,
        "source_comparison": source_comparison,
        "reconciliation": reconciliation,
    }


def _build_property_revenue(
    kamernet_silver: Iterable[dict[str, Any]],
    airbnb_silver: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    properties: list[dict[str, Any]] = []
    for source_name, records in (
        ("kamernet", kamernet_silver),
        ("airbnb", airbnb_silver),
    ):
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in eligible_revenue_records(source_name, records):
            grouped[record["source_listing_key"]].append(record)

        for listing_key, duplicates in sorted(grouped.items()):
            representative = duplicates[0]
            identity = _property_identity(representative)
            if any(_property_identity(record) != identity for record in duplicates[1:]):
                raise ValueError(
                    f"Conflicting eligible {source_name} records share listing key "
                    f"{listing_key}"
                )
            input_amount = representative["revenue_input_amount"]
            properties.append(
                {
                    "source_name": source_name,
                    "source_listing_key": listing_key,
                    "pc4": representative.get("pc4"),
                    "annual_gross_revenue_eur": calculate_annual_gross_revenue(
                        input_amount,
                        representative["revenue_input_unit"],
                    ),
                    "revenue_input_amount_eur": input_amount,
                    "revenue_input_unit": representative["revenue_input_unit"],
                    "currency_code": "EUR",
                    "location_scope": representative["location_scope"],
                    "status": representative.get("status"),
                    "postcode_source": representative.get("postcode_source", "unknown"),
                    "postcode_quality": representative.get(
                        "postcode_quality", "unknown"
                    ),
                    "quality_flags": sorted({
                        flag
                        for record in duplicates
                        for flag in record.get("quality_flags", [])
                    }),
                    "duplicate_count": max(
                        len(duplicates),
                        max(
                            int(record.get("duplicate_count", 1))
                            for record in duplicates
                        ),
                    ),
                }
            )
    return sorted(
        properties,
        key=lambda record: (record["source_name"], record["source_listing_key"]),
    )


def _property_identity(record: dict[str, Any]) -> tuple[Any, ...]:
    return (
        record.get("revenue_input_amount"),
        record.get("revenue_input_unit"),
        record.get("currency_code"),
        record.get("location_scope"),
        record.get("status"),
        record.get("pc4"),
    )


def _build_postcode_products(
    properties: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    totals: dict[tuple[str, str], dict[str, Any]] = {}
    for record in properties:
        pc4 = record["pc4"]
        if not pc4:
            continue
        key = (record["source_name"], pc4)
        if key not in totals:
            totals[key] = {"property_count": 0, "annual_gross_revenue_eur": Decimal(0)}
        totals[key]["property_count"] += 1
        totals[key]["annual_gross_revenue_eur"] += record[
            "annual_gross_revenue_eur"
        ]

    postcode_revenue = [
        {
            "source_name": source_name,
            "pc4": pc4,
            "property_count": values["property_count"],
            "annual_gross_revenue_eur": values["annual_gross_revenue_eur"],
        }
        for (source_name, pc4), values in sorted(totals.items())
    ]

    by_pc4: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for record in postcode_revenue:
        by_pc4[record["pc4"]][record["source_name"]] = record

    kamernet_ranks = _competition_ranks(postcode_revenue, "kamernet")
    airbnb_ranks = _competition_ranks(postcode_revenue, "airbnb")

    source_comparison = []
    for pc4, sources in sorted(by_pc4.items()):
        kamernet = sources.get("kamernet", {})
        airbnb = sources.get("airbnb", {})
        kamernet_total = kamernet.get("annual_gross_revenue_eur", Decimal(0))
        airbnb_total = airbnb.get("annual_gross_revenue_eur", Decimal(0))
        source_comparison.append(
            {
                "pc4": pc4,
                "kamernet_property_count": kamernet.get("property_count", 0),
                "airbnb_property_count": airbnb.get("property_count", 0),
                "kamernet_annual_gross_revenue_eur": kamernet_total,
                "airbnb_annual_gross_revenue_eur": airbnb_total,
                "airbnb_minus_kamernet_revenue_eur": airbnb_total - kamernet_total,
                "higher_revenue_source": (
                    "tie"
                    if airbnb_total == kamernet_total
                    else "airbnb"
                    if airbnb_total > kamernet_total
                    else "kamernet"
                ),
                "kamernet_pc4_rank": kamernet_ranks.get(pc4),
                "airbnb_pc4_rank": airbnb_ranks.get(pc4),
            }
        )
    return postcode_revenue, source_comparison


def _competition_ranks(
    postcode_revenue: list[dict[str, Any]],
    source_name: str,
) -> dict[str, int]:
    totals = sorted(
        (
            (
                record["pc4"],
                record["annual_gross_revenue_eur"],
            )
            for record in postcode_revenue
            if record["source_name"] == source_name
        ),
        key=lambda item: (-item[1], item[0]),
    )

    ranks: dict[str, int] = {}
    previous_total: Decimal | None = None
    previous_rank = 0
    for position, (pc4, total) in enumerate(totals, start=1):
        if previous_total is None or total != previous_total:
            previous_rank = position
            previous_total = total
        ranks[pc4] = previous_rank
    return ranks


def _build_reconciliation(
    properties: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    reconciliation: dict[str, dict[str, Any]] = {}
    for source_name in ("kamernet", "airbnb"):
        source_properties = [
            record for record in properties if record["source_name"] == source_name
        ]
        known_pc4 = [record for record in source_properties if record["pc4"]]
        reconciliation[source_name] = {
            "property_count": len(source_properties),
            "duplicate_source_rows_collapsed": sum(
                record["duplicate_count"] - 1 for record in source_properties
            ),
            "property_revenue_total_eur": sum(
                (record["annual_gross_revenue_eur"] for record in source_properties),
                Decimal(0),
            ),
            "known_pc4_property_count": len(known_pc4),
            "known_pc4_revenue_total_eur": sum(
                (record["annual_gross_revenue_eur"] for record in known_pc4),
                Decimal(0),
            ),
            "unknown_pc4_property_count": len(source_properties) - len(known_pc4),
            "unknown_pc4_revenue_total_eur": sum(
                (
                    record["annual_gross_revenue_eur"]
                    for record in source_properties
                    if not record["pc4"]
                ),
                Decimal(0),
            ),
        }
    return reconciliation


def write_gold_parquet(
    products: dict[str, Any],
    output_dir: str | Path,
) -> dict[str, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    decimal_scale = _decimal_scale(products)
    decimal_type = pa.decimal128(38, decimal_scale)
    schemas = {
        "property_revenue": pa.schema([
            ("source_name", pa.string()),
            ("source_listing_key", pa.string()),
            ("pc4", pa.string()),
            ("annual_gross_revenue_eur", decimal_type),
            ("revenue_input_amount_eur", decimal_type),
            ("revenue_input_unit", pa.string()),
            ("currency_code", pa.string()),
            ("location_scope", pa.string()),
            ("status", pa.string()),
            ("postcode_source", pa.string()),
            ("postcode_quality", pa.string()),
            ("quality_flags", pa.list_(pa.string())),
            ("duplicate_count", pa.int64()),
        ]),
        "postcode_revenue": pa.schema([
            ("source_name", pa.string()),
            ("pc4", pa.string()),
            ("property_count", pa.int64()),
            ("annual_gross_revenue_eur", decimal_type),
        ]),
        "source_comparison": pa.schema([
            ("pc4", pa.string()),
            ("kamernet_property_count", pa.int64()),
            ("airbnb_property_count", pa.int64()),
            ("kamernet_annual_gross_revenue_eur", decimal_type),
            ("airbnb_annual_gross_revenue_eur", decimal_type),
            ("airbnb_minus_kamernet_revenue_eur", decimal_type),
            ("higher_revenue_source", pa.string()),
            ("kamernet_pc4_rank", pa.int64()),
            ("airbnb_pc4_rank", pa.int64()),
        ]),
    }
    paths: dict[str, Path] = {}
    for name, schema in schemas.items():
        path = output_dir / f"{name}.parquet"
        table = pa.Table.from_pylist(products[name], schema=schema)
        pq.write_table(table, path)
        paths[name] = path
    return paths


def _decimal_scale(products: dict[str, Any]) -> int:
    scales = [2]
    for product_name in ("property_revenue", "postcode_revenue", "source_comparison"):
        for record in products[product_name]:
            for field in _MONEY_FIELDS:
                amount = record.get(field)
                if isinstance(amount, Decimal):
                    scales.append(max(0, -amount.as_tuple().exponent))
            if product_name == "source_comparison":
                amount = record["airbnb_minus_kamernet_revenue_eur"]
                scales.append(max(0, -amount.as_tuple().exponent))
    return max(scales)
