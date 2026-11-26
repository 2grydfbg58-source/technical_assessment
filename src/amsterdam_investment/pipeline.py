from __future__ import annotations

import json
from dataclasses import dataclass
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
        gold["output_paths"] = write_gold_parquet(gold, Path(config.output_dir))
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
