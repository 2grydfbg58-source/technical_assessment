# Validation: Exploration and Data Contracts

- [x] Exploratory validation notebooks are present under `scratch/` and can be rerun against the supplied source files.
- [x] Source row counts, nulls, duplicates, types, distributions, postcode patterns, coordinate bounds, and malformed records are measured and documented.
- [x] Amsterdam candidate coverage is quantified, including active and inactive Kamernet counts.
- [x] Measured values are reconciled with the constitution's stated counts; every discrepancy is explained or explicitly left as an investigated finding.
- [x] Airbnb optional-field gaps are measured, and bedroom/review-score gaps do not incorrectly disqualify otherwise valid revenue records.
- [x] The minimum required fields and rejection reasons for a defensible revenue calculation are explicitly documented for each source.
- [x] Silver and gold contracts state field types, requiredness, grain, keys, revenue measures, and quality metadata.
- [x] Postcode normalization, coordinate-based recovery, unknown values, and rejection behavior each have an example and expected outcome.
- [x] Revenue contract formulas match the constitution: monthly Kamernet rent × 12 and Airbnb nightly price × 365.
- [x] All material data assumptions are documented; no unexplained assumption remains at Milestone 1 exit.
