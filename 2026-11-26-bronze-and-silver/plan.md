# Plan: Bronze and Silver

1. **Establish ingestion and transformation contracts**
   - Add the minimal reusable package structure and configuration needed for source paths, ingestion metadata, and postcode geography.
   - Define typed bronze and silver record contracts that preserve source values and expose canonical fields, Amsterdam scope, quality flags, and rejection reasons.
   - Keep this milestone limited to ingestion and cleaning; defer revenue calculations and gold products.

2. **Implement traceable bronze ingestion**
   - Ingest `data/rentals.json` and `data/airbnb.csv` into reproducible bronze records.
   - Retain source payloads, source name, source record identity where available, and ingestion metadata.
   - Preserve malformed or unparseable records in an explicit diagnostic/quarantine path with source context rather than silently dropping them.

3. **Standardize and deduplicate silver records**
   - Normalize Kamernet `_id`, rent, active status, city, and postcode while retaining original values.
   - Normalize Airbnb price, coordinates, postcode, and optional enrichment fields; derive a deterministic row key when no source identifier exists.
   - Apply documented, deterministic duplicate handling without treating identical Airbnb rows as proven real-world identity.
   - Retain records and status needed for audit, including inactive or unknown-status Kamernet rows and out-of-scope candidates.

4. **Clean and enrich location data**
   - Normalize valid Dutch postcodes to canonical display form and derive PC4 keys.
   - Recover missing or invalid Airbnb postcodes only when coordinates fall unambiguously within a supplied postcode polygon.
   - Keep unrecoverable, ambiguous, or out-of-scope cases explicit with quality state and reason; do not guess a postcode.

5. **Add focused tests and implementation documentation**
   - Test parsing, normalization, type conversion, deduplication, postcode recovery, unknown/quarantine behavior, and preservation of source records.
   - Document the bronze/silver outputs, transformation rules, and how to reproduce the checks.
   - Verify milestone exit criteria and record any unmet criterion without marking the milestone complete prematurely.
