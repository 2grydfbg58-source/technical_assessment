---
name: changelog
description: Create and maintain a concise, dated project changelog from verified repository changes.
---

# Changelog skill

Use this skill when asked to create, update, or explain a project changelog.

## Workflow

1. Inspect the repository history and current worktree. Review relevant diffs and project documentation to identify completed changes.
2. Record only changes supported by repository evidence. Use commit dates for committed work and the current date for verified uncommitted work. Do not infer a date from filenames alone.
3. Keep the entry focused on user-visible features and meaningful fixes. Group entries under `Added`, `Changed`, `Fixed`, or `Removed` as appropriate.
4. Preserve existing changelog entries. Add the newest entry at the top, using an ISO date heading (`## YYYY-MM-DD`).
5. Distinguish implemented features from plans, and mention important scope limits where readers could otherwise infer more than was delivered.
6. Do not include secrets, personal data, or unrelated worktree changes. Never overwrite or stage unrelated user changes.
7. After editing, review the changelog diff for date accuracy, clear wording, and unsupported claims.

## Entry style

```markdown
## YYYY-MM-DD

### Added

- Short description of the completed feature and its user-visible outcome.
```

Keep entries concise, factual, and understandable without requiring the reader to inspect commits.
