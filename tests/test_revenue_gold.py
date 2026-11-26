from decimal import Decimal

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from amsterdam_investment.gold import build_gold_products, write_gold_parquet
from amsterdam_investment.revenue import (
    calculate_annual_gross_revenue,
    eligible_revenue_records,
)


def _silver_record(
    source_name,
    key,
    amount,
    unit,
    *,
    pc4="1018",
    status="true",
    location_scope="amsterdam",
    duplicate_count=1,
):
    return {
        "source_name": source_name,
        "source_listing_key": key,
        "revenue_input_amount": amount,
        "revenue_input_unit": unit,
        "currency_code": "EUR",
        "location_scope": location_scope,
        "status": status,
        "pc4": pc4,
        "postcode_source": "normalized" if pc4 else "unknown",
        "postcode_quality": "known" if pc4 else "invalid",
        "quality_flags": [],
        "duplicate_count": duplicate_count,
    }


def test_annual_gross_revenue_uses_source_units():
    assert calculate_annual_gross_revenue(
        Decimal("1000.50"), "EUR_per_month"
    ) == Decimal("12006.00")
    assert calculate_annual_gross_revenue(
        Decimal("125.25"), "EUR_per_night"
    ) == Decimal("45716.25")

    with pytest.raises(ValueError, match="Unsupported revenue input unit"):
        calculate_annual_gross_revenue(Decimal("10"), "EUR_per_week")
    with pytest.raises(ValueError, match="finite positive"):
        calculate_annual_gross_revenue(Decimal("0"), "EUR_per_night")


def test_eligibility_and_gold_grains_reconcile_unknown_postcodes():
    kamernet = [
        _silver_record("kamernet", "active", Decimal("500"), "EUR_per_month"),
        _silver_record(
            "kamernet", "inactive", Decimal("900"), "EUR_per_month", status="false"
        ),
        _silver_record(
            "kamernet", "unknown-status", Decimal("900"), "EUR_per_month",
            status="unknown",
        ),
        _silver_record(
            "kamernet", "outside", Decimal("900"), "EUR_per_month",
            location_scope="non_amsterdam",
        ),
        _silver_record("kamernet", "invalid", None, "EUR_per_month"),
    ]
    airbnb_listing = _silver_record(
        "airbnb",
        "content-hash",
        Decimal("100"),
        "EUR_per_night",
        pc4=None,
        status=None,
        duplicate_count=2,
    )
    airbnb = [
        airbnb_listing,
        dict(airbnb_listing),
        _silver_record(
            "airbnb", "outside", Decimal("200"), "EUR_per_night",
            location_scope="non_amsterdam",
        ),
        _silver_record("airbnb", "invalid", Decimal("0"), "EUR_per_night"),
    ]

    products = build_gold_products(kamernet, airbnb)

    assert len(eligible_revenue_records("kamernet", kamernet)) == 1
    assert len(eligible_revenue_records("airbnb", airbnb)) == 2
    assert len(products["property_revenue"]) == 2
    properties = {
        (row["source_name"], row["source_listing_key"]): row
        for row in products["property_revenue"]
    }
    assert properties[("kamernet", "active")]["annual_gross_revenue_eur"] == 6000
    assert properties[("airbnb", "content-hash")]["annual_gross_revenue_eur"] == 36500
    assert properties[("airbnb", "content-hash")]["duplicate_count"] == 2
    assert properties[("airbnb", "content-hash")]["pc4"] is None

    assert products["postcode_revenue"] == [{
        "source_name": "kamernet",
        "pc4": "1018",
        "property_count": 1,
        "annual_gross_revenue_eur": Decimal("6000"),
    }]
    assert products["source_comparison"][0]["higher_revenue_source"] == "kamernet"
    assert products["reconciliation"]["airbnb"] == {
        "property_count": 1,
        "duplicate_source_rows_collapsed": 1,
        "property_revenue_total_eur": Decimal("36500"),
        "known_pc4_property_count": 0,
        "known_pc4_revenue_total_eur": Decimal("0"),
        "unknown_pc4_property_count": 1,
        "unknown_pc4_revenue_total_eur": Decimal("36500"),
    }


