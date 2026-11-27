# Databricks notebook source

dbutils.widgets.text("root", "/Workspace/technical_assessment")
dbutils.widgets.text("kamernet_source", "")
dbutils.widgets.text("airbnb_source", "")
dbutils.widgets.text("postcode_geojson", "")
dbutils.widgets.text("amsterdam_geojson", "")
dbutils.widgets.text("output_dir", "")
dbutils.widgets.text("property_table", "amsterdam_property_revenue")
dbutils.widgets.text("postcode_table", "amsterdam_postcode_revenue")
dbutils.widgets.text("comparison_table", "amsterdam_source_comparison")
dbutils.widgets.text("kamernet_bronze_table", "amsterdam_kamernet_bronze")
dbutils.widgets.text("airbnb_bronze_table", "amsterdam_airbnb_bronze")
dbutils.widgets.text("kamernet_silver_table", "amsterdam_kamernet_silver")
dbutils.widgets.text("airbnb_silver_table", "amsterdam_airbnb_silver")
dbutils.widgets.text("quality_table", "amsterdam_pipeline_quality")

root = dbutils.widgets.get("root")
import sys

sys.path.insert(0, f"{root}/src")

from amsterdam_investment.pipeline import (
    PipelineConfig,
    PipelineError,
    run_full_pipeline,
)

overrides = {}
for widget_name in (
    "kamernet_source",
    "airbnb_source",
    "postcode_geojson",
    "amsterdam_geojson",
    "output_dir",
    "property_table",
    "postcode_table",
    "comparison_table",
    "kamernet_bronze_table",
    "airbnb_bronze_table",
    "kamernet_silver_table",
    "airbnb_silver_table",
    "quality_table",
):
    value = dbutils.widgets.get(widget_name)
    if value:
        overrides[widget_name] = value

config = PipelineConfig.for_root(root, **overrides)
try:
    detected_run_id = dbutils.notebook.entry_point.getDbutils().notebook().getContext().tags().get("jobRunId").getOrElse(None)
except Exception:
    detected_run_id = None
if detected_run_id:
    from dataclasses import replace
    config = replace(config, run_id=str(detected_run_id))

try:
    result = run_full_pipeline(root, config=config)
except PipelineError as exc:
    raise RuntimeError(str(exc)) from exc

table_products = (
    ("property_revenue", config.property_table),
    ("postcode_revenue", config.postcode_table),
    ("source_comparison", config.comparison_table),
)
for product_name, table_name in table_products:
    spark.createDataFrame(result[product_name]).write.format("delta").mode(
        "overwrite"
    ).saveAsTable(table_name)


def flatten_bronze(records):
    import json

    return [{
        "source_name": record["source_name"],
        "source_record_id": record["source_record_id"],
        "source_payload": json.dumps(record["source_payload"], ensure_ascii=False),
        "source_path": record["source_path"],
        "source_row_number": record["source_row_number"],
        "ingestion_timestamp": record["ingestion_timestamp"],
        "ingestion_batch_id": record["ingestion_batch_id"],
        "parse_status": record["parse_status"],
        "parse_error": record["parse_error"],
    } for record in records]


def flatten_silver(records):
    import json

    return [{
        "source_name": record["source_name"],
        "source_listing_key": record["source_listing_key"],
        "source_payload": json.dumps(record["source_record"]["source_payload"], ensure_ascii=False),
        "source_path": record["source_record"]["source_path"],
        "source_row_number": record["source_record"]["source_row_number"],
        "city": record["city"],
        "latitude": record["latitude"],
        "longitude": record["longitude"],
        "postcode_full": record["postcode_full"],
        "pc4": record["pc4"],
        "postcode_source": record["postcode_source"],
        "postcode_quality": record["postcode_quality"],
        "location_scope": record["location_scope"],
        "status": record["status"],
        "currency_code": record["currency_code"],
        "revenue_input_amount": str(record["revenue_input_amount"]) if record["revenue_input_amount"] is not None else None,
        "revenue_input_unit": record["revenue_input_unit"],
        "bedrooms": str(record["bedrooms"]) if record["bedrooms"] is not None else None,
        "review_score": str(record["review_score"]) if record["review_score"] is not None else None,
        "quality_flags": json.dumps(record["quality_flags"]),
        "rejection_reason": record["rejection_reason"],
        "duplicate_count": record["duplicate_count"],
        "ingestion_timestamp": record["ingestion_timestamp"],
        "ingestion_batch_id": record["ingestion_batch_id"],
        "original": json.dumps(record["original"], ensure_ascii=False),
    } for record in records]


