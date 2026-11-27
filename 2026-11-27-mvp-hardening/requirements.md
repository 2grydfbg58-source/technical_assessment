# Requirements: MVP Hardening

## Score

- **Feature completion score:** 0/100 (planning only; no implementation or validation evidence has been produced for this feature).

## Context

This feature addresses **Milestone 5: MVP Hardening**, the earliest incomplete implementation milestone in `specs/roadmap.md`. Milestones 0–4 are marked complete. The milestone requires a verified end-to-end Databricks Free Trial run in addition to local tests, a clean pipeline run, edge-case review, final gold exports, observable rejection/backfill behavior, and README setup and execution guidance.

## Decisions

- Preserve the existing source semantics, data contracts, revenue calculations, ranking rules, and completed milestone behavior.
- Keep hardening scoped to the Milestone 5 outcomes and exit criteria; do not begin stretch milestones.
- Validate unit tests and the full pipeline locally using the repository's existing test and execution patterns.
- Treat the configured Databricks Free Trial end-to-end run as a required acceptance criterion. Local success or configuration inspection alone does not satisfy it.
- Require run and output evidence for the remote execution; if access or authorization prevents the run, record the blocker and leave the milestone incomplete.
- Start the score at 0/100 and increase it only when requirements have recorded verification evidence.

## Scope

### In scope

- Complete unit-test coverage and execution for pipeline behavior.
- Clean-environment or isolated-fixture full pipeline execution.
- Review of quality, duplicate, aggregation, rejection, and backfill edge cases.
- Databricks Free Trial end-to-end execution with run and output evidence.
- Final gold Parquet exports.
- Observable rejection and backfill behavior.
- README setup and execution instructions.

### Out of scope

- Changing business assumptions, data semantics, or completed Milestone 0–4 acceptance criteria.
- CI/CD deployment, pre-commit hooks, dashboards, streaming, area-level enrichment, or other stretch goals.
- Claiming remote execution success without an observed run and recorded evidence.

## Completion

This feature is complete only when every Milestone 5 exit criterion has verified evidence. Keep the roadmap milestone incomplete and the score at 0/100 until that evidence is recorded. Planning artifacts alone do not count as implementation or validation.
