from __future__ import annotations

from collections import Counter
from decimal import Decimal
from typing import Any, Iterable

from shapely.geometry import Point
from shapely.ops import unary_union

from .cleaning import (
    airbnb_content_key,
    normalize_postcode,
    parse_coordinate,
    parse_positive_decimal,
    parse_positive_price,
    point_in_postcode,
)


def clean_kamernet(
    bronze_records: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    silver: list[dict[str, Any]] = []
    seen_ids: Counter[str] = Counter()
    for bronze in bronze_records:
        payload = bronze["source_payload"]
        if bronze["parse_status"] != "parsed" or not isinstance(payload, dict):
            silver.append(
                _base_silver(bronze, {
                    "quality_flags": ["malformed", "rejected"],
                    "rejection_reason": bronze["parse_error"] or "malformed_source_record",
                })
            )
            continue

        source_id = bronze["source_record_id"]
        city = str(payload.get("city", "")).strip()
        canonical_city = city.lower()
        location_scope = "amsterdam" if canonical_city == "amsterdam" else (
            "unknown" if not city else "non_amsterdam"
        )
        status = payload.get("isRoomActive")
        status = str(status).strip().lower() if status is not None else ""
        status = status if status in {"true", "false"} else "unknown"

        rent_original = payload.get("rent")
        rent, rent_error = parse_positive_decimal(rent_original)
        postcode_full, pc4 = normalize_postcode(payload.get("postalCode"))
        postcode_source = "normalized" if pc4 else "unknown"
        postcode_quality = "known" if pc4 else "invalid"

        latitude = parse_coordinate(payload.get("latitude"))
        longitude = parse_coordinate(payload.get("longitude"))
        quality_flags: list[str] = []
        rejection_reason: str | None = None

        if not source_id:
            quality_flags.append("missing_source_id")
            rejection_reason = "missing_source_id"
        if rent_error:
            quality_flags.append(rent_error)
            if rejection_reason is None:
                rejection_reason = rent_error
        if pc4 is None:
            quality_flags.append("unknown_postcode")
        if status == "unknown":
            quality_flags.append("unknown_status")
        if latitude is None or longitude is None:
            quality_flags.append("missing_or_invalid_coordinates")
        if not city:
            quality_flags.append("missing_city")

        seen_ids[source_id or ""] += 1
        if seen_ids[source_id or ""] > 1:
            quality_flags.append("duplicate")

        record = _base_silver(
            bronze,
            {
                "source_listing_key": source_id,
                "city": city,
                "latitude": latitude,
                "longitude": longitude,
                "postcode_full": postcode_full,
                "pc4": pc4,
                "postcode_source": postcode_source,
                "postcode_quality": postcode_quality,
                "location_scope": location_scope,
                "status": status,
                "currency_code": "EUR",
                "revenue_input_amount": rent,
                "revenue_input_unit": "EUR_per_month",
                "bedrooms": None,
                "review_score": None,
                "quality_flags": quality_flags,
                "rejection_reason": rejection_reason,
                "original": {
                    "rent": rent_original,
                    "postalCode": payload.get("postalCode"),
                    "isRoomActive": payload.get("isRoomActive"),
                },
            },
        )
        silver.append(record)
    return silver


def clean_airbnb(
    bronze_records: Iterable[dict[str, Any]],
    postcode_geojson: Any,
    amsterdam_geojson: Any,
) -> list[dict[str, Any]]:
    postcode_polygons = _load_postcode_polygons(postcode_geojson)
    amsterdam_polygons = _load_amsterdam_polygons(amsterdam_geojson)
    amsterdam_shape = unary_union(amsterdam_polygons) if amsterdam_polygons else None
    bronze_list = list(bronze_records)
    postcode_cache: dict[tuple[float | None, float | None], tuple[str | None, str, str]] = {}
    scope_cache: dict[tuple[float | None, float | None], str] = {}

    counts: Counter[str] = Counter(
        airbnb_content_key(record["source_payload"])
        for record in bronze_list
        if isinstance(record["source_payload"], dict)
    )
    silver: list[dict[str, Any]] = []

    for bronze in bronze_list:
        payload = bronze["source_payload"]
        if bronze["parse_status"] != "parsed" or not isinstance(payload, dict):
            silver.append(
                _base_silver(bronze, {
                    "quality_flags": ["malformed", "rejected"],
                    "rejection_reason": bronze["parse_error"] or "malformed_source_record",
                })
            )
            continue

        source_key = airbnb_content_key(payload)
        duplicate_count = counts[source_key]
        latitude = parse_coordinate(payload.get("latitude"))
        longitude = parse_coordinate(payload.get("longitude"))
        raw_postcode = payload.get("zipcode")
        postcode_full, pc4 = normalize_postcode(raw_postcode)
        postcode_source = "normalized" if pc4 and postcode_full else ("normalized" if pc4 else "unknown")
        postcode_quality = "known" if pc4 else "invalid"
        inferred_code: str | None = None

        if pc4 is None:
            postcode_key = (latitude, longitude)
            if postcode_key not in postcode_cache:
                postcode_cache[postcode_key] = point_in_postcode(
                    latitude,
                    longitude,
                    postcode_polygons,
                )
            inferred_code, postcode_quality, postcode_source = postcode_cache[postcode_key]
            if postcode_quality == "known":
                pc4 = inferred_code
                postcode_full = None
                postcode_source = "inferred"

        point_valid = (
            latitude is not None
            and longitude is not None
            and -90 <= latitude <= 90
            and -180 <= longitude <= 180
        )
        if point_valid:
            scope_key = (latitude, longitude)
            if scope_key not in scope_cache:
                scope_cache[scope_key] = (
                    "amsterdam"
                    if amsterdam_shape is not None
                    and amsterdam_shape.contains(Point(longitude, latitude))
                    else "non_amsterdam"
                )
            location_scope = scope_cache[scope_key]
        else:
            location_scope = "unknown"

        price, price_error = parse_positive_price(payload.get("price"))
        bedrooms = _optional_decimal(payload.get("bedrooms"))
        review_score = _optional_decimal(payload.get("review_scores_value"))

        quality_flags: list[str] = []
        rejection_reason: str | None = None
        if postcode_source == "unknown" or postcode_quality in {"ambiguous", "out_of_bounds"}:
            quality_flags.append("unknown_postcode")
        if pc4 is not None and postcode_source == "inferred":
            quality_flags.append("inferred_postcode")
        if duplicate_count > 1:
            quality_flags.append("duplicate")
            quality_flags.append(f"duplicate_count={duplicate_count}")
        if price_error:
            quality_flags.append(price_error)
            rejection_reason = price_error
        if latitude is None or longitude is None:
            quality_flags.append("missing_location")
        if location_scope != "amsterdam":
            quality_flags.append(f"location_{location_scope}")

        record = _base_silver(
            bronze,
            {
                "source_listing_key": source_key,
                "city": "Amsterdam" if location_scope == "amsterdam" else None,
                "latitude": latitude,
                "longitude": longitude,
                "postcode_full": postcode_full,
                "pc4": pc4,
                "postcode_source": postcode_source,
                "postcode_quality": postcode_quality,
                "location_scope": location_scope,
                "status": None,
                "currency_code": "EUR",
                "revenue_input_amount": price,
                "revenue_input_unit": "EUR_per_night",
                "bedrooms": bedrooms,
                "review_score": review_score,
                "quality_flags": quality_flags,
                "rejection_reason": rejection_reason,
                "duplicate_count": duplicate_count,
                "original": {
                    "zipcode": raw_postcode,
                    "price": payload.get("price"),
                    "latitude": payload.get("latitude"),
                    "longitude": payload.get("longitude"),
                },
            },
        )
        silver.append(record)
    return silver


def _load_postcode_polygons(postcode_geojson: Any) -> list[tuple[str, Any]]:
    from .cleaning import load_postcode_polygons
    return load_postcode_polygons(postcode_geojson)


def _load_amsterdam_polygons(amsterdam_geojson: Any) -> list[Any]:
    from .cleaning import load_amsterdam_polygons
    return load_amsterdam_polygons(amsterdam_geojson)


def _optional_decimal(value: Any) -> Decimal | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        amount = Decimal(str(value).strip().replace(",", "."))
        return amount if amount.is_finite() else None
    except Exception:
        return None


def _base_silver(bronze: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    record = {
        "source_listing_key": None,
        "source_name": bronze["source_name"],
        "source_record": {
            "source_payload": bronze["source_payload"],
            "source_path": bronze["source_path"],
            "source_row_number": bronze["source_row_number"],
        },
        "city": None,
        "latitude": None,
        "longitude": None,
        "postcode_full": None,
        "pc4": None,
        "postcode_source": "unknown",
        "postcode_quality": "unknown",
        "location_scope": "unknown",
        "status": None,
        "currency_code": None,
        "revenue_input_amount": None,
        "revenue_input_unit": None,
        "bedrooms": None,
        "review_score": None,
        "quality_flags": [],
        "rejection_reason": None,
        "duplicate_count": 1,
        "ingestion_timestamp": bronze["ingestion_timestamp"],
        "ingestion_batch_id": bronze["ingestion_batch_id"],
        "original": {},
    }
    record.update(updates)
    return record
