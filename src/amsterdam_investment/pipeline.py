from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .gold import build_gold_products, write_gold_parquet
from .ingestion import ingest_airbnb, ingest_kamernet
from .silver import clean_airbnb, clean_kamernet


@dataclass(frozen=True)
class PipelineConfig:
    kamernet_source: str = "data/rentals.json"
    airbnb_source: str = "data/airbnb.csv"
    postcode_geojson: str = "data/geo/post_codes.geojson"
    amsterdam_geojson: str = "data/geo/amsterdam_areas.geojson"
    output_dir: str = "data/output"
    property_table: str = "amsterdam_property_revenue"
    postcode_table: str = "amsterdam_postcode_revenue"
    comparison_table: str = "amsterdam_source_comparison"
    kamernet_bronze_table: str = "amsterdam_kamernet_bronze"
    airbnb_bronze_table: str = "amsterdam_airbnb_bronze"
    kamernet_silver_table: str = "amsterdam_kamernet_silver"
    airbnb_silver_table: str = "amsterdam_airbnb_silver"
    quality_table: str = "amsterdam_pipeline_quality"
    run_id: str | None = None

    @classmethod
    def for_root(cls, root: str | Path, **overrides: Any) -> "PipelineConfig":
        root = Path(root)
        config = cls(**overrides)
        resolved = {}
        for field_name in (
            "kamernet_source",
            "airbnb_source",
            "postcode_geojson",
            "amsterdam_geojson",
            "output_dir",
        ):
            value = getattr(config, field_name)
            resolved[field_name] = (
                str(Path(value))
                if Path(value).is_absolute()
                else str(root / value)
            )
        return cls(
            **{
                **config.__dict__,
                **resolved,
            }
        )


class PipelineError(RuntimeError):
    def __init__(
        self,
        stage: str,
        source_context: str,
        quality_context: dict[str, Any] | None = None,
    ) -> None:
        self.stage = stage
        self.source_context = source_context
        self.quality_context = quality_context or {}
        context = f"quality={self.quality_context}" if self.quality_context else ""
        super().__init__(
            f"Pipeline failed during {stage}; source context: {source_context}. "
            f"{context}".rstrip()
        )


def run_bronze_silver(
    root: str | Path,
    config: PipelineConfig | None = None,
) -> dict[str, Any]:
    root = Path(root)
    config = config or PipelineConfig.for_root(root)
    kamernet_bronze = ingest_kamernet(Path(config.kamernet_source))
    airbnb_bronze = ingest_airbnb(Path(config.airbnb_source))
    postcode_path = Path(config.postcode_geojson)
    amsterdam_path = Path(config.amsterdam_geojson)

    with postcode_path.open(encoding="utf-8") as handle:
        postcode_geojson = json.load(handle)
    with amsterdam_path.open(encoding="utf-8") as handle:
        amsterdam_geojson = json.load(handle)

    return {
        "kamernet_bronze": kamernet_bronze,
        "airbnb_bronze": airbnb_bronze,
        "kamernet_silver": clean_kamernet(kamernet_bronze),
        "airbnb_silver": clean_airbnb(
            airbnb_bronze,
            postcode_geojson,
            amsterdam_geojson,
        ),
    }


def run_full_pipeline(
    root: str | Path,
    output_dir: str | Path | None = None,
    config: PipelineConfig | None = None,
) -> dict[str, Any]:
    root = Path(root)
    config = config or PipelineConfig.for_root(root)
    if output_dir is not None:
        config = PipelineConfig(
            **{
                **config.__dict__,
                "output_dir": str(output_dir),
            }
        )
    try:
        products = run_bronze_silver(root, config)
    except Exception as exc:
        raise PipelineError(
            "bronze/silver",
            f"kamernet={config.kamernet_source}; airbnb={config.airbnb_source}",
        ) from exc
    try:
        gold = build_gold_products(
            products["kamernet_silver"],
            products["airbnb_silver"],
        )
        from .quality import quality_report

        gold["quality"] = {
            "kamernet": quality_report(products["kamernet_silver"]),
            "airbnb": quality_report(products["airbnb_silver"]),
        }
        output_dir = Path(config.output_dir)
        started_at = datetime.now(timezone.utc).isoformat()
        run_id = config.run_id or os.getenv("DATABRICKS_JOB_RUN_ID")
        gold["output_paths"] = write_gold_parquet(gold, output_dir)
        gold["output_paths"].update(write_medallion_parquet(products, output_dir))
        gold["output_paths"].update(write_quality_parquet(products, gold["quality"], output_dir))
        gold["run_manifest_path"] = write_run_manifest(
            gold,
            products,
            output_dir,
            run_id=run_id,
            started_at=started_at,
        )
        gold["output_paths"]["run_manifest"] = gold["run_manifest_path"]
    except Exception as exc:
        from .quality import quality_report

        quality_context = {
            "kamernet": quality_report(products["kamernet_silver"]),
            "airbnb": quality_report(products["airbnb_silver"]),
        }
        raise PipelineError(
            "gold/export",
            f"kamernet={config.kamernet_source}; airbnb={config.airbnb_source}",
            quality_context,
        ) from exc
    return {**products, **gold}


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str, sort_keys=True)


