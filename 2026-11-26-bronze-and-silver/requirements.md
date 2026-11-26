# Requirements: Bronze and Silver

## Score

- **Feature completion score:** 0/100 (planning only; no implementation or validation evidence has been produced).

## Context

This feature addresses **Milestone 2: Bronze and Silver**, the earliest incomplete implementation milestone in `specs/roadmap.md`. It builds the ingestion and cleaning foundation needed by the later revenue and gold milestone. The source contracts and data assumptions are established in `specs/mission.md` and `specs/tech_stack.md`, and Milestone 1 findings are recorded in `docs/exploration-findings.md`.

## Decisions

- Ingest both Kamernet JSON and Airbnb CSV into traceable bronze records while retaining source payloads and available identifiers.
- Preserve malformed records with diagnostic context instead of silently discarding them.
- Retain original values alongside standardized values, and make backfilled or inferred values distinguishable from source values.
- Normalize Kamernet identifiers, rent, active status, and Dutch postcodes; normalize Airbnb price, coordinates, and four-digit or full Dutch postcodes.
- Use a deterministic content-based Airbnb row key because the export has no listing identifier. Treat exact duplicates deterministically and retain duplicate counts, without claiming that the key proves real-world identity.
- Derive missing or invalid Airbnb PC4 values from the supplied postcode GeoJSON only when point-in-polygon matching produces exactly one unambiguous postcode. Preserve unknown or ambiguous cases explicitly.
- Keep inactive and unknown-status Kamernet records auditable; only `"true"` is active. Preserve source records even when they are outside the Amsterdam comparison scope, and represent scope explicitly for downstream filtering.
- Keep optional Airbnb bedrooms and review scores from blocking revenue eligibility; do not calculate revenue or build gold aggregations in this milestone.
- Include quality flags, rejection reasons, and an explicit quarantine/unknown state where a record cannot be safely normalized or recovered.

## Scope

### In scope

- Reusable ingestion and cleaning code for both supplied sources.
- Bronze and silver record contracts, source preservation, typing, normalization, deduplication, geographic postcode enrichment, quality metadata, and quarantine handling.
- Focused unit tests and directly related documentation.

### Out of scope

- Annual revenue calculations, property/postcode gold aggregations, and Parquet gold exports (Milestone 3).
- Databricks job orchestration and operational deployment (Milestone 4).
- Dashboard, CI/CD, streaming, or other stretch goals.

## Completion

The feature is complete only when bronze and silver records are reproducible and traceable, all parsing and cleaning transformations have focused tests, and missing data is retained or repaired according to the published rules. The roadmap milestone must remain incomplete until its exit criteria are verified.
