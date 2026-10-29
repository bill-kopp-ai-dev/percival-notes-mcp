# Percival Notes MCP

Project-scoped instructions for the Notes MCP server. Read `README.md` and
`docs/` for its current tool contract and vault format.

## Company approval

This project belongs to Positronic Bean Labs (PBLabs), owned by Bill Kopp.
Bill is the sole final decision-maker for decisions requiring owner or company
approval. Technical review, implementation, and routine operations may be
delegated without transferring final approval authority. This does not alter
runtime access or authorize publication, deployment, or production changes.

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
- Docker recipe: inspect `docker-compose.yml`; keep the Notes vault as the only
  writable persistent mount. Never run cleanup against user data.
