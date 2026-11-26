# Bronze and Silver Pipeline

The `amsterdam_investment` package implements the ingestion and cleaning
Milestone 2. It is portable outside Databricks and accepts a repository root
whose `data/` directory contains the supplied source and geography files.

## Bronze

`ingestion.ingest_kamernet` parses the top-level JSON array and preserves each
record's original payload. Malformed JSON or non-object records remain as
diagnostic bronze records rather than being silently discarded.

`ingestion.ingest_airbnb` parses the CSV with the standard library so row
width and source values remain explicit. Every bronze record includes the source
path, source row number, parse status/error, UTC ingestion timestamp, and a
batch ID derived from a SHA-256 prefix of the source file.

## Silver

Kamernet `_id` values are scalarized, Euro rent strings are parsed, active
status is normalized to `true`, `false`, or `unknown`, and six-character
postcodes are canonicalized. Inactive and unknown-status records remain in
silver audit data.

Airbnb records use a deterministic SHA-256 key over the exact source-row
payload because the export has no listing identifier. The key is explicitly
provisional: duplicate counts are retained, but the hash does not establish
real-world listing identity.

Four-digit and full Dutch postcodes are normalized. Missing or invalid
postcodes are recovered only when a coordinate is contained by exactly one
postcode polygon in `data/geo/post_codes.geojson`. Ambiguous or unrecoverable
values remain unknown. Amsterdam scope is established by
`data/geo/amsterdam_areas.geojson`, not by a coordinate bounding box.

Bedrooms and review scores are optional enrichment fields. Positive numeric
rent and nightly price fields are retained as EUR revenue inputs; this
milestone does not calculate annual gold revenue.

## Quality reporting

`quality.quality_report` returns input, rejection, rejection-reason, and quality
flag counts for a set of silver records. Rejection reasons are machine-readable
and include missing or invalid identifiers, rent, price, and location values.

## Reproduction

```bash
python -m pip install -e .
pytest
python - <<'PY'
from amsterdam_investment.pipeline import run_bronze_silver

result = run_bronze_silver(".")
print(len(result["kamernet_bronze"]), len(result["airbnb_bronze"]))
PY
```
