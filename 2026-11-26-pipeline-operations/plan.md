# Plan: Pipeline and Operations

1. **Define ranking and operational contracts**
   - Add separate nullable `kamernet_pc4_rank` and `airbnb_pc4_rank` fields to the source-comparison product.
   - Rank each source's PC4s independently by that source's annual gross revenue, descending, using standard competition ranks for ties.
   - Preserve the existing source-comparison grain and comparison fields; a source with no eligible properties at a PC4 has a null rank.
   - Define configurable input paths, output locations, and table names without changing transformation behavior.

2. **Implement and test source-specific PC4 ranking**
   - Extend the gold aggregation to calculate both ranks independently.
   - Cover unequal totals, tied totals and resulting rank gaps, source-specific rank order, and absent-source null ranks with focused tests.
   - Keep rank values and revenue totals aligned to the same eligible property and known-PC4 rules used by the existing gold products.

3. **Organize the reusable pipeline and notebook entry points**
   - Refactor reusable ingestion, cleaning, gold, quality, and orchestration code into the existing Python package where needed.
   - Add reusable Databricks notebooks that invoke the package rather than duplicating transformation logic.
   - Preserve the portable local pipeline and its existing outputs.

4. **Add configurable Databricks job resources**
   - Add job configuration under `resources` and connect it to the existing Databricks bundle configuration.
   - Parameterize source and geography paths, output locations, and table names through configuration or job parameters.
   - Ensure changing deployment configuration does not require editing transformation code.

5. **Document execution, configuration, and rationale**
   - Update the README with local setup, pipeline execution, and Databricks job instructions.
   - Document the rank fields, ranking and tie rules, nullability, configuration parameters, and major data-quality and revenue decisions in `docs`.
   - Describe how pipeline failures expose source and quality context.

6. **Validate locally and on Databricks**
   - Run focused rank tests and the existing test suite.
   - Validate that ranking schemas and behavior are documented and that configuration changes do not require code edits.
   - Run the configured job end to end on Databricks Free Trial and record output and failure-context evidence.
   - Mark the roadmap milestone complete only after every exit criterion has verified evidence.
