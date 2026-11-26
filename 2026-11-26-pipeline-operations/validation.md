# Validation: Pipeline and Operations

- [ ] Source-comparison output includes separately named Kamernet and Airbnb PC4 rank fields with documented nullable types.
- [ ] Each source's PC4s are ranked by that source's annual gross revenue in descending order; source ranks do not affect one another.
- [ ] Equal totals share a standard competition rank and subsequent ranks contain the appropriate gaps.
- [ ] A PC4 without eligible properties for one source has a null rank for that source while its comparison count and revenue remain zero.
- [ ] Focused tests cover rank ordering, ties, rank gaps, independent source rankings, and absent-source nullability.
- [ ] Reusable notebooks invoke package transformations without duplicating them, and the portable local pipeline continues to work.
- [ ] Databricks job configuration is under `resources`; source/geography paths, output locations, and table names can be changed without editing transformation code.
- [ ] README and `docs` explain how to configure and run the pipeline, rank fields and tie/null behavior, and the rationale for major rules.
- [ ] Pipeline failures expose relevant source and quality context.
- [ ] Focused tests and the repository test suite pass.
- [ ] The configured pipeline completes end to end on Databricks Free Trial, with run and output evidence recorded.
