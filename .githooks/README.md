# Git hooks

Shared, dependency-free git hooks for this repository. They are plain POSIX
`sh` — no Node, Python or other runtime is required — so the identical hooks
are used across every project in the workspace.

## `commit-msg`

Enforces [Conventional Commits](https://www.conventionalcommits.org/) on every
local commit:

    <type>[(scope)][!]: <description>

- **type** — one of `feat fix docs style refactor perf test build ci chore revert`
- **scope** — optional, e.g. `feat(nav): …`
- **!** — optional, marks a breaking change
- description is non-empty, has no trailing full stop, and the header is 100
  characters or fewer (72 or fewer preferred)
- a body, if present, is separated from the header by a blank line

Merge, revert, fixup!/squash! and reapply commits are skipped. The hook runs on
**local commits only** — dependabot and GitHub web-UI commits bypass it.

## Activation

Hooks are shared via `core.hooksPath`. After cloning, run once:

    git config core.hooksPath .githooks
