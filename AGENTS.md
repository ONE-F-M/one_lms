# AGENTS.md

This repository hosts the `one_lms` Frappe app.

## Commit Format

All commits must use conventional commit titles so `commitlint.config.js`, the
commit-msg pre-commit hook, and CI linting can validate them.

Use this format:

```text
<type>(<scope>): <subject>
```

Allowed types are:

- `build`
- `chore`
- `ci`
- `docs`
- `feat`
- `fix`
- `perf`
- `refactor`
- `revert`
- `style`
- `test`
- `deprecate`

For sprint work, use the work item ID as the scope:

```text
chore(WI-000795): align commitlint with Frappe
```
