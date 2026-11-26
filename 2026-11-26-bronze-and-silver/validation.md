# Validation: Bronze and Silver

- [ ] Kamernet JSON and Airbnb CSV can each be ingested reproducibly into bronze records with source context and ingestion metadata.
- [ ] Bronze records preserve original source payloads and available source identifiers; malformed records remain inspectable with diagnostic context.
- [ ] Silver records have documented types and canonical fields while retaining original values and distinguishing normalized or inferred values.
- [ ] Kamernet `_id`, rent, active status, and postcode normalization follow the documented source contracts; inactive and unknown-status records remain auditable and are not treated as active.
- [ ] Airbnb prices, coordinates, and postcode forms are normalized; optional bedrooms and review scores do not block otherwise eligible records.
- [ ] Duplicate handling is deterministic, reports duplicate counts, and does not claim that an Airbnb content key proves real-world identity.
- [ ] Missing or invalid Airbnb PC4 recovery uses the supplied postcode polygons only for a single unambiguous containing polygon; ambiguous and unrecoverable cases remain explicitly unknown or quarantined.
- [ ] Amsterdam candidate scope is represented explicitly, and source records outside that scope are not silently lost.
- [ ] Focused unit tests cover source parsing, malformed-record handling, normalization, typing, deduplication, postcode recovery, unknown/quarantine behavior, and source preservation.
- [ ] The bronze/silver schemas and cleaning/backfill rules are documented, and all transformations required by Milestone 2 are covered by tests.
