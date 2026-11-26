# Validation: Pipeline and Operations

- [ ] Source-comparison output includes separately named Kamernet and Airbnb PC4 rank fields with documented nullable types.
- [x] Each source's PC4s are ranked by that source's annual gross revenue in descending order; source ranks do not affect one another.
- [x] Equal totals share a standard competition rank and subsequent ranks contain the appropriate gaps.
- [x] A PC4 without eligible properties for one source has a null rank for that source while its comparison count and revenue remain zero.
- [x] Focused tests cover rank ordering, ties, rank gaps, independent source rankings, and absent-source nullability.
- [x] Reusable notebooks invoke package transformations without duplicating them, and the portable local pipeline continues to work.
- [x] Databricks job configuration is under `resources`; source/geography paths, output locations, and table names can be changed without editing transformation code.
- [x] README and `docs` explain how to configure and run the pipeline, rank fields and tie/null behavior, and the rationale for major rules.
- [x] Pipeline failures expose relevant source and quality context.
- [x] Focused tests and the repository test suite pass.
- [ ] The configured pipeline completes end to end on Databricks Free Trial, with run and output evidence recorded.

## Validation record (2026-11-26)

- **Passed:** `PYTHONPATH=src python3 -m pytest tests/test_revenue_gold.py` — 5 passed.
- **Passed:** `PYTHONPATH=src python3 -m pytest` — 22 passed.
- **Passed:** Ran `run_full_pipeline` on the supplied data with a temporary output directory; inspected all three Parquet products and confirmed 81 source-comparison rows and nullable `int64` rank columns.
- **Passed by code/configuration inspection:** source-specific competition ranking, notebook delegation to the package, configurable paths/table names in the bundle job, and source/quality context in `PipelineError`.
- **Incomplete:** The output schema has nullable `int64` rank fields, and the docs call the ranks nullable, but the docs do not explicitly state the `int64` field type.
- **Blocked:** Databricks end-to-end run and bundle validation were not run because the Databricks CLI is not installed in this environment. No deployment or remote job was attempted.
- The feature completion score remains **0/100** as defined in `requirements.md`; the required Databricks evidence is still outstanding.
