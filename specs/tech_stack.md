# Tech Stack

## Primary Platform

- Databricks Free Trial
- Databricks notebooks for exploration and pipeline implementation
- Apache Spark for distributed ingestion and transformations
- Delta Lake for durable bronze, silver, and gold tables
- Databricks Jobs for scheduled pipeline execution

The implementation should remain portable enough to run local unit tests outside a Databricks runtime.

## Languages and Libraries

- Python
- PySpark
- pandas for small in-process exploratory validation only
- GeoPandas and Shapely for GeoJSON loading and point-in-polygon postcode enrichment
- pytest for unit tests
- pyproject-based packaging for reusable pipeline code
- Ruff or Flake8 for linting
- Black for formatting
- pre-commit for local quality hooks

Avoid heavy notebook-only logic: reusable transformation and validation functions belong in `src/<package_name>`.

## Input and Output Formats

- Kamernet source: JSON at `data/rentals.json`
- Airbnb source: CSV at `data/airbnb.csv`
- Geographic datasets:
  - `data/geo/post_codes.geojson`
  - `data/geo/amsterdam_areas.geojson`
- Gold exports: Parquet under `data/output`
- Pipeline configuration: Databricks/job-compatible files under `resources`

## Medallion Architecture

### Bronze

- Raw source payload retention.
- Source name, source record identifier, ingestion timestamp, and ingestion batch identifier.
- Append-only ingestion where practical.
- Preserve malformed records for diagnostics.

### Silver

- Typed schemas.
- Canonical rental and location fields.
- Standardized postcode and currency representation.
- Deduplication and source-specific data-quality flags.
- Rejected and backfilled-record audit fields.

### Gold

- Property-level annual revenue.
- Postcode-level annual revenue.
- Source comparison and ranking metrics.
- Readable names and stable schemas for reporting.

## Recommended Package Layout

```text
src/<package_name>/
  ingestion/
  cleaning/
  enrichment/
  revenue/
  aggregation/
  quality/
notebooks/
scratch/
tests/
resources/
docs/
data/output/
```

The exact package name should reflect the pipeline domain, such as `amsterdam_investment`.

## Data and Configuration Conventions

- Use named, typed Spark schemas for JSON and CSV ingestion.
- Use ISO 8601 timestamps.
- Store source currency explicitly and normalize to one documented currency only when conversion rules exist.
- Represent unknowns consistently; do not silently replace missing rent or price with zero.
- Keep thresholds, currency assumptions, file paths, table names, and calculation parameters in configuration.
- Store secrets in Databricks Secrets or an equivalent secret provider, never in notebooks or source control.
- Normalize Kamernet `_id` arrays to a scalar string identifier.
- Parse Kamernet `rent` with explicit Euro validation and preserve the original string.
- Derive Airbnb PC4 postcodes from valid 4-digit values or 6-character Dutch postcodes; use polygon containment only for missing or invalid values.
- Do not treat Airbnb `bedrooms` or review scores as revenue requirements.

## Data Quality Framework

Use Databricks expectations or a framework with equivalent capabilities:

- Required-field checks.
- Range checks for coordinates and prices.
- Postcode format checks.
- Duplicate detection.
- Validity and rejection counts.
- Detailed rejection reasons in silver or a dedicated quarantine table.
- Source-specific checks for Kamernet rent parsing and active status.
- Airbnb coordinate bounds and point containment checks.

Quality checks must be automated and testable rather than embedded only in notebooks.

## CI/CD and Delivery

MVP delivery can use Git and manual Databricks deployment. Stretch-level CI/CD should use:

- GitHub Actions or an equivalent hosted CI provider.
- Automated pytest execution.
- Formatting and lint checks.
- pre-commit hooks.
- Databricks Asset Bundles or Declarative Automation Bundles for deployment.

For Declarative Automation Bundles, deployment configuration belongs in `resources` and environment-specific values should remain separate from code.

## Stretch-Level Visualization

- Databricks SQL dashboard or a notebook-hosted visualization.
- GeoJSON support for postcode and Amsterdam-area boundaries.
- A postcode choropleth for rent revenue and Airbnb revenue.
- Source drill-down and quality annotations.

## Testing Tools

- pytest for unit and focused integration tests.
- Spark local session or Databricks test notebook for Spark-level tests.
- Temporary directories or in-memory fixtures for Parquet and table validation.
- Synthetic fixtures that cover malformed, missing, duplicate, and postcode-backfill cases.

Tests must verify behavior, not only library imports or DataFrame constants.
