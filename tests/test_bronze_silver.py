import csv
import json
from decimal import Decimal
from pathlib import Path

import pytest
import pyarrow.parquet as pq
from shapely.geometry import Point, Polygon

from amsterdam_investment.cleaning import (
    normalize_postcode,
    parse_positive_decimal,
    parse_positive_price,
    point_in_postcode,
)
from amsterdam_investment.ingestion import ingest_airbnb, ingest_kamernet
from amsterdam_investment.quality import quality_report
from amsterdam_investment.silver import clean_airbnb, clean_kamernet


ROOT = Path(__file__).resolve().parents[1]


def test_kamernet_normalization_and_audit(tmp_path):
    source = tmp_path / "rentals.json"
    source.write_text(json.dumps([
        {"_id": ["abc"], "rent": "€ 500,-", "city": "Amsterdam",
         "postalCode": "1018AS", "isRoomActive": "true",
         "latitude": "52.3", "longitude": "4.9"},
        {"_id": ["old"], "rent": "€ 400,-", "city": "Amsterdam",
         "postalCode": "1018AS", "isRoomActive": "false",
         "latitude": "52.3", "longitude": "4.9"},
        {"_id": ["unknown"], "rent": "€ 400,-", "city": "Amsterdam",
         "postalCode": "1018AS", "isRoomActive": None,
         "latitude": "52.3", "longitude": "4.9"},
    ]), encoding="utf-8")

    bronze = ingest_kamernet(source)
    silver = clean_kamernet(bronze)

    assert bronze[0]["source_record_id"] == "abc"
    assert silver[0]["source_listing_key"] == "abc"
    assert silver[0]["pc4"] == "1018"
    assert silver[0]["postcode_full"] == "1018 AS"
    assert silver[0]["postcode_source"] == "normalized"
    assert silver[0]["status"] == "true"
    assert silver[1]["status"] == "false"
    assert silver[2]["status"] == "unknown"
    assert "unknown_status" in silver[2]["quality_flags"]


def test_rent_and_price_validation():
    assert parse_positive_decimal("€ 500,-")[0] == 500
    assert parse_positive_decimal("€ 0,-")[1] == "non_positive_rent"
    assert parse_positive_decimal(None)[1] == "missing_rent"
    assert parse_positive_decimal("unknown")[1] == "invalid_rent_format"
    assert parse_positive_price("130")[0] == 130
    assert parse_positive_price("0")[1] == "non_positive_price"
    assert parse_positive_price("abc")[1] == "invalid_price_format"


def test_postcode_and_polygon_recovery():
    assert normalize_postcode("1016 AM") == ("1016 AM", "1016")
    assert normalize_postcode("1018AS") == ("1018 AS", "1018")
    assert normalize_postcode("0") == (None, None)

    polygon = [(("1053"), Polygon([(4, 52), (5, 52), (5, 53), (4, 53)]))]
    assert point_in_postcode(52.5, 4.5, polygon) == ("1053", "known", "inferred")
    assert point_in_postcode(51, 4, polygon)[1] == "out_of_bounds"


def test_malformed_json_and_csv_are_preserved(tmp_path):
    malformed_json = tmp_path / "bad.json"
    malformed_json.write_text("{not json", encoding="utf-8")
    json_bronze = ingest_kamernet(malformed_json)
    assert json_bronze[0]["parse_status"] == "malformed"
    assert json_bronze[0]["parse_error"]

    malformed_csv = tmp_path / "bad.csv"
    with malformed_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["zipcode", "price", "latitude", "longitude"])
        writer.writerow(["1011", "100", "52.3"])
    csv_bronze = ingest_airbnb(malformed_csv)
    csv_silver = clean_airbnb(
        csv_bronze,
        {"features": []},
        {"features": []},
    )
    assert csv_silver[0]["rejection_reason"] == "missing_price" or csv_silver[0]["rejection_reason"] is None
    assert len(csv_bronze) == 1


def test_airbnb_duplicate_inference_and_quality(tmp_path):
    csv_path = tmp_path / "airbnb.csv"
    fields = ["zipcode", "price", "latitude", "longitude", "bedrooms", "review_scores_value"]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for _ in range(2):
            writer.writerow({
                "zipcode": "", "price": "130", "latitude": "52.378",
                "longitude": "4.874", "bedrooms": "", "review_scores_value": "",
            })

    polygon = Polygon([(4.8, 52.3), (5.0, 52.3), (5.0, 52.5), (4.8, 52.5)])
    postcode_geojson = {"features": [{
        "properties": {"pc4_code": "1053"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[4.8, 52.3], [5.0, 52.3], [5.0, 52.5], [4.8, 52.5], [4.8, 52.3]]],
        },
    }]}
    amsterdam_geojson = {"features": [{
        "properties": {},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[4.7, 52.2], [5.1, 52.2], [5.1, 52.5], [4.7, 52.5], [4.7, 52.2]]],
        },
    }]}

    bronze = ingest_airbnb(csv_path)
    silver = clean_airbnb(bronze, postcode_geojson, amsterdam_geojson)

    assert silver[0]["pc4"] == "1053"
    assert silver[0]["postcode_source"] == "inferred"
    assert silver[0]["location_scope"] == "amsterdam"
    assert silver[0]["bedrooms"] is None
    assert silver[0]["review_score"] is None
    assert silver[0]["duplicate_count"] == 2
    assert "duplicate" in silver[0]["quality_flags"]
    assert "duplicate_count=2" in silver[0]["quality_flags"]
    report = quality_report(silver)
    assert report["input_count"] == 2