def write_medallion_parquet(
    products: dict[str, Any],
    output_dir: str | Path,
) -> dict[str, Path]:
    import pyarrow as pa
    import pyarrow.parquet as pq

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    bronze_schema = pa.schema([
        ("source_name", pa.string()),
        ("source_record_id", pa.string()),
        ("source_payload", pa.string()),
        ("source_path", pa.string()),
        ("source_row_number", pa.int64()),
        ("ingestion_timestamp", pa.string()),
        ("ingestion_batch_id", pa.string()),
        ("parse_status", pa.string()),
        ("parse_error", pa.string()),
    ])
    silver_schema = pa.schema([
        ("source_name", pa.string()),
        ("source_listing_key", pa.string()),
        ("source_payload", pa.string()),
        ("source_path", pa.string()),
        ("source_row_number", pa.int64()),
        ("city", pa.string()),
        ("latitude", pa.float64()),
        ("longitude", pa.float64()),
        ("postcode_full", pa.string()),
        ("pc4", pa.string()),
        ("postcode_source", pa.string()),
        ("postcode_quality", pa.string()),
        ("location_scope", pa.string()),
        ("status", pa.string()),
        ("currency_code", pa.string()),
        ("revenue_input_amount", pa.string()),
        ("revenue_input_unit", pa.string()),
        ("bedrooms", pa.string()),
        ("review_score", pa.string()),
        ("quality_flags", pa.string()),
        ("rejection_reason", pa.string()),
        ("duplicate_count", pa.int64()),
        ("ingestion_timestamp", pa.string()),
        ("ingestion_batch_id", pa.string()),
        ("original", pa.string()),
    ])

    for source_name in ("kamernet", "airbnb"):
        bronze_records = [
            {
                "source_name": record["source_name"],
                "source_record_id": record["source_record_id"],
                "source_payload": _json_text(record["source_payload"]),
                "source_path": record["source_path"],
                "source_row_number": record["source_row_number"],
                "ingestion_timestamp": record["ingestion_timestamp"],
                "ingestion_batch_id": record["ingestion_batch_id"],
                "parse_status": record["parse_status"],
                "parse_error": record["parse_error"],
            }
            for record in products[f"{source_name}_bronze"]
        ]
        bronze_path = output_dir / f"{source_name}_bronze.parquet"
        pq.write_table(
            pa.Table.from_pylist(bronze_records, schema=bronze_schema),
            bronze_path,
        )
        paths[f"{source_name}_bronze"] = bronze_path

        silver_records = []
        for record in products[f"{source_name}_silver"]:
            source_record = record["source_record"]
            amount = record["revenue_input_amount"]
            bedroom = record["bedrooms"]
            review = record["review_score"]
            silver_records.append({
                "source_name": record["source_name"],
                "source_listing_key": record["source_listing_key"],
                "source_payload": _json_text(source_record["source_payload"]),
                "source_path": source_record["source_path"],
                "source_row_number": source_record["source_row_number"],
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
                "revenue_input_amount": str(amount) if amount is not None else None,
                "revenue_input_unit": record["revenue_input_unit"],
                "bedrooms": str(bedroom) if bedroom is not None else None,
                "review_score": str(review) if review is not None else None,
                "quality_flags": _json_text(record["quality_flags"]),
                "rejection_reason": record["rejection_reason"],
                "duplicate_count": record["duplicate_count"],
                "ingestion_timestamp": record["ingestion_timestamp"],
                "ingestion_batch_id": record["ingestion_batch_id"],
                "original": _json_text(record["original"]),
            })
        silver_path = output_dir / f"{source_name}_silver.parquet"
        pq.write_table(
            pa.Table.from_pylist(silver_records, schema=silver_schema),
            silver_path,
        )
        paths[f"{source_name}_silver"] = silver_path
    return paths


