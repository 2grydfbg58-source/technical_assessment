# Validation: MVP Hardening

- [x] The configured pipeline completes end to end on Databricks Free Trial, and its run identifier and output evidence are recorded.
- [x] The repository unit-test suite passes.
- [x] The full pipeline runs successfully on a clean environment or isolated fixture.
- [x] Quality, duplicate, and aggregation edge cases have been reviewed, with focused tests added for any uncovered Milestone 5-relevant behavior.
- [x] Final bronze, silver, and gold outputs exist; final gold exports are present as Parquet under the configured output location.
- [x] Rejection and backfill behavior is observable from recorded run or output evidence.
- [x] The README documents setup and how to execute the pipeline locally and on the configured Databricks target.

## Validation record

Validated 2026-11-27 on branch `feature/2026-11-27-mvp-hardening-validation`.

### Local validation

- `uv sync --group dev` — passed.
- `uv lock --check` — passed.
- `uv run pytest` — **23 passed** (Python 3.12.13).
- `.venv/bin/python -m py_compile notebooks/run_pipeline.py` — passed.
- `tests/test_bronze_silver.py::test_full_source_pipeline_smoke` passed. A full local run wrote all ten expected outputs to `data/output` and generated `data/output/run_manifest.json`.
- Verified Parquet row counts in `data/output`: Kamernet bronze/silver 46,722 each; Airbnb bronze/silver 9,913 each; quality 2; quality/rejection evidence 2,262; property revenue 16,946; postcode revenue 151; source comparison 81.
- The new `test_rejections_and_backfills_are_exported_as_quality_evidence` verifies one inferred-postcode backfill and one invalid-price rejection are exported and counted. Existing duplicate and aggregation/reconciliation tests also pass.

### Databricks Free Trial evidence

- `databricks bundle validate --skills-invoked databricks-core,databricks-dabs,databricks-jobs,databricks-serverless --strict --target dev --profile technical_assessment` — passed.
- `databricks bundle deploy --skills-invoked databricks-core,databricks-dabs,databricks-jobs,databricks-serverless --target dev --profile technical_assessment` — deployed successfully.
- `databricks bundle run --skills-invoked databricks-core,databricks-dabs,databricks-jobs,databricks-serverless amsterdam_investment_pipeline --target dev --profile technical_assessment` — **SUCCESS**.
- Job ID: `1097488801587617`; successful run ID: `627272186486302` (task run ID `801938985113483`); effective mode: `STANDARD`; execution duration: 60 seconds.
- Run URL: https://dbc-33b3016f-3675.cloud.databricks.com/?o=7474658174397239#job/1097488801587617/run/627272186486302
- Genie query verified all eight Delta tables in `workspace.default`: property revenue 16,946 rows; postcode revenue 151; source comparison 81; Kamernet bronze/silver 46,722 each; Airbnb bronze/silver 9,913 each; pipeline quality 2.
- The remote output directory `/Workspace/Users/marton.klecsany@gmail.com/.bundle/technical_assessment/dev/files/data/output` contains all ten expected Parquet/manifest files. The remote quality table reports 2,262 inferred postcodes and zero source-data rejections; the focused local fixture verifies rejection behavior.
- The initial deployment exposed that this workspace supports serverless only. The job was moved to serverless `STANDARD` with pinned pandas, PyArrow, and Shapely dependencies. A subsequent run exposed all-null Spark schema inference in bronze writes; explicit bronze/silver Spark schemas fixed it. The final deployment and run above passed.
- `README.md` documents local setup/execution and the Databricks target, including the serverless job environment.

All Milestone 5 validation criteria are verified.
