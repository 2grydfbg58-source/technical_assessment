# Plan: Revenue and Gold

1. **Define revenue and gold contracts**
   - Add typed, reusable revenue and gold transformation modules following the existing `amsterdam_investment` package patterns.
   - Specify property, postcode, and source-comparison schemas, their keys, and the fields needed to audit source eligibility.
   - Keep annual gross revenue in EUR; do not introduce occupancy adjustments or costs.

2. **Calculate eligible property revenue**
   - Calculate Kamernet annual gross revenue as monthly rent multiplied by 12, using only Amsterdam records with `status="true"` and a valid positive revenue input.
   - Calculate Airbnb annual gross revenue as nightly price multiplied by 365, using only geographically in-scope Amsterdam records with a valid positive revenue input.
   - Deduplicate Airbnb gold candidates by the existing provisional content hash, retain duplicate counts, and document that the hash does not prove real-world listing identity.
   - Preserve valid Amsterdam property revenue when its PC4 is unknown; exclude records without a known PC4 only from postcode aggregation.

3. **Build postcode and source-comparison products**
   - Aggregate each source's eligible property revenue by known PC4 and source, producing unique postcode/source rows and the documented comparison measures.
   - Ensure property and postcode products have unique keys at their declared grains.
   - Reconcile postcode totals to the known-PC4 property subset and overall property totals to eligible, deduplicated silver inputs.

4. **Export and document gold datasets**
   - Write the property, postcode, and source-comparison products as Parquet under `data/output`.
   - Document output schemas, grains, keys, formulas, eligibility, duplicate treatment, and reconciliation rules.
   - Integrate the gold transformations with the existing portable pipeline without changing bronze/silver behavior.

5. **Add focused tests and validate the milestone**
   - Test formulas, source eligibility, duplicate handling, unknown-PC4 behavior, aggregation grains, Parquet schemas, and total reconciliation.
   - Run the focused suite and the full supplied-data gold pipeline; record evidence for each Milestone 3 exit criterion.
   - Leave the roadmap milestone incomplete unless every exit criterion is verified.