def write_quality_parquet(
    products: dict[str, Any],
    quality_reports: dict[str, dict[str, Any]],
    output_dir: str | Path,
) -> dict[str, Path]:
    import pyarrow as pa
    import pyarrow.parquet as pq

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    quality_records = [
        {
            "source_name": source_name,
            "input_count": report["input_count"],
            "rejected_count": report["rejected_count"],
            "rejection_counts": _json_text(report["rejection_counts"]),
            "quality_flag_counts": _json_text(report["quality_flag_counts"]),
        }
        for source_name, report in quality_reports.items()
    ]
    quality_schema = pa.schema([
        ("source_name", pa.string()),
        ("input_count", pa.int64()),
        ("rejected_count", pa.int64()),
        ("rejection_counts", pa.string()),
        ("quality_flag_counts", pa.string()),
    ])
    quality_path = output_dir / "pipeline_quality.parquet"
    pq.write_table(
        pa.Table.from_pylist(quality_records, schema=quality_schema),
        quality_path,
    )

    rejection_schema = pa.schema([
        ("source_name", pa.string()),
        ("source_listing_key", pa.string()),
        ("pc4", pa.string()),
        ("postcode_source", pa.string()),
        ("postcode_quality", pa.string()),
        ("location_scope", pa.string()),
        ("status", pa.string()),
        ("rejection_reason", pa.string()),
        ("quality_flags", pa.string()),
        ("duplicate_count", pa.int64()),
        ("record_kind", pa.string()),
    ])
    evidence_records = []
    for source_name in ("kamernet", "airbnb"):
        for record in products[f"{source_name}_silver"]:
            quality_flags = record["quality_flags"]
            if record["rejection_reason"] or "inferred_postcode" in quality_flags:
                evidence_records.append({
                    "source_name": source_name,
                    "source_listing_key": record["source_listing_key"],
                    "pc4": record["pc4"],
                    "postcode_source": record["postcode_source"],
                    "postcode_quality": record["postcode_quality"],
                    "location_scope": record["location_scope"],
                    "status": record["status"],
                    "rejection_reason": record["rejection_reason"],
                    "quality_flags": _json_text(quality_flags),
                    "duplicate_count": record["duplicate_count"],
                    "record_kind": (
                        "rejected"
                        if record["rejection_reason"]
                        else "backfilled"
                    ),
                })
    evidence_path = output_dir / "quality_rejection_evidence.parquet"
    pq.write_table(
        pa.Table.from_pylist(evidence_records, schema=rejection_schema),
        evidence_path,
    )
    return {
        "pipeline_quality": quality_path,
        "quality_rejection_evidence": evidence_path,
    }


def write_run_manifest(
    gold: dict[str, Any],
    products: dict[str, Any],
    output_dir: str | Path,
    run_id: str | None = None,
    started_at: str | None = None,
) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    def json_value(value: Any) -> Any:
        if hasattr(value, "is_finite") and not value.is_finite():
            return str(value)
        if hasattr(value, "as_tuple"):
            return str(value)
        if isinstance(value, (list, tuple)):
            return [json_value(item) for item in value]
        if isinstance(value, dict):
            return {key: json_value(item) for key, item in value.items()}
        return value

    manifest = {
        "run_id": run_id,
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "source_counts": {
            "kamernet_bronze": len(products["kamernet_bronze"]),
            "airbnb_bronze": len(products["airbnb_bronze"]),
            "kamernet_silver": len(products["kamernet_silver"]),
            "airbnb_silver": len(products["airbnb_silver"]),
        },
        "quality": json_value(gold["quality"]),
        "reconciliation": json_value(gold["reconciliation"]),
        "output_paths": {
            name: str(path)
            for name, path in gold["output_paths"].items()
        },
    }
    manifest_path = output_dir / "run_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return manifest_path
