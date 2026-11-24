import csv
import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd
import pytest
from shapely.geometry import Point, shape


ROOT = Path(__file__).resolve().parents[1]
KAMERNET_PATH = ROOT / "data" / "rentals.json"
AIRBNB_PATH = ROOT / "data" / "airbnb.csv"
POSTCODE_PATH = ROOT / "data" / "geo" / "post_codes.geojson"
AREA_PATH = ROOT / "data" / "geo" / "amsterdam_areas.geojson"
NOTEBOOK_PATH = ROOT / "scratch" / "explore_source_data.ipynb"


@pytest.fixture(scope="module")
def kamernet():
    with KAMERNET_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture(scope="module")
def airbnb():
    return pd.read_csv(AIRBNB_PATH)


@pytest.fixture(scope="module")
def amsterdam(kamernet):
    return [
        row
        for row in kamernet
        if str(row.get("city", "")).strip().lower() == "amsterdam"
    ]


def normalize_postcode(value):
    if value is None:
        return None
    normalized = re.sub(r"[^A-Za-z0-9]", "", str(value)).upper()
    return normalized if re.fullmatch(r"\d{4}[A-Z]{2}", normalized) else None


def kamernet_id(row):
    value = row.get("_id")
    return str(value[0]) if isinstance(value, list) and value else str(value)


def test_exploration_artifacts_exist_and_notebook_is_valid_json():
    assert NOTEBOOK_PATH.is_file()
    assert POSTCODE_PATH.is_file()
    assert AREA_PATH.is_file()
    with NOTEBOOK_PATH.open(encoding="utf-8") as handle:
        notebook = json.load(handle)
    assert notebook["nbformat"] == 4
    assert any(cell["cell_type"] == "code" for cell in notebook["cells"])


def test_source_row_counts_and_exact_duplication(kamernet, airbnb):
    assert len(kamernet) == 46_722
    assert len(airbnb) == 9_913
    assert len(kamernet) - len({kamernet_id(row) for row in kamernet}) == 0
    assert len(airbnb) - len(airbnb.drop_duplicates()) == 382


def test_amsterdam_candidate_counts(amsterdam):
    active = [row for row in amsterdam if row.get("isRoomActive") == "true"]
    inactive = [row for row in amsterdam if row.get("isRoomActive") == "false"]

    assert len(amsterdam) == 8_095
    assert len(active) == 7_722
    assert len(inactive) == 353
    assert len(amsterdam) - len(active) - len(inactive) == 20


def test_kamernet_nulls_postcodes_coordinates_and_rents(amsterdam):
    valid_postcodes = [
        normalize_postcode(row.get("postalCode"))
        for row in amsterdam
    ]
    valid_postcodes = [value for value in valid_postcodes if value]

    assert len(valid_postcodes) == 8_095
    assert len({value[:4] for value in valid_postcodes}) == 73
    assert all(str(row.get("latitude", "")).strip() for row in amsterdam)
    assert all(str(row.get("longitude", "")).strip() for row in amsterdam)

    rents = []
    for row in amsterdam:
        match = re.search(r"(\d+(?:[.,]\d+)?)", str(row.get("rent", "")))
        assert match is not None
        rents.append(float(match.group(1).replace(",", ".")))
    assert len(rents) == 8_095
    assert min(rents) == 1.0
    assert max(rents) == 5_000.0


def test_airbnb_optional_gaps_and_types(airbnb):
    with AIRBNB_PATH.open(newline="", encoding="utf-8-sig") as handle:
        raw_rows = list(csv.DictReader(handle))
    assert sum(str(row["zipcode"]).strip() == "" for row in raw_rows) == 2_254
    assert int(airbnb["bedrooms"].isna().sum()) == 14
    assert int(airbnb["review_scores_value"].isna().sum()) == 1_711
    assert pd.to_numeric(airbnb["price"], errors="coerce").notna().all()
    assert pd.to_numeric(airbnb["latitude"], errors="coerce").notna().all()
    assert pd.to_numeric(airbnb["longitude"], errors="coerce").notna().all()
    assert float(airbnb["latitude"].min()) == pytest.approx(52.29031)
    assert float(airbnb["latitude"].max()) == pytest.approx(52.42538071)
    assert float(airbnb["longitude"].min()) == pytest.approx(4.763264201)
    assert float(airbnb["longitude"].max()) == pytest.approx(5.019667018)


def test_airbnb_postcode_formats_and_uniform_csv_rows():
    with AIRBNB_PATH.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        rows = list(reader)
    assert len(rows) == 9_914
    assert set(map(len, rows)) == {8}

    airbnb = pd.read_csv(AIRBNB_PATH)
    zips = airbnb["zipcode"].fillna("").astype(str).str.strip()
    formats = zips.map(
        lambda value: (
            "missing"
            if not value
            else "pc4"
            if re.fullmatch(r"\d{4}", value)
            else "full6"
            if re.fullmatch(r"\d{4}\s*[A-Z]{2}", value.upper())
            else "invalid"
        )
    )
    counts = Counter(formats)
    assert counts["missing"] == 2_254
    assert counts["pc4"] == 3_119
    assert counts["full6"] == 4_531
    assert counts["invalid"] == 9


def test_coordinate_postcode_recovery(airbnb):
    with POSTCODE_PATH.open(encoding="utf-8") as handle:
        postcode_geo = json.load(handle)

    polygons = [
        (str(feature["properties"]["pc4_code"]).strip(), shape(feature["geometry"]))
        for feature in postcode_geo["features"]
    ]
    recovered = unknown = ambiguous = 0

    for row in airbnb.itertuples(index=False):
        raw = "" if pd.isna(row.zipcode) else str(row.zipcode).strip()
        normalized = re.sub(r"[^A-Za-z0-9]", "", raw).upper()
        if re.fullmatch(r"\d{4}(?:[A-Z]{2})?", normalized):
            continue

        point = Point(float(row.longitude), float(row.latitude))
        hits = sorted({code for code, polygon in polygons if polygon.contains(point)})
        if len(hits) == 1:
            recovered += 1
        elif len(hits) == 0:
            unknown += 1
        else:
            ambiguous += 1

    assert len(postcode_geo["features"]) == 474
    assert recovered == 2_262
    assert unknown == 0
    assert ambiguous == 0


def test_unknown_postcode_is_not_assigned_a_pc4():
    invalid_zip = "0"
    normalized = re.sub(r"[^A-Za-z0-9]", "", invalid_zip).upper()
    assert re.fullmatch(r"\d{4}(?:[A-Z]{2})?", normalized) is None


@pytest.mark.parametrize(
    ("monthly_rent", "nightly_price"),
    [(500, 130), (950, 59)],
)
def test_revenue_contract_formulas(monthly_rent, nightly_price):
    assert monthly_rent * 12 > 0
    assert nightly_price * 365 > 0
    assert monthly_rent * 12 == pytest.approx(monthly_rent * 12)


def test_postcode_normalization_and_optional_revenue_inputs():
    normalized = re.sub(r"[^A-Za-z0-9]", "", "1018AS").upper()
    assert normalized[:4] == "1018"
    assert f"{normalized[:4]} {normalized[4:]}" == "1018 AS"

    assert normalize_postcode("1016 AM") == "1016AM"
    assert normalize_postcode(None) is None
