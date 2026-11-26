---
name: feature-validation
description: Run and report evidence-based validation for a feature using its validation checklist and repository test commands.
---

# Feature validation skill

Use this skill when asked to validate, test, or check completion of a feature, especially one with a `validation.md` checklist.

## Workflow

1. **Identify the feature and preserve repository state**
   - Use the feature folder named in the request or current context. If it is not clear which feature is meant, ask the user.
   - Read the feature's `validation.md`, `requirements.md`, and relevant `plan.md`, plus applicable repository instructions and test documentation.
   - Inspect the current branch and worktree before running commands. Do not discard, stage, commit, or overwrite pre-existing changes.

2. **Turn criteria into a validation matrix**
   - List each criterion and identify what evidence would prove it: a focused test, broader test suite, build/type check, lint, application or pipeline run, output inspection, or manual/external confirmation.
   - Locate the project's existing test and validation commands from manifests, CI configuration, and documentation. Prefer repository-defined commands and existing dependencies.
   - Use the smallest relevant check first. Add broader checks only when required by the checklist, repository conventions, or a failure that warrants investigation.
   - Do not equate passing unit tests with successful application, integration, deployment, data-quality, or infrastructure validation.

3. **Run checks safely**
   - Execute relevant checks without changing product behavior. Do not create or alter implementation code just to make validation pass.
   - Avoid destructive commands, production data changes, deployments, external service mutations, or commands with unclear side effects. Ask for approval before any such action.
   - Do not install dependencies unless the project manifest changed or a required validation command reports a missing dependency. Do not silently skip a check because its tooling is unavailable.
   - Capture the exact commands and their outcomes. If a command fails, inspect the failure and report the actionable cause; do not retry repeatedly without a reason.

4. **Update validation records accurately**
   - Mark a checklist item complete only when its stated outcome is directly supported by successful evidence.
   - Leave unmet items unchecked. For checks that cannot run in the current environment, record the blocker and the evidence or access still needed; do not present them as passing.
   - Distinguish `failed`, `blocked`, and `not run` in the report. Do not alter requirements, acceptance criteria, or the feature scope to make results appear complete.
   - Update a completion score only when the feature's existing requirements define how it is calculated and the score is supported by verified criteria.

5. **Review and report**
   - Review edits to validation artifacts and confirm unrelated worktree changes remain untouched.
   - Summarize passed, failed, blocked, and unrun checks, including exact commands and concise outcomes. State clearly whether the feature meets all validation criteria.
   - Do not claim full validation when any required criterion remains unverified.

## Validation principles

- Prefer reproducible, project-native checks over ad hoc substitutes.
- Validate the acceptance criteria themselves, not merely that a test command exits successfully.
- Treat manual review, external credentials, deployed-environment checks, and user acceptance as separate evidence requirements.
- Do not commit or push changes unless the user explicitly asks.
