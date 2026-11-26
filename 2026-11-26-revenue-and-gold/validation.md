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

- `PYTHONPATH=src python3 -m pytest -q`: 21 passed.
- Supplied-data `run_full_pipeline(".")` completed with 46,722 Kamernet and 9,913 Airbnb silver records.
- Kamernet gold: 7,722 unique eligible properties, €90,137,064 total annual gross revenue, all with known PC4.
- Airbnb gold: 9,224 unique eligible properties, 372 duplicate source rows collapsed, €699,598,420 total annual gross revenue, all with known PC4.
- For each source, property revenue equaled known-PC4 plus unknown-PC4 revenue; postcode revenue equaled the known-PC4 property subset. Property, postcode, and comparison keys were unique and comparison measures matched their source-by-PC4 aggregates.
- Parquet products were written and read back from `data/output`: 16,946 property rows, 151 postcode/source rows, and 81 comparison rows. Monetary fields use `decimal128(38, 2)` for the supplied data; schemas and grains are documented in `docs/revenue-gold.md`.
