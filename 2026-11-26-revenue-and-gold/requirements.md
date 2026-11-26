# Requirements: Revenue and Gold

## Score

- **Feature completion score:** 0/100 (planning only; implementation and validation have not started).

## Context

This feature addresses **Milestone 3: Revenue and Gold**, the earliest incomplete implementation milestone in `specs/roadmap.md`. It builds on the bronze and silver pipeline and the source contracts in `specs/mission.md` and `specs/tech_stack.md`.

The goal is to calculate standardized annual gross revenue for Amsterdam Kamernet and Airbnb listings, provide property- and postcode-level gold datasets, compare both sources, and export the products as Parquet under `data/output`.

## Decisions

- Kamernet annual gross revenue is monthly EUR rent multiplied by 12. Only Amsterdam records with `status="true"` and a valid positive revenue input are current revenue candidates. Inactive and unknown-status records remain available in silver for audit and do not enter gold revenue.
- Airbnb annual gross revenue is nightly EUR price multiplied by 365. Only records whose geographic `location_scope` is Amsterdam and whose revenue input is valid and positive enter gold revenue.
- Revenue is gross potential revenue based on snapshot prices. Do not apply occupancy, operating costs, taxes, financing, or forecasts.
- The property grain is one source listing: Kamernet `source_listing_key` and Airbnb's existing stable content hash. Preserve source, key, PC4, annual revenue, and relevant duplicate/quality context in the property product.
- Airbnb exact duplicate source rows are collapsed to one gold candidate per content hash, with the duplicate count retained on the representative row and reflected in reconciliation. This is a deterministic exported-row policy, not proof that identical rows are the same real-world listing.
- Include eligible Amsterdam properties in the property product even when PC4 is unknown. Use only known PC4 values for postcode aggregates and make that exclusion observable.
- Aggregate by source and PC4 so both sources can be compared at the same postcode grain. Keep property and postcode keys unique at their declared grains.
- Export the property, postcode, and source-comparison products as Parquet under `data/output`; document their schemas and keys.
- Reconcile the property total to eligible, deduplicated silver inputs. Reconcile postcode totals to the property subset with known PC4, accounting for the explicitly excluded unknown-PC4 records.

## Scope

### In scope

- Reusable revenue calculation, gold product, aggregation, and Parquet export code in the existing package.
- Property-level annual gross revenue for eligible listings from both sources.
- Source-by-PC4 revenue aggregation and comparison.
- Focused unit and output tests, plus directly related schema and calculation documentation.

### Out of scope

- Changes to bronze/silver ingestion and cleaning behavior.
- Occupancy-adjusted revenue, costs, yield, property valuation, or investment recommendations.
- Databricks job orchestration and operational deployment (Milestone 4).
- Dashboard, CI/CD, streaming, or other stretch goals.

## Completion

Complete this feature only when revenue calculations are unit-tested, property and postcode keys are unique at their intended grains, Parquet outputs have documented schemas, and gold totals reconcile with the corresponding eligible silver inputs. Until then, leave the roadmap milestone incomplete and keep the score at 0/100.
