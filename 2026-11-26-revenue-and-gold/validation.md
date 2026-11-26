# Validation: Revenue and Gold

- [ ] Kamernet revenue tests verify monthly rent × 12 and exclude inactive, unknown-status, non-Amsterdam, and invalid-input records.
- [ ] Airbnb revenue tests verify nightly price × 365 and exclude out-of-scope and invalid-input records while not requiring optional enrichment fields.
- [ ] Airbnb identical source rows produce one gold property row per content hash, preserve the duplicate count, and do not imply proven real-world identity.
- [ ] Eligible Amsterdam properties with unknown PC4 remain in the property product and are excluded from postcode aggregation with an observable count.
- [ ] Property-level and postcode/source-level gold products have unique keys at their declared grains.
- [ ] Postcode aggregation and source comparison values reconcile to the known-PC4 property subset; property totals reconcile to eligible, deduplicated silver inputs.
- [ ] Property, postcode, and source-comparison Parquet outputs are created under `data/output` and their schemas are documented.
- [ ] Focused tests pass, and the supplied-data gold pipeline completes with its outputs and reconciliation evidence recorded.

## Validation evidence

No implementation or validation has been performed. This feature is planning-only.
