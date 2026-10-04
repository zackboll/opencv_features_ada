# Agent workflow

Read task/rules and record current repo/worktree/branch/HEAD before changes.
Preserve unrelated local changes. An unpacked bootstrap is not yet a Git repo;
do not invent its starting SHA or treat absent CI runs as passing.

Work in the requested scope and make small reviewable changes. Do not amend,
force-push, merge, tag, release, open a PR, dispatch workflows, or create a
remote without explicit user authorization. Repository rules do not grant it.
When commits are authorized, use normal commits and report tested/pushed/PR
head equality. Stop at the requested review gate.

Classify failures from evidence: implementation, native behavior, fixture or
infrastructure. Reproduce before correcting; preserve diagnostics. Do not
silently change native algorithms or claim work happened in the background.
The initial native-unvalidated baseline needs Task 001, not a scope expansion.
