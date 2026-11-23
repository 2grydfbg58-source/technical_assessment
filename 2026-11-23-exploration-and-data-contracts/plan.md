# Plan: Exploration and Data Contracts

1. **Establish reproducible source inspection**
   - Locate and inspect the supplied Kamernet JSON, Airbnb CSV, and geographic data.
   - Create exploratory validation notebooks under `scratch/`.
   - Record the inputs and commands or notebook steps needed to reproduce the findings.

2. **Profile and validate the source data**
   - Measure row counts, data types, nulls, duplicates, value distributions, postcode patterns, and coordinate bounds.
   - Inspect malformed JSON/CSV records and optional-field gaps.
   - Quantify Amsterdam coverage and distinguish active from inactive Kamernet listings.
   - Compare measured results with the counts and known gaps stated in the project constitution; document any discrepancy.

3. **Define the revenue input minimum**
   - Identify the fields required to calculate annual gross revenue for each source.
   - Specify source-specific validation and rejection reasons for missing or invalid required values.
   - Keep optional Airbnb enrichment fields separate from revenue eligibility.

4. **Specify silver and gold data contracts**
   - Document typed, canonical silver fields, source identifiers, postcode representation, and quality/backfill flags.
   - Document property-level and postcode-level gold grains, keys, revenue measures, and comparison fields.
   - Include examples and expected outcomes for postcode normalization, coordinate-based recovery, unknown postcodes, and rejected records.

5. **Review and finalize milestone evidence**
   - Ensure every material data assumption is explicit and supported by source inspection or the constitution.
   - Summarize findings and schema decisions in durable project documentation.
   - Check all success criteria in `validation.md` and record any unresolved issue rather than silently assuming an outcome.