def test_full_source_pipeline_smoke(tmp_path):
    pytest.importorskip("amsterdam_investment")
    from amsterdam_investment.pipeline import run_full_pipeline

    result = run_full_pipeline(ROOT, tmp_path / "output")
    assert len(result["kamernet_bronze"]) == 46_722
    assert len(result["airbnb_bronze"]) == 9_913
    assert len(result["kamernet_silver"]) == 46_722
    assert len(result["airbnb_silver"]) == 9_913
    assert set(result["output_paths"]) == {
        "property_revenue",
        "postcode_revenue",
        "source_comparison",
        "kamernet_bronze",
        "airbnb_bronze",
        "kamernet_silver",
        "airbnb_silver",
        "pipeline_quality",
        "quality_rejection_evidence",
        "run_manifest",
    }
    manifest_path = tmp_path / "output" / "run_manifest.json"
    assert manifest_path.is_file()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["source_counts"]["kamernet_bronze"] == 46_722
    assert manifest["source_counts"]["airbnb_bronze"] == 9_913
    assert set(manifest["quality"]) == {"kamernet", "airbnb"}
    assert manifest["started_at"]
    assert manifest["finished_at"]
    assert "kamernet_bronze" in manifest["output_paths"]
    assert "quality_rejection_evidence" in manifest["output_paths"]
    assert pq.read_table(tmp_path / "output" / "kamernet_bronze.parquet").num_rows == 46_722
    assert pq.read_table(tmp_path / "output" / "airbnb_silver.parquet").num_rows == 9_913
    quality_table = pq.read_table(tmp_path / "output" / "pipeline_quality.parquet")
    assert quality_table.num_rows == 2
    assert pq.read_table(
        tmp_path / "output" / "quality_rejection_evidence.parquet"
    ).num_rows >= 1
    property_keys = [
        (row["source_name"], row["source_listing_key"])
        for row in result["property_revenue"]
    ]
    assert len(property_keys) == len(set(property_keys))
    postcode_keys = [
        (row["source_name"], row["pc4"])
        for row in result["postcode_revenue"]
    ]
    assert len(postcode_keys) == len(set(postcode_keys))
    comparison_postcodes = [
        row["pc4"] for row in result["source_comparison"]
    ]
    assert len(comparison_postcodes) == len(set(comparison_postcodes))

    postcode_products = {
        (row["source_name"], row["pc4"]): row
        for row in result["postcode_revenue"]
    }
    for comparison in result["source_comparison"]:
        for source_name in ("kamernet", "airbnb"):
            postcode = postcode_products.get((source_name, comparison["pc4"]), {})
            prefix = f"{source_name}_"
            assert comparison[f"{prefix}property_count"] == postcode.get(
                "property_count", 0
            )
            assert comparison[f"{prefix}annual_gross_revenue_eur"] == postcode.get(
                "annual_gross_revenue_eur", Decimal(0)
            )

    for source_name, reconciliation in result["reconciliation"].items():
        assert (
            reconciliation["property_revenue_total_eur"]
            == reconciliation["known_pc4_revenue_total_eur"]
            + reconciliation["unknown_pc4_revenue_total_eur"]
        ), source_name
        postcode_total = sum(
            (
                row["annual_gross_revenue_eur"]
                for row in result["postcode_revenue"]
                if row["source_name"] == source_name
            ),
            start=Decimal(0),
        )
        assert postcode_total == reconciliation["known_pc4_revenue_total_eur"]
        assert (
            reconciliation["property_count"]
            + reconciliation["duplicate_source_rows_collapsed"]
            == sum(
                record["source_name"] == source_name
                and bool(record.get("source_listing_key"))
                and record.get("revenue_input_amount") is not None
                and record.get("revenue_input_unit") == (
                    "EUR_per_month"
                    if source_name == "kamernet"
                    else "EUR_per_night"
                )
                and record.get("location_scope") == "amsterdam"
                and record.get("currency_code") == "EUR"
                and record.get("revenue_input_amount") > 0
                and (
                    source_name != "kamernet"
                    or record.get("status") == "true"
                )
                for record in result[f"{source_name}_silver"]
            )
        ), source_name
