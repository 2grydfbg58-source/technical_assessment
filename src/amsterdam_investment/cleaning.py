from __future__ import annotations

import hashlib
import json
import re
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable

from shapely.geometry import Point, shape
from shapely.strtree import STRtree


POSTCODE_FULL = re.compile(r"^[0-9]{4}[A-Z]{2}$")
POSTCODE_PC4 = re.compile(r"^[0-9]{4}$")
_POSTCODE_TREE_CACHE: dict[int, tuple[list[tuple[str, Any]], STRtree]] = {}


def normalize_postcode(value: Any) -> tuple[str | None, str | None]:
    if value is None:
        return None, None
    compact = re.sub(r"[^A-Za-z0-9]", "", str(value)).upper()
    if POSTCODE_FULL.fullmatch(compact):
        return f"{compact[:4]} {compact[4:]}", compact[:4]
    if POSTCODE_PC4.fullmatch(compact):
        return None, compact
    return None, None


def parse_positive_decimal(value: Any) -> tuple[Decimal | None, str | None]:
    if value is None:
        return None, "missing_rent"
    text = str(value).strip()
    if not text:
        return None, "missing_rent"
    match = re.search(r"(\d+(?:[.,]\d+)?)", text)
    if not match:
        return None, "invalid_rent_format"
    try:
        amount = Decimal(match.group(1).replace(",", "."))
    except InvalidOperation:
        return None, "invalid_rent_format"
    if amount <= 0:
        return None, "non_positive_rent"
    return amount, None


def parse_positive_price(value: Any) -> tuple[Decimal | None, str | None]:
    if value is None or str(value).strip() == "":
        return None, "missing_price"
    try:
        amount = Decimal(str(value).strip().replace(",", "."))
    except InvalidOperation:
        return None, "invalid_price_format"
    if not amount.is_finite():
        return None, "invalid_price_format"
    if amount <= 0:
        return None, "non_positive_price"
    return amount, None


def parse_coordinate(value: Any) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return parsed if __import__("math").isfinite(parsed) else None


def load_postcode_polygons(postcode_geojson: Any) -> list[tuple[str, Any]]:
    if isinstance(postcode_geojson, (str,)):
        with open(postcode_geojson, encoding="utf-8") as handle:
            postcode_geojson = json.load(handle)
    return [
        (str(feature["properties"]["pc4_code"]).strip(), shape(feature["geometry"]))
        for feature in postcode_geojson["features"]
    ]


def load_amsterdam_polygons(amsterdam_geojson: Any) -> list[Any]:
    if isinstance(amsterdam_geojson, (str,)):
        with open(amsterdam_geojson, encoding="utf-8") as handle:
            amsterdam_geojson = json.load(handle)
    return [shape(feature["geometry"]) for feature in amsterdam_geojson["features"]]


def point_in_postcode(
    latitude: float | None,
    longitude: float | None,
    polygons: list[tuple[str, Any]],
) -> tuple[str | None, str, str]:
    if latitude is None or longitude is None:
        return None, "unknown", "missing_location"
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return None, "unknown", "invalid_coordinates"
    point = Point(longitude, latitude)
    cache_key = id(polygons)
    cached = _POSTCODE_TREE_CACHE.get(cache_key)
    if cached is None:
        tree = STRtree([polygon for _, polygon in polygons])
        cached = (polygons, tree)
        _POSTCODE_TREE_CACHE[cache_key] = cached
    _, tree = cached
    candidate_indexes = tree.query(point)
    hits = sorted({
        polygons[index][0]
        for index in candidate_indexes
        if polygons[index][1].contains(point)
    })
    if len(hits) == 1:
        return hits[0], "known", "inferred"
    if not hits:
        return None, "out_of_bounds", "out_of_bounds"
    return None, "ambiguous", "ambiguous_postcode"


def _decimal_optional(value: Any) -> Decimal | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        parsed = Decimal(str(value).strip().replace(",", "."))
        return parsed if parsed.is_finite() else None
    except InvalidOperation:
        return None


def airbnb_content_key(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
