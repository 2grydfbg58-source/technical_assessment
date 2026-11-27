# Plan: MVP Hardening

1. **Establish the hardening baseline**
   - Inspect the current pipeline configuration, job resource, tests, and existing run evidence.
   - Record the commands and Databricks Free Trial target needed to run the configured pipeline.
   - Preserve existing data contracts and the completed Milestones 0–4 behavior.

2. **Harden local pipeline behavior and tests**
   - Complete and run the unit-test suite for ingestion, cleaning, backfill, revenue, aggregation, and quality behavior.
   - Review duplicate, rejection, backfill, and aggregation edge cases; add focused tests for gaps that affect the Milestone 5 criteria.
   - Run the full pipeline against a clean environment or isolated fixture and verify its outputs and quality evidence.

3. **Run and verify the configured Databricks job**
   - Execute the configured pipeline end to end on Databricks Free Trial.
   - Capture the successful run identifier and evidence for the generated bronze, silver, and gold outputs.
   - Verify rejection and backfill behavior is observable from the run or its outputs; record any blocker without claiming success.

4. **Finalize exports and operational documentation**
   - Produce the final gold Parquet exports under the configured output location.
   - Update the README with setup and execution instructions, including the verified local and Databricks workflows.
   - Document evidence locations and operational observations without changing unrelated roadmap scope.

5. **Validate and close the milestone**
   - Re-run the relevant tests and verify the clean-run outputs, rejection/backfill evidence, and README instructions.
   - Record validation evidence and update the requirements score only for verified criteria.
   - Mark Milestone 5 complete only when every roadmap exit criterion, including the Free Trial run, has evidence.