from pyspark.sql.types import DoubleType, LongType, StringType, StructField, StructType

bronze_schema = StructType([
    StructField("source_name", StringType()),
    StructField("source_record_id", StringType()),
    StructField("source_payload", StringType()),
    StructField("source_path", StringType()),
    StructField("source_row_number", LongType()),
    StructField("ingestion_timestamp", StringType()),
    StructField("ingestion_batch_id", StringType()),
    StructField("parse_status", StringType()),
    StructField("parse_error", StringType()),
])
silver_schema = StructType([
    StructField("source_name", StringType()),
    StructField("source_listing_key", StringType()),
    StructField("source_payload", StringType()),
    StructField("source_path", StringType()),
    StructField("source_row_number", LongType()),
    StructField("city", StringType()),
    StructField("latitude", DoubleType()),
    StructField("longitude", DoubleType()),
    StructField("postcode_full", StringType()),
    StructField("pc4", StringType()),
    StructField("postcode_source", StringType()),
    StructField("postcode_quality", StringType()),
    StructField("location_scope", StringType()),
    StructField("status", StringType()),
    StructField("currency_code", StringType()),
    StructField("revenue_input_amount", StringType()),
    StructField("revenue_input_unit", StringType()),
    StructField("bedrooms", StringType()),
    StructField("review_score", StringType()),
    StructField("quality_flags", StringType()),
    StructField("rejection_reason", StringType()),
    StructField("duplicate_count", LongType()),
    StructField("ingestion_timestamp", StringType()),
    StructField("ingestion_batch_id", StringType()),
    StructField("original", StringType()),
])


medallion_products = (
    ("kamernet_bronze", "kamernet_bronze_table", "kamernet_bronze"),
    ("airbnb_bronze", "airbnb_bronze_table", "airbnb_bronze"),
    ("kamernet_silver", "kamernet_silver_table", "kamernet_silver"),
    ("airbnb_silver", "airbnb_silver_table", "airbnb_silver"),
)
for source_name, table_config_name, result_name in medallion_products:
    is_bronze = source_name.endswith("bronze")
    records = (
        flatten_bronze(result[result_name])
        if is_bronze
        else flatten_silver(result[result_name])
    )
    schema = bronze_schema if is_bronze else silver_schema
    spark.createDataFrame(records, schema=schema).write.format("delta").mode(
        "overwrite"
    ).saveAsTable(getattr(config, table_config_name))

quality_records = [
    {
        "source_name": source_name,
        "input_count": report["input_count"],
        "rejected_count": report["rejected_count"],
        "rejection_counts": str(report["rejection_counts"]),
        "quality_flag_counts": str(report["quality_flag_counts"]),
    }
    for source_name, report in result["quality"].items()
]
spark.createDataFrame(quality_records).write.format("delta").mode(
    "overwrite"
).saveAsTable(config.quality_table)

print({
    "bronze_and_silver_tables": {
        "kamernet_bronze": config.kamernet_bronze_table,
        "airbnb_bronze": config.airbnb_bronze_table,
        "kamernet_silver": config.kamernet_silver_table,
        "airbnb_silver": config.airbnb_silver_table,
    },
    "quality_table": config.quality_table,
    "property_table": config.property_table,
    "postcode_table": config.postcode_table,
    "comparison_table": config.comparison_table,
    "output_paths": {name: str(path) for name, path in result["output_paths"].items()},
    "reconciliation": result["reconciliation"],
    "quality": result["quality"],
})
