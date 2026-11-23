# Requirements: Exploration and Data Contracts

## Score

- **Feature completion score:** 100/100 (all required exploration, reconciliation, and contract outcomes completed and validated).

## Context

This work addresses **Milestone 1: Exploration and Data Contracts**, the first incomplete milestone in `specs/roadmap.md`. It establishes evidence-based input and output contracts before implementation of the bronze/silver pipeline.

The project compares annual gross rental revenue for Amsterdam listings from Kamernet and Airbnb. The source exports are expected to contain 46,722 Kamernet records and 9,913 Airbnb records. The constitution reports 8,095 Amsterdam Kamernet records, of which 7,722 are active, along with 2,254 Airbnb records missing postcodes, 14 missing bedroom values, and 1,711 missing review scores. Exploratory work must measure these values and report differences rather than assume the reference counts are exact.

## Decisions

- Restrict the investment comparison to Amsterdam records.
- Include only Kamernet listings with `isRoomActive = "true"` in current revenue candidates; retain inactive rows for audit and profiling.
- Define the property grain as one source listing: Kamernet `_id`, and an Airbnb source listing identifier or documented stable row hash if no identifier exists.
- Require the source identifier, location/candidate scope, and valid positive revenue input to qualify a record for revenue calculation.
- Treat Airbnb bedrooms and review scores as optional enrichment, not revenue requirements.
- Use the stated gross-revenue formulas as contract semantics: Kamernet monthly rent × 12; Airbnb nightly price × 365. Do not introduce occupancy adjustment in this milestone.
- Preserve original values and distinguish normalized, inferred, unknown, and rejected location values. Derive PC4 from coordinates only when a postcode polygon unambiguously contains the point; otherwise use an explicit unknown/null state.
- Define canonical silver and gold schemas, including data types, requiredness, grain, keys, and quality metadata. Keep implementation of ingestion and transformations in the following milestone.
- Put exploratory validation notebooks in `scratch/`; use project documentation to preserve findings and contract decisions.

## Required outcomes

- Reproducible profiling of source row counts, nulls, duplicates, data types, distributions, postcodes, coordinates, malformed records, and optional-field gaps.
- Quantified Amsterdam coverage and Kamernet active/inactive counts.
- A documented minimum input field set for defensible revenue calculations, with rejection conditions.
- Silver and gold schema contracts at the grains described above.
- Backfill and quarantine examples with expected outcomes, including unknown postcode handling.
- No undocumented material assumptions remaining at milestone completion.
