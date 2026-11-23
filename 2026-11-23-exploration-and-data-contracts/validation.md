# Validation: Exploration and Data Contracts

- [ ] Exploratory validation notebooks are present under `scratch/` and can be rerun against the supplied source files.
- [ ] Source row counts, nulls, duplicates, types, distributions, postcode patterns, coordinate bounds, and malformed records are measured and documented.
- [ ] Amsterdam candidate coverage is quantified, including active and inactive Kamernet counts.
- [ ] Measured values are reconciled with the constitution's stated counts; every discrepancy is explained or explicitly left as an investigated finding.
- [ ] Airbnb optional-field gaps are measured, and bedroom/review-score gaps do not incorrectly disqualify otherwise valid revenue records.
- [ ] The minimum required fields and rejection reasons for a defensible revenue calculation are explicitly documented for each source.
- [ ] Silver and gold contracts state field types, requiredness, grain, keys, revenue measures, and quality metadata.
- [ ] Postcode normalization, coordinate-based recovery, unknown values, and rejection behavior each have an example and expected outcome.
- [ ] Revenue contract formulas match the constitution: monthly Kamernet rent × 12 and Airbnb nightly price × 365.
- [ ] All material data assumptions are documented; no unexplained assumption remains at Milestone 1 exit.
