from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .gold import build_gold_products, write_gold_parquet
from .ingestion import ingest_airbnb, ingest_kamernet
from .silver import clean_airbnb, clean_kamernet


def run_bronze_silver(
    root: str | Path,
) -> dict[str, Any]:
    root = Path(root)
    kamernet_bronze = ingest_kamernet(root / "data" / "rentals.json")
    airbnb_bronze = ingest_airbnb(root / "data" / "airbnb.csv")
    postcode_path = root / "data" / "geo" / "post_codes.geojson"
    amsterdam_path = root / "data" / "geo" / "amsterdam_areas.geojson"

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
) -> dict[str, Any]:
    root = Path(root)
    products = run_bronze_silver(root)
    gold = build_gold_products(
        products["kamernet_silver"],
        products["airbnb_silver"],
    )
    target_dir = Path(output_dir) if output_dir is not None else root / "data" / "output"
    gold["output_paths"] = write_gold_parquet(gold, target_dir)
    return {**products, **gold}
