# AGENTS.md

This file is the Codex entrypoint for the cortex repo.

@./CLAUDE.md

`CLAUDE.md` is the canonical repo-local engineering guide. In particular,
Okis' Cortex Domain Model is now the target artifact for domain vocabulary:
Shared Kernel, Identity foundation, Brand/Publisher actors,
Discovery/Placement/Agent capability contexts, Library, and Insights.

Do not resurrect the old `brand_analytics` / `publisher_analytics` domain
split. Dashboard code is an API projection over `service/insights/`.

Critical Codex workflow rules for this repo:

- Never push directly to `develop`; use a feature branch and PR.
- Make code changes from an isolated git worktree.
- Preserve user work; do not revert unrelated changes.
- Run the relevant validation before calling work done.
- Trigger PR re-review with `@owl review`.

When working from the Mlytics coordinator workspace, also read
`../aigc_coordinator/AGENTS.md` if it exists. This file must remain useful on a
plain cortex clone where that sibling repo is absent.