def test_conflicting_listing_key_is_rejected():
    records = [
        _silver_record("kamernet", "same-key", Decimal("500"), "EUR_per_month"),
        _silver_record("kamernet", "same-key", Decimal("600"), "EUR_per_month"),
    ]
    with pytest.raises(ValueError, match="Conflicting eligible kamernet records"):
        build_gold_products(records, [])


def test_source_pc4_ranks_use_competition_ranking_and_independent_totals():
    kamernet = [
        _silver_record("kamernet", "k-1018", Decimal("500"), "EUR_per_month", pc4="1018"),
        _silver_record("kamernet", "k-1018-b", Decimal("500"), "EUR_per_month", pc4="1018"),
        _silver_record("kamernet", "k-1019", Decimal("1000"), "EUR_per_month", pc4="1019"),
        _silver_record("kamernet", "k-1020", Decimal("250"), "EUR_per_month", pc4="1020"),
    ]
    airbnb = [
        _silver_record("airbnb", "a-1018", Decimal("100"), "EUR_per_night", pc4="1018", status=None),
        _silver_record("airbnb", "a-1020", Decimal("100"), "EUR_per_night", pc4="1020", status=None),
    ]

    comparison = {
        row["pc4"]: row
        for row in build_gold_products(kamernet, airbnb)["source_comparison"]
    }

    assert comparison["1019"]["kamernet_pc4_rank"] == 1
    assert comparison["1018"]["kamernet_pc4_rank"] == 1
    assert comparison["1020"]["kamernet_pc4_rank"] == 3
    assert comparison["1018"]["airbnb_pc4_rank"] == 1
    assert comparison["1020"]["airbnb_pc4_rank"] == 1

    no_airbnb = build_gold_products(
        [_silver_record("kamernet", "k", Decimal("500"), "EUR_per_month", pc4="1018")],
        [],
    )["source_comparison"][0]
    assert no_airbnb["airbnb_property_count"] == 0
    assert no_airbnb["airbnb_annual_gross_revenue_eur"] == Decimal("0")
    assert no_airbnb["airbnb_pc4_rank"] is None


def test_parquet_exports_have_typed_schemas_and_round_trip(tmp_path):
    products = build_gold_products(
        [_silver_record("kamernet", "listing", Decimal("500.25"), "EUR_per_month")],
        [_silver_record(
            "airbnb", "hash", Decimal("120.50"), "EUR_per_night", pc4="1018",
            status=None,
        )],
    )

    paths = write_gold_parquet(products, tmp_path)

    assert set(paths) == {"property_revenue", "postcode_revenue", "source_comparison"}
    property_table = pq.read_table(paths["property_revenue"])
    assert pa.types.is_decimal(property_table.schema.field(
        "annual_gross_revenue_eur"
    ).type)
    assert property_table.num_rows == 2
    property_rows = {
        row["source_name"]: row for row in property_table.to_pylist()
    }
    assert property_rows["kamernet"]["annual_gross_revenue_eur"] == Decimal(
        "6003.00"
    )

    postcode_table = pq.read_table(paths["postcode_revenue"])
    assert postcode_table.num_rows == 2
    assert postcode_table.schema.field("property_count").type == pa.int64()
    comparison_table = pq.read_table(paths["source_comparison"])
    assert comparison_table.num_rows == 1
    assert comparison_table.schema.field("kamernet_pc4_rank").type == pa.int64()
    assert comparison_table.schema.field("airbnb_pc4_rank").type == pa.int64()
    comparison = comparison_table.to_pylist()[0]
    assert comparison["airbnb_minus_kamernet_revenue_eur"] == Decimal("37979.50")
    assert comparison["kamernet_pc4_rank"] == 1
    assert comparison["airbnb_pc4_rank"] == 1
