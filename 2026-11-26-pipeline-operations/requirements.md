# Requirements: Pipeline and Operations

## Score

- **Feature completion score:** 0/100 (planning only; implementation and acceptance criteria are not yet verified).

## Context

This feature addresses **Milestone 4: Pipeline and Operations**, the earliest incomplete implementation milestone in `specs/roadmap.md`. Milestones 0–3 are complete. The existing portable package produces source-comparison totals but does not rank PC4s; reusable package modules exist, while notebook entry points and job configuration under `resources` are not yet present.

The feature adds independent source rankings and completes the pipeline organization, configurable Databricks job, and operational documentation required by the milestone.

## Decisions

- Add `kamernet_pc4_rank` and `airbnb_pc4_rank` to each source-comparison PC4 row.
- Compute each source's ranks independently over PC4s with eligible properties, ordered by that source's annual gross revenue descending.
- Use standard competition ranking: equal revenue totals share a rank, and the next distinct total receives the rank it would have held without ties (for example, `1, 1, 3`).
- A source with no eligible properties at a PC4 has a null rank, even though its existing comparison count and revenue total remain zero.
- Preserve the existing source-comparison grain, revenue semantics, eligibility rules, and Milestone 3 outputs except for the additive rank fields.
- Keep transformation logic reusable in the existing Python package, with Databricks notebooks serving as orchestration entry points.
- Parameterize source paths, geography paths, output locations, and table names through job or bundle configuration rather than transformation-code edits.
- Use the existing Databricks Free Trial target for the required end-to-end job validation. Do not mark the milestone complete without an observed successful run.

## Scope

### In scope

- Separate source-specific PC4 ranking fields, nullability, ranking behavior, and tests.
- Reusable package and notebook organization for pipeline execution.
- Databricks job configuration under `resources`, integrated with the existing bundle.
- Configurable paths and table names.
- README and `docs` updates describing setup, operation, rank semantics, configuration, and rationale.
- Local test validation and an end-to-end Databricks Free Trial run.

### Out of scope

- Reopening or changing completed bronze/silver or revenue/gold acceptance criteria.
- Combining Kamernet and Airbnb into one rank.
- Changing source eligibility, revenue formulas, postcode recovery, or comparison grain.
- Dashboards, CI/CD deployment, pre-commit hooks, environment promotion, or other stretch goals.

## Completion

This feature is planned but not implemented. Keep the score at 0/100 until requirements are verified with recorded evidence. Keep the Milestone 4 roadmap status incomplete until every milestone exit criterion, including the Databricks Free Trial run, has passed.
