# Mission

## Purpose

Build a reliable data pipeline that helps RevoData identify Amsterdam postcodes with the strongest potential for property investment and compare long-term Kamernet income with short-term Airbnb income.

The MVP is an engineering and analytical foundation, not a financial recommendation engine. It prioritizes reproducible, traceable calculations and high-quality datasets over unverified return assumptions.

## Business Goal

For each property and postcode, produce:

- An estimated annual gross revenue for Kamernet rental listings.
- An estimated annual gross revenue for Airbnb listings.
- A source-level and postcode-level comparison of potential revenue.
- A ranked view of Amsterdam postcodes by available investment potential.

## Analytical Scope

### In scope

- Ingest `data/rentals.json` from Kamernet.
- Ingest `data/airbnb.csv` from Airbnb.
- Restrict the investment comparison to Amsterdam records.
- Standardize locations and postal codes.
- Validate, clean, deduplicate, and reconcile source records.
- Design explicit backfill behavior for missing or improper values.
- Apply Medallion Architecture: bronze, silver, and gold datasets.
- Produce pipeline notebooks, reusable packages, tests, configuration, documentation, and Parquet exports.
- Enrich or visualize data at stretch-goal levels when the MVP is complete.

### Out of scope for MVP

- Purchasing, financing, or valuation of properties.
- Purchase price, mortgage, tax, maintenance, management, vacancy, cleaning, or utility costs.
- An external market forecast or live data acquisition system.
- Production real-time processing.
- Automated investment decisions or financial guarantees.

## Revenue Assumption

The first comparison uses gross potential revenue:

- Kamernet annual gross revenue = monthly rent × 12.
- Airbnb annual gross revenue = nightly price × 365.

### Source fields

- Kamernet rent is in `rent` as a Euro string such as `€ 500,-` or `€ 500,-  Utilities incl.`. Parse the first numeric amount and store EUR separately. Only active listings (`isRoomActive = "true"`) are current candidates; inactive listings remain in bronze and may be retained in silver for history or quality analysis.
- Kamernet canonical identity is `_id`, represented as a one-element JSON array in the source.
- Kamernet postcode is `postalCode` as a six-character Dutch postcode such as `1024SJ`. Normalize it to `1024 SJ` only for display and retain `1024` as the postcode aggregation key.
- Airbnb price is `price`, already an integer nightly value in the supplied dataset. Treat it as EUR unless a documented source update proves otherwise.
- Airbnb postcode is `zipcode`, supplied as a four-digit postcode, a six-character full postcode, or a missing/invalid value.
- Airbnb coordinates are `latitude` and `longitude` and are complete in the supplied dataset.
- For annual gross comparison, aggregate all valid Airbnb listings and active valid Kamernet listings independently by PC4 postcode.

The source exports contain 46,722 Kamernet records and 9,913 Airbnb records. The supplied Kamernet data spans multiple Dutch cities; 8,095 records are for Amsterdam, of which 7,722 have `isRoomActive = "true"` and 353 are inactive. The Airbnb dataset has 2,254 missing postcodes, 14 missing bedroom values, and 1,711 missing review scores.

If an occupancy or availability field is present in the source data, it may be exposed as a configurable or derived metric. It must not silently change the default gross calculation. The MVP should therefore distinguish:

- `gross_potential_revenue`
- `occupancy_adjusted_revenue` when source or documented policy data supports it

The pipeline must document any exchange, unit, currency, and date assumptions applied to the source fields.

## Target Data Products

### Bronze

- Preserve source records as faithfully as practical.
- Retain source identifiers and an ingestion timestamp.
- Keep malformed records for traceability instead of discarding them silently.

### Silver

- Standardized, typed, deduplicated records.
- Canonical Amsterdam postcode and location fields.
- Quality flags for missing, repaired, rejected, and suspicious values.
- Reconciled property-level revenue fields.

### Gold

- Property-level revenue table.
- Postcode-level revenue summary.
- A source comparison table indicating whether Kamernet or Airbnb has higher potential gross revenue for comparable or nearby data.
- Parquet exports under `data/output`.

## Backfill Principles

Missing or improper data must be handled with a deterministic strategy:

1. Detect the issue and preserve the original value.
2. Normalize a known Kamernet postcode or Airbnb full postcode to canonical Dutch format.
3. Derive a missing or malformed Airbnb PC4 from `latitude` and `longitude` using `data/geo/post_codes.geojson`, when the point is unambiguously contained by a postcode polygon.
4. Use an explicitly named `unknown` or null state when recovery is not reliable.
5. Mark inferred values so downstream consumers can distinguish them from original values.
6. Reject records that lack the minimum fields required for a defensible revenue calculation.
7. Never infer a financially material value through an arbitrary default.

## Data Quality Rules

The MVP pipeline must validate:

- Required source identifiers.
- Kamernet `_id`, rent, city, active status, coordinates, and postcode.
- Airbnb coordinates and nightly price.
- The current Amsterdam candidate set must use active Kamernet listings; inactive records must not contribute to investment rankings.
- Kamernet rent parsing must reject values that are absent or outside a configured positive range.
- Airbnb invalid or missing postcodes must not be guessed from nearby text or an arbitrary default.
- Airbnb `bedrooms` and `review_scores_value` are optional enrichment fields and must not block revenue calculations.
- Positive, numeric rental amounts and nightly prices.
- Valid Amsterdam postcodes or clearly flagged unknown postcodes.
- Valid latitude and longitude ranges when coordinates are provided.
- Duplicate properties and source records.
- Unsupported units or currencies.
- Date and ingestion freshness.
- Property and postcode aggregation row counts.
- The property grain should be the source listing: Kamernet `_id` and Airbnb a source listing key or a stable row hash if no identifier exists.
- Duplicate Airbnb listings should be identified by an exact or documented key before aggregation.

At least one quality framework, such as Spark expectations or an equivalent declarative check layer, must publish pass/fail counts and rejected-record reasons.

## Success Criteria

The MVP is successful when:

- Both sources are ingested and cleaned through notebooks or reusable pipeline code.
- Bronze, silver, and gold outputs are created following Medallion Architecture.
- Missing and improper values follow documented, tested backfill rules.
- Annual potential gross revenue is calculated consistently for both sources.
- Property and postcode aggregations are available and exported as Parquet.
- Exploratory validation work is located in `scratch`.
- Pipeline implementation is in `notebooks` and reusable code is in `src/<package_name>`.
- Unit tests cover parsing, cleaning, backfill, revenue calculation, and aggregation.
- The README and `docs` explain both implementation and rationale.
- Pipeline configuration is stored in `resources`.
