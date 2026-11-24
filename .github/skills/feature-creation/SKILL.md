---
name: feature-creation
description: Plan, implement, test, and track a feature from the next incomplete project milestone.
---

# Feature creation skill

Use this skill when asked to create or implement a project feature tracked by `specs/roadmap.md`.

## Workflow

1. **Inspect project state**
   - Read `specs/roadmap.md`, the relevant constitution documents in `specs/`, and the repository guidance that applies to the feature.
   - Review existing feature folders and tests for established naming, planning, implementation, and validation patterns.
   - Check the current branch, worktree status, and recent history. Preserve all pre-existing changes; do not stage or revert unrelated files.

2. **Select and scope the feature**
   - Find the earliest incomplete roadmap milestone with concrete implementation outcomes. Do not select completed milestones or stretch goals while an earlier implementation milestone remains incomplete.
   - Derive the feature scope from that milestone and its exit criteria. Reuse decisions already recorded in the constitution and avoid expanding scope.
   - Ask the user about material ambiguities that affect data semantics, behavior, interfaces, or acceptance criteria. Record confirmed decisions in the feature requirements.
   - If there is no eligible milestone, or the feature request conflicts with the roadmap, ask the user which scope to follow.

3. **Create the feature workspace**
   - Use the current date and a concise kebab-case feature name for the directory: `YYYY-MM-DD-feature-name/`.
   - Create a branch named `feature/YYYY-MM-DD-feature-name` before implementation. Inspect the worktree first; never discard changes to make a branch operation succeed. If a safe branch operation is not possible, explain the blocker and ask before proceeding.
   - Add these three files to the feature directory:
     - `plan.md`: ordered, numbered task groups with concrete deliverables.
     - `requirements.md`: context, decisions, scope, and a completion score. Start new work at `0/100`; only increase it based on verified requirements.
     - `validation.md`: observable, testable success criteria derived from the roadmap exit criteria and requirements.
   - Keep plans specific to the feature. Do not mark requirements or validation items complete before evidence exists.

4. **Implement the feature**
   - Unless the user requests planning only, execute task groups in order and keep directly related code, tests, and documentation consistent.
   - Inspect the relevant code and reuse existing patterns before editing. Make the smallest changes that satisfy the requirements.
   - Add focused tests for new or corrected behavior. Do not substitute tests for a real application or pipeline run when the validation criteria require one.
   - Do not claim completion for unavailable infrastructure or unverified behavior; record blockers and remaining work explicitly.

5. **Validate and track**
   - Run the smallest relevant tests first, then any additional build, lint, notebook, pipeline, or application checks required by `validation.md`.
   - Update validation checkboxes and the requirements score only from successful, recorded evidence. Report failures accurately and leave unmet criteria open.
   - Mark the roadmap milestone complete only when all of its exit criteria have been verified. Otherwise leave its status incomplete and summarize what remains.
   - Review the final diff and worktree. Ensure no unrelated changes were staged, overwritten, or included in the feature.

## Naming and artifact conventions

```text
feature/YYYY-MM-DD-feature-name
YYYY-MM-DD-feature-name/
  plan.md
  requirements.md
  validation.md
```

Use repository conventions where they are more specific. Keep dates consistent between the branch and directory, and use ISO dates.
