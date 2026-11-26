# .har — Agent Harness (CLI / library profile)

This directory is the **agent harness** for this repository. It lets AI coding agents run the project in isolated git worktrees with optional Docker-backed shared infra.

Generated and maintained by [`har`](https://github.com/os-factory/har). Run `har env maintain` when the repo stack changes.

**The harness is how you run this project.** Launch a slot to exercise the code in isolation; don't hand-roll setup. If a harness command fails, fix the harness or report it — don't silently fall back to ad-hoc commands.

## What's in here

**Yours — the configuration surface** (edit freely; drift tracking records adaptations):

| File | Purpose |
|------|---------|
| `README.md` | This file — index of the harness |
| `harness.env` | Schema-validated config: worktree default, `HARNESS_INFRA_SERVICES`, toolchain provisioning (`HARNESS_ECOSYSTEM`, `HARNESS_INSTALL_CMD`), migrate/seed commands |
| `stages.json` | Registered stages, verification tiers, artifacts, slot limits, gate policy |
| `stages/` | Project-owned stage scripts registered from `stages.json` |
| `hooks/` | Optional lifecycle hooks (`pre-launch.sh`, `post-launch.sh`, `pre-verify.sh`, `pre-teardown.sh`, `post-teardown.sh`) |
| `plugins/` | Optional local plugins (`har plugin create <id>`) |
| `docker-compose.agent.yml` | Optional shared infrastructure containers (services listed in `HARNESS_INFRA_SERVICES`) |
| `.har/README.md` | Detailed instructions for coding agents |
| `STAGES.md` | Stage registry and script-contract guide |
| `justfile` | Optional shortcuts (requires `just`) |

**Generated state** (don't edit — `har env eject` vendors `.har/runtime/`):

| File | Purpose |
|------|---------|
| `manifest.json` | Runtime version, profile, checksums — managed by the har CLI |
| `runs/` | Run history from every entry point — `.har/runs/YYYY-MM-DD/HH-mm-ss_<stageId>_agent-<id>.json` (gitignored) |
| `artifacts/` | Stage outputs: reports, traces, logs |

No PM2 or `ecosystem.agent.template.cjs` in this profile — agents run project commands directly in their worktree.
## Quick start

**har CLI or MCP:**

```bash
har env launch 1
har env verify 1
har env verify 1 --full
har env teardown 1
```

In Cursor with HAR MCP configured: use `har_launch_environment`, `har_run_verification`, and `har_teardown_environment`.

CLI and MCP are the only entry points. `har env eject` vendors the runtime into
`.har/runtime/` for offline ownership (`node .har/runtime/har.cjs env …`).

Read **`stages.json`** and **`verificationStages`**. Optional: `har env add-plugin playwright`.

## Environment

| | |
|--|--|
| **Agent ID** | <id> |
| **Work dir** | Fresh session worktree per launch — see the launch output or `.har/slots/agent-<id>.json` |

**Never edit the main checkout** — launch FIRST, then make ALL file edits under the work dir from the launch output. An occupied slot always blocks a new launch — run `har env teardown <id>` (or `complete <id>`) first, then launch again.

```bash
har env agent <id> status
```

## Verification contract

Steps in `har env verify` are **project-specific examples** — adapt them to your stack
during scaffold / `har env maintain` / benchmark setup. The table describes
each tier's intent, not a fixed command list.

| Mode | Command | Typical steps |
|------|---------|---------------|
| Quick | `har env verify <id>` | Stock ecosystem smoke: compile / import / build conventions |
| Full | `har env verify <id> --full` | Stock conventional tests/lint + optional readiness smoke, **browser-e2e** when `stages/browser-e2e.sh` exists |

The stock commands are deliberately generic conventions keyed by
`HARNESS_ECOSYSTEM`. Replace them with the repository's real commands during
adaptation; do not leave Node/npm, Python, Go, Rust, Java, or Ruby defaults in
place when they do not match the project.

For repos that need runtime services, distinguish health from usability. If the
harness skips slow local-dev setup, document the skipped steps and add a minimal
bootstrap/readiness check when agents need default data, credentials, or an
authenticated workflow.

Use `har env launch 1 --no-worktree` only when working in the repo root.

## Definition of done

- [ ] Full verification returns `"status": "pass"` (`har env verify <id> --full`, MCP `har_run_verification` with `full: true`, or `har env verify <id> --full`)
- [ ] The slot is agent-usable for this repo's documented smoke workflow when runtime services are involved
- [ ] Full verify runs every registered stage in `stages.json` `verificationStages` (Playwright, custom checks, …) — when `stages/browser-e2e.sh` exists, adapt specs under `tests/` for UI changes
- [ ] New behavior has automated test coverage
- [ ] Changes committed **in the session worktree** with a clear message
- [ ] Present session handoff (summary, branch, preview URLs) and **wait for user** before `complete`, push, or PR
- [ ] On user approval of the default: push + open PR (when `gh`/GitHub MCP available), then `har env complete <id>` (or MCP `har_complete_environment`) — reuse last passing full validation + teardown, branch kept. Pass `--verify` / `verify: true` if the tree may have changed.

### Session handoff

After full verify and commit, stop and propose next steps. Never autonomously run
`complete`, `teardown`, `git push`, or open a PR. **Default recommendation:** when
`gh` or GitHub MCP is available, complete the slot **and** open a PR (push → PR →
`har env complete` / `har_complete_environment`). Offer complete-only or something
else as alternatives. If PR tooling is unavailable, recommend complete and report
the session branch for a manual push. Prefer `complete` over bare `teardown` when
the work succeeded. See `.cursor/rules/har-workflow.mdc` for the handoff shape.

Quick loop: MCP `har_run_verification`, `har env verify <id>`, or `har env verify <id>`

Stages are the harness's single vocabulary for checks: templates and custom stages compile to generic kinds in `.har/stages.json`, and you interact with them only through the registry (`har_run_stage`, `verify`), never stack-specific tooling. Authoring guide: `.har/STAGES.md`.

## Readiness

Adapt this section for the repository. For pure CLI/library repos, full verify
may be enough. If the project needs services, auth, seeded data, or a sample
workflow, document the required credentials/default data and wire a smoke into
`HARNESS_READINESS_CMD` or full verify.

## Run history

Every entry point — `./.har/*.sh`, `har env …`, MCP — runs the same packaged runtime and writes the same records under the main checkout `.har/runs/YYYY-MM-DD/`.

With git worktree slots, verification runs code in the worktree but run JSON stays in the main repo `.har/runs/`. Each record includes `workDir` when a slot is active.

## For coding agents

1. Read repo [`AGENTS.md`](../AGENTS.md)
2. Read this file and `stages.json` — this file is the harness reference:
   slot environment, readiness, definition of done, project commands
3. Drive the harness with HAR MCP tools or `har env …`; never hardcode ports —
   ask `har env agent <id> url`

## Project commands

```bash
# TODO: adapt for this repository. Examples:
# npm test
# pytest -q
# go test ./...
# cargo test
# make test
```

## Port & shared services (CLI profile)

This profile has **no PM2 app ports** — agents run project commands directly in their worktree. Port variables in `harness.env` exist for optional test servers and for shared Docker infra.

### Port allocation

| Layer | Scope | Rule | On conflict |
|-------|-------|------|-------------|
| Shared Postgres | Per machine | `HARNESS_DB_PORT_DEFAULT` | Scan `HARNESS_DB_PORT_SCAN_START..END` |
| Other compose services | Per machine | `HARNESS_*_PORT_DEFAULT` for that service | Scan configured ranges in `harness.env` |

When a repo adds a local HTTP server for integration tests, prefer reading ports from `.env.agent.<id>` or `har env agent <id>` rather than hardcoding values.

### Shared vs per-slot

| Resource | Model | Configuration |
|----------|-------|---------------|
| Postgres / Redis / mail / … | One shared container on a scanned host port | `HARNESS_INFRA_SERVICES` + matching vars in `harness.env` |
| Per-slot databases | Cloned from template DB when `db` is enabled | `har env launch` |
| Application code | Isolated git worktree per slot | `HARNESS_USE_WORKTREE=true` |

### Do not

- Hardcode `15432` or other default infra ports in tests — read `AGENT_DB_PORT` from `.env.agent.<id>` or `har_pg`
- Run raw `docker compose` for harness infrastructure — use `har env setup-infra`

## Do not

- Work around a failing harness command with ad-hoc setup — fix the harness or report the failure
- Edit `.env.agent.<id>` by hand
- Run `verify` before `launch` when e2e needs a running server
- Edit the main checkout — all edits go under the session work dir

## Maintaining this harness

When the project stack changes (new services, different test commands, new env vars):

```bash
har env maintain
```

The authoring agent reconciles the config surface and this README. Review changes before committing.

Customize through the contract — config (`harness.env`), stages (`stages.json` +
`stages/`), hooks (`hooks/`), plugins (`plugins/`). Drive the harness with
`har env …` or MCP. `har env eject` vendors `.har/runtime/` for offline ownership.
`har env doctor` validates the result.

## Session lifecycle

Every `launch` starts a **fresh session**: a new git worktree from the **main
checkout's current HEAD** at
`~/worktrees/<base-branch>-<sha4>-har-agent-<id>-<rand4>`, on a branch of the same name.
Switch that checkout to your intended base before launch. The session is recorded in
`.har/slots/agent-<id>.json` (the slot registry) — status, verify, and teardown resolve
the work dir through it. Make ALL file edits under the work dir printed by launch,
never in the main checkout.

- Occupied slots always block a new launch: `har env complete <id>` (or `teardown <id>`),
  then `har env launch <id>`. A new launch never chooses `main` for you — switch the
  main checkout to your intended base first.
- When every slot is occupied, do not pick one to free on your own. Run
  `har env status` and give the user a slot-by-slot summary: branch, bound work
  unit, what the session achieves, last verify, and whether its commits are merged,
  pushed, or unpushed (`git log <base>..<branch>`, PR state). Recommend which slot
  to close — merged or abandoned work with nothing left to do first; never one with
  unpushed commits — and free it with `complete` / `teardown` only after approval.
- `teardown` removes the worktree but **keeps the session branch** so you can push it
  or open a PR (`--delete-branch` to drop it).
- If launch fails after creating a worktree/env file, the registry records `status: failed`.
  Resume it instead of starting fresh: `har env launch <id> --resume` or `har env recover <id>`.
- `har env complete <id>` finishes a session: reuses the last matching passing
  full validation, then teardown — branch kept. Pass `--verify` to re-run full
  verify if the tree may have changed.
- `--no-worktree` runs the slot from the repo root instead (single-agent mode).
