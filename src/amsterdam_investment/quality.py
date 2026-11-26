from __future__ import annotations

from collections import Counter
from typing import Iterable


def quality_report(silver_records: Iterable[dict]) -> dict:
    records = list(silver_records)
    rejection_counts = Counter(
        record["rejection_reason"]
        for record in records
        if record.get("rejection_reason")
    )
    flag_counts = Counter(
        flag
        for record in records
        for flag in record.get("quality_flags", [])
    )
    return {
        "input_count": len(records),
        "rejected_count": sum(bool(record.get("rejection_reason")) for record in records),
        "rejection_counts": dict(sorted(rejection_counts.items())),
        "quality_flag_counts": dict(sorted(flag_counts.items())),
    }
