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
):
    value = dbutils.widgets.get(widget_name)
    if value:
        overrides[widget_name] = value

config = PipelineConfig.for_root(root, **overrides)

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

print({
    "property_table": config.property_table,
    "postcode_table": config.postcode_table,
    "comparison_table": config.comparison_table,
    "output_paths": {name: str(path) for name, path in result["output_paths"].items()},
    "reconciliation": result["reconciliation"],
})
