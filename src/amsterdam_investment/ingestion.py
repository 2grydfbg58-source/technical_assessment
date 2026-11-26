from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def source_batch_id(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"{path.name}:{digest[:16]}"


def _bronze(
    source_name: str,
    source_record_id: str | None,
    payload: dict[str, Any] | str,
    source_path: Path,
    row_number: int,
    ingestion_batch_id: str,
    parse_status: str = "parsed",
    parse_error: str | None = None,
) -> dict[str, Any]:
    return {
        "source_name": source_name,
        "source_record_id": source_record_id,
        "source_payload": payload,
        "source_path": str(source_path),
        "source_row_number": row_number,
        "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
        "ingestion_batch_id": ingestion_batch_id,
        "parse_status": parse_status,
        "parse_error": parse_error,
    }


def ingest_kamernet(path: Path) -> list[dict[str, Any]]:
    path = Path(path)
    batch_id = source_batch_id(path)
    try:
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return [
            _bronze(
                "kamernet",
                None,
                path.read_text(encoding="utf-8", errors="replace"),
                path,
                0,
                batch_id,
                "malformed",
                str(exc),
            )
        ]

    if not isinstance(payload, list):
        return [
            _bronze(
                "kamernet",
                None,
                payload if isinstance(payload, dict) else str(payload),
                path,
                0,
                batch_id,
                "malformed",
                "Top-level JSON value is not an array",
            )
        ]

    records: list[dict[str, Any]] = []
    for index, row in enumerate(payload, start=1):
        if not isinstance(row, dict):
            records.append(
                _bronze(
                    "kamernet",
                    None,
                    str(row),
                    path,
                    index,
                    batch_id,
                    "malformed",
                    "JSON record is not an object",
                )
            )
            continue
        source_id = row.get("_id")
        if isinstance(source_id, list):
            source_id = str(source_id[0]) if source_id else None
        elif source_id is not None:
            source_id = str(source_id)
        records.append(_bronze("kamernet", source_id, row, path, index, batch_id))
    return records


def ingest_airbnb(path: Path) -> list[dict[str, Any]]:
    path = Path(path)
    batch_id = source_batch_id(path)
    records: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return [
                _bronze(
                    "airbnb",
                    None,
                    "",
                    path,
                    0,
                    batch_id,
                    "malformed",
                    "CSV header is missing",
                )
            ]
        for index, row in enumerate(reader, start=1):
            row_payload = dict(row)
            has_extra_fields = None in row_payload
            if has_extra_fields:
                parse_status = "malformed"
                parse_error = "CSV row has extra fields"
                source_id = None
            else:
                parse_status = "parsed"
                parse_error = None
                source_id = None
            records.append(
                _bronze(
                    "airbnb",
                    source_id,
                    row_payload,
                    path,
                    index,
                    batch_id,
                    parse_status,
                    parse_error,
                )
            )
    return records
