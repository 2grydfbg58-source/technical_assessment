# Roadmap

## Milestone 0: Assessment Setup

**Status: [x] Completed**

### Outcomes

- Confirmed the delivered source files and schemas.
- Confirm currency field semantics: both source prices are Euro amounts.
- Create a baseline repository layout.
- Add reusable configuration and package scaffolding.

### Exit Criteria

- Source JSON, CSV, and GeoJSON datasets are available.
- Field mappings include `_id`, `rent`, `city`, `postalCode`, `isRoomActive`, and Airbnb `zipcode`, coordinates, `price`, `room_type`, `bedrooms`, and `review_scores_value`.
- Success formulas and quality thresholds are registered in configuration.

## Milestone 1: Exploration and Data Contracts

**Status: [x] Completed**

### Outcomes

- Place exploratory validation notebooks in `scratch`.
- Profile row counts, nulls, duplicates, data types, distributions, postcodes, and coordinates.
- Document the supplied data findings: 46,722 Kamernet and 9,913 Airbnb records.
- Quantify Amsterdam rental coverage, missing/invalid postcode patterns, coordinate bounds, and optional-field gaps.
- Inspect malformed JSON and CSV records.
- Define the minimum fields required for a defensible revenue calculation.
- Specify silver and gold schemas.

### Exit Criteria

- Source and target schemas are documented.
- The source scope is Amsterdam; the downstream revenue comparison excludes non-Amsterdam candidates.
- Backfill rules have examples and expected outcomes.
- Exploratory checks identify no undocumented material data assumption.

## Milestone 2: Bronze and Silver

**Status: [x] Completed**

### Outcomes

- Implement Kamernet JSON ingestion.
- Implement Airbnb CSV ingestion.
- Preserve raw or minimally transformed bronze records.
- Standardize fields and types.
- Deduplicate source records.
- Implement postcode and location cleanup.
- Normalize Kamernet postcodes and derive stable PC4 keys.
- Normalize Airbnb 4-digit and full Dutch postcode values.
- Use point-in-polygon GeoJSON enrichment for missing or invalid Airbnb postcodes.
- Keep records with unknown postcodes in a quarantine or explicit unknown-postcode state and exclude them from postcode rankings.
- Implement backfill and quarantine logic.
- Attach quality flags and rejection reasons.

### Exit Criteria

- Bronze and silver records are reproducible and traceable.
- All parsing and cleaning transformations have unit tests.
- Missing data is retained or repaired according to the published rules.

## Milestone 3: Revenue and Gold

**Status: [x] Completed**

### Outcomes

- Calculate Kamernet annual gross revenue from monthly rent.
- Calculate Airbnb annual gross revenue from nightly price.
- Use active (`isRoomActive = "true"`) Kamernet listings only.
- Preserve inactive Kamernet rows for audit and optional historical analysis.
- Produce property-level data.
- Aggregate revenue by postcode.
- Compare both sources.
- Export gold datasets to `data/output` as Parquet.

### Exit Criteria

- Revenue calculations are unit-tested.
- Property and postcode keys are unique at their intended grain.
- Parquet outputs have documented schemas.
- Gold aggregation totals reconcile with silver inputs.

## Milestone 4: Pipeline and Operations

**Status: [x] Completed**

### Replan

The mission and tech stack require postcode ranking metrics, but the completed
revenue comparison currently reports source totals and the higher-revenue
source without ranks. Add independent source rankings here rather than reopening
Milestone 3, whose published exit criteria and validation are complete.

### Outcomes

- Add separate Kamernet and Airbnb PC4 ranks to the source-comparison product,
  ordered by annual gross revenue; do not combine the two source totals into one
  rank. Equal totals share a standard competition rank, and a source with no
  eligible properties at a PC4 has no rank.
- Organize implementation into reusable notebooks and Python package modules.
- Add job configuration under `resources`.
- Parameterize source paths and table names.
- Add README and `docs` rationale.

### Exit Criteria

- Each source's PC4 rank is descending by its annual gross revenue, tied totals
  share a rank, and PC4s without eligible source properties are unranked.
- Ranking fields, nullability, and tie behavior are documented and covered by
  focused tests.
- Configuration can be changed without editing transformation code.
- Pipeline failures expose source and quality context.
- Documentation explains why each major rule exists.

## Milestone 5: MVP Hardening

**Status: [x] Completed**

### Outcomes

- Run the pipeline end to end as a Databricks job on the Free Trial.
- Complete unit tests.
- Run the full pipeline on a clean environment or fixture.
- Review quality, duplicate, and aggregation edge cases.
- Produce final gold exports.

### Exit Criteria

- The configured pipeline completes end to end on Databricks Free Trial, with run and output evidence recorded.
- Tests pass.
- Bronze, silver, and gold outputs exist.
- Rejection and backfill behavior is observable.
- README documents setup and execution.

## Stretch 1: Engineer

**Status: [ ] Not started**

- Add CI/CD deployment.
- Run tests and lint checks in CI.
- Add pre-commit hooks.
- Separate Databricks environments with configurable resource names.

## Stretch 2: Artist

**Status: [ ] Not started**

- Add a dashboard of potential revenue by postcode.
- Compare Kamernet and Airbnb revenue visually.
- Create data-flow and CI/CD diagrams.
- Add quality and backfill annotations to reports.

## Stretch 3: Future-Proof

**Status: [ ] Not started**

- Evaluate Lakeflow Spark Declarative Pipelines.
- Define expectations for ingestion, cleaning, and gold outputs.
- Package deployment through Declarative Automation Bundles.
- Add environment promotion and rollback guidance.

## Stretch 4: Over 9000

**Status: [ ] Not started**

- Stream JSON records one at a time.
- Manage ingestion checkpoints and malformed records.
- Update gold tables incrementally as streaming records arrive.
- Define event-time and processing-time semantics.

## Stretch 5: Geographic

**Status: [ ] Not started**

Use the source data and approved geographic datasets to:

- Recover missing Airbnb postcodes from `data/geo/post_codes.geojson`.
- Add Amsterdam-area dimensions from `data/geo/amsterdam_areas.geojson`.
- Compare revenue at postcode and area grains.
- Feed area boundaries into the visualization.
