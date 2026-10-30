# Percival Notes MCP

Project-scoped instructions for the Notes MCP server. Read `README.md` and
`docs/` for its current tool contract and vault format.

## Ownership and approvals

This application is being built for Positronic Bean Labs
(https://labs.positronicbean.com). Bill Kopp (bill.kopp.dev@gmail.com) is the
sole owner of this application and its IaC infrastructure, the only project
contributor, and the only decision-maker and signatory.

Proceed with requested code, documentation, and local fixture work without
seeking duplicate approvals or repeated acceptance from another party. Record
an owner decision once and apply it consistently; repeat a check only when it
covers a distinct risk, changed artifact, or new target environment. Ask Bill
only when intent is materially ambiguous or an action has an external or
production consequence not already authorized. This authority does not itself
authorize publication, deployment, or production changes.

## Docker and operations

- This server is stdio-only. Keep stdout exclusively JSON-RPC; do not add TTY,
  published ports or HTTP healthchecks. The manager supplies the single init.
- The vault is persistent user data. Identify its exact bind and owner before
  work; never use a real vault for failure, restore, or rollback rehearsals.
- Percival's broker owns production containers and alone receives Docker access.
  Compose is a local development fixture, not a second production manager.
- Route operations through the owning manager: Percival WebUI/API or the
  Positronic `/mcp` TUI/CLI. Do not edit manager configuration/registry by hand.
  Reread revisions and image IDs; use an isolated vault and checksum for restore.
- Redact vault contents, environment values and tokens from logs/inventories.
  Verify with MCP `initialize`, `tools/list` and a safe read in the fixture.

## Verification

- Canonical suite: `uv run pytest -q`.
- Run focused tests when they cover a distinct regression or risk; avoid
  duplicating the same assertion in multiple checklists, reports, or approval
  steps. Reuse valid evidence for the same revision and environment.
- Docker recipe: inspect `docker-compose.yml`; keep the Notes vault as the only
  writable persistent mount. Never run cleanup against user data.
