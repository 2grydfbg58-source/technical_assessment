# Validation: Revenue and Gold

- [x] Kamernet revenue tests verify monthly rent × 12 and exclude inactive, unknown-status, non-Amsterdam, and invalid-input records.
- [x] Airbnb revenue tests verify nightly price × 365 and exclude out-of-scope and invalid-input records while not requiring optional enrichment fields.
- [x] Airbnb identical source rows produce one gold property row per content hash, preserve the duplicate count, and do not imply proven real-world identity.
- [x] Eligible Amsterdam properties with unknown PC4 remain in the property product and are excluded from postcode aggregation with an observable count.
- [x] Property-level and postcode/source-level gold products have unique keys at their declared grains.
- [x] Postcode aggregation and source comparison values reconcile to the known-PC4 property subset; property totals reconcile to eligible, deduplicated silver inputs.
- [x] Property, postcode, and source-comparison Parquet outputs are created under `data/output` and their schemas are documented.
- [x] Focused tests pass, and the supplied-data gold pipeline completes with its outputs and reconciliation evidence recorded.

## Validation evidence

- Validation branch: `feature/2026-11-26-revenue-and-gold-validation`, created from merged commit `0554a12`.
- `PYTHONPATH=src python3 -m pytest -q`: **21 passed**.
- A fresh `run_full_pipeline` supplied-data run completed in a temporary output directory with 46,722 Kamernet and 9,913 Airbnb silver records. It verified unique property, postcode/source, and comparison keys; source comparison values matched postcode aggregates; postcode totals matched the known-PC4 property subset; and each property total reconciled with the eligible silver rows after deduplication.
- Kamernet: 7,722 eligible properties, 0 collapsed duplicate rows, €90,137,064 annual gross revenue, all with known PC4.
- Airbnb: 9,596 eligible silver rows reduced to 9,224 properties, 372 duplicate rows collapsed, €699,598,420 annual gross revenue, all with known PC4.
- Read the three committed Parquet files from `data/output` and compared them with the fresh pipeline exports; all schemas and table contents matched. They contain 16,946 property rows, 151 postcode/source rows, and 81 comparison rows. Supplied-data monetary fields are `decimal128(38, 2)`; schemas and grains are documented in `docs/revenue-gold.md`.
- Focused fixtures also verified unknown-PC4 property retention and postcode exclusion, inactive/unknown Kamernet status exclusion, Airbnb duplicate counts, and both annualization formulas.
- `git diff --check`: passed before recording this validation update. No checks failed, were blocked, or remain unrun.
