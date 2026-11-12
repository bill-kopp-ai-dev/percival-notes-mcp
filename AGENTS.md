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

## Image lifecycle: build, pin, test, decide, promote, clean

Positronic's MCP servers run in Docker. This agent is connected to the pinned
Notes image (`server id notes`, registry `$POSITRONIC_HOME/mcp/registry.json`,
config `$POSITRONIC_HOME/mcp/servers/notes.json`) and calls its tools directly
(`notes_get_status`, `notes_get_stats`, ...). That connection is the test
surface: a change is only validated when the new image is built, pinned and
exercised through this MCP.

Positronic owns the images it builds and pins. Never touch Percival's registry,
broker or commands; the two owners never cross.

### 0. Preconditions

- Canonical suite green before building (see Verification).
- Read current state first: `positronic mcp server show notes` (revision,
  `configurationId`, current pin), `positronic mcp server local-images`
  (authorized image IDs), `runtime_capabilities` or
  `positronic mcp maintenance capabilities` (host build grants).
- Building requires a host-granted recipe for this project (`project:
  percival-notes-mcp`, `recipe: canonical`, `serverId: notes`, `agentRoot:
  /home/bill/Projects/percival-notes-mcp`, `dockerfile: Dockerfile`,
  `versionFile: pyproject.toml`). The registered project name is
  `percival-notes-mcp`; `notes` is the MCP `serverId`, not the build project.
  If no recipe for `percival-notes-mcp` is listed, the submission is
  `policy-denied`: ask the operator to add it to the host policy file
  (`POSITRONIC_EXECUTOR_MAINTENANCE_POLICY_FILE`). The agent never self-grants
  a recipe and never builds through another project's recipe.
- Record the previous good image ID (A) and its revision before starting.

### 1. Build the image with the current code

- `image_build(project="percival-notes-mcp", recipe="canonical")` returns a
  `requestId`. The build directory comes from the granted recipe, never from
  arguments.
- Track it with `image_job(requestId, "status")`; `image_job(requestId,
  "cancel")` stops it. The host also runs the vulnerability scan and SBOM; a
  finding at or above the recipe's `rejectSeverities` blocks the job. The
  current recipe grant reports `scanGate: [HIGH, CRITICAL]` with
  `rejectSeverities: [HIGH, CRITICAL]`, so the scan **blocks** the job — treat
  a clean scan as a gate, not as evidence to be requested. (An earlier revision
  of this file described the gate as `report-only`; that changed on 2026-11-09
  when the owner set the rejection severities in the host policy.)
- Capture as evidence: image ID (`sha256:...`), source revision, version from
  `pyproject.toml`, scan and SBOM hashes.
- After a lost reply, reconcile with `runtime_capabilities` and `image_job` on
  the same `requestId`. Never resubmit the same intent blindly.

### 2. Authorize and pin the image in this agent

- `image_authorize(requestId)` authorizes the derived digest of the finished
  job. For an image not produced by a job:
  `positronic mcp server authorize-local <sha256:...> <authRevision>`.
- Pin it: `positronic mcp server update-image notes <sha256:...> <revision>`.
- `update-image` invalidates the previous `configurationId`: re-apply the
  configuration with `positronic mcp server configure notes <newRevision>
  --network none --mount '<vault-host-path>|/vault|rw' --tools <allowlist>`,
  then `positronic mcp server discover notes` and `activate` if it was
  deactivated. Keep the vault as the only writable persistent mount.
- Record the pin: image ID, revision, `configurationId`.

### 3. Test against the pinned image

- Exercise the real tools through this session (`notes_get_status`,
  `notes_get_stats`, and every tool the change touches). The server
  configuration allowlist gates what this agent can call; extend it with
  `configure` when the change touches a tool that is not yet exposed, and keep
  the allowlist minimal.
- Contract checks: `initialize` -> `tools/list` -> one safe read. Stdio only:
  no TTY, no published ports, no HTTP healthcheck, exactly one init.
- Use an isolated vault fixture for exploratory or destructive writes. The
  pinned vault is persistent user data; a rollback rehearsal never targets it.

### 4. Decide: approve or reject

- Approve only on evidence: canonical suite green, image conformance via
  `scripts/docker-ci-conformance.py` against the built image, and MCP-level
  validation on the pinned image. Record the decision, image ID, revision and
  evidence.
- Reject: leave the pin on A, remove the candidate image (step 5), fix, and
  restart the cycle. A rejected candidate must not stay pinned.

### 5. Promote and clean up

- Promotion = the approved image stays pinned and becomes the reference. The
  promoted pin is the new A for the next cycle.
- Cleanup order (the host refuses to remove an image that is still referenced):
  1. Unpin the obsolete image (re-pin A, or delete the installation, which
     keeps the image).
  2. `positronic mcp server revoke-local <sha256:...> <revision>` to drop it
     from the local authorization list.
  3. `image_remove(requestId)` (or `positronic mcp maintenance remove <jobId>`)
     to delete the image from the host Engine.
- Retention: keep only the last good image and the current promoted/candidate
  image per server (2 IDs), plus the A/B pair while a cycle is open. Accumulated
  test images are garbage; removing them is part of finishing the cycle, not an
  optional extra.
- Prohibited: `docker image prune -a`, `docker system prune`, `docker rmi -f`,
  `docker rm -f`, and removing any image that is pinned, authorized, referenced
  by a container, or needed for rollback. Removal happens by explicit image ID.
- When a prior cycle's image cannot be removed from this session (its build
  `requestId` is unknown), report the image IDs and ask the operator; do not
  improvise a generic Docker cleanup.

## Verification

- Canonical suite: `uv run pytest -q`.
- Run focused tests when they cover a distinct regression or risk; avoid
  duplicating the same assertion in multiple checklists, reports, or approval
  steps. Reuse valid evidence for the same revision and environment.
- Docker recipe: inspect `docker-compose.yml`; keep the Notes vault as the only
  writable persistent mount. Never run cleanup against user data.

## Records and references

- Journal one durable note per cycle: decision, image IDs, revisions and
  evidence. A note is evidence of a decision, never a substitute for it.
- Operational runbook (Percival owner):
  `/home/bill/Projects/nanobot/docs/operations/mcp-docker-local-runbook.md`.
  Global skills `mcp-docker-workflow` (build, pin, promote, remove) and
  `docker-desktop` (Desktop CLI inspection).
