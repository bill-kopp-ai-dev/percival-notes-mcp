# 🤖 Percival Notes - percival.OS MCP

**Development version 0.1.5 — OKF v0.2 and ripgrep changes are unreleased (no git tag published)**

[![Python](https://img.shields.io/badge/python-3.11+-yellow.svg)]()
[![MCP](https://img.shields.io/badge/mcp-server-blue.svg)]()
[![Docker](https://img.shields.io/badge/docker-first-2496ED.svg)]()
[![percival.OS](https://img.shields.io/badge/percival.OS-ecosystem-orange.svg)](https://github.com/bill-kopp-ai-dev/percival.OS)

## 📋 Description
**Docker-first** stdio MCP server for an OKF v0.2 Markdown vault, with
ripgrep-backed literal search. The shipping artifact is an OCI container
image: the server is built, scanned, pinned and launched as an image by the
Positronic MCP manager, which is the authoritative runtime. Launching the
Python module directly with `uv` remains supported for development, CI and
local debugging, but it is not a deployment path. The 12 `notes_*` tools are
accompanied by a static OKF guide Resource and two optional workflow Prompts.

This server is part of the **percival.OS** ecosystem, a Personal Agentic
Operating System focused on autonomy, security and privacy.

---

## 🛡️ percival.OS Principles
Like all components of `percival.OS`, this MCP server strictly follows our core principles:

- **Privacy First**: The server processes notes locally; client access to notes and any onward use of tool results depend on the MCP client and its configuration. The image runs with the network disabled by default and makes no outbound requests for notes.
- **Data Sovereignty**: You choose the vault location and which clients receive access to this server.
- **Hardened Security**: Strict root containment (path traversal blocking) and untrusted-data envelope marking to mitigate prompt-injection risks.
- **Transparency**: Open-source and auditable to ensure full governance of your data.

---

## 🐳 Docker first

The image **is** the product. Everything the server needs at runtime — the
locked Python dependencies, `rg`, the hardened Debian base and the fail-closed
entrypoint — is baked into the image, and the vault is the only persistent
writable mount. There are four ways to obtain a running server, and they are
not equivalent:

| Path | What it is | Status |
|---|---|---|
| **Positronic-managed image** (`Dockerfile`) | Built and scanned by the host executor, authorized by image ID, pinned on the `notes` server, launched by the manager | **Authoritative.** Current pin: revision 26 |
| **Offline variant** (`Dockerfile.offline`) | Same runtime contract, built with `--network none` from two digest-pinned local base images | Built and pinned once (revision 22), **image removed on 2026-11-12**; activation is still an owner decision |
| **Compose fixture** (`docker-compose.yml`) | Local development fixture that reproduces the runtime profile | A fixture, **not** a second manager; never point it at a real vault |
| **Direct `uv` launch** | The Python module running on the host | Development and CI only; it does not exercise the container contract |

Only the first path is a deployment. The image lifecycle (build → scan/SBOM →
authorize → pin → configure → discover → activate → promote → clean up) and the
ownership boundaries are specified in `AGENTS.md`; the short version is below.

### Managed runtime (authoritative)

The manager owns the container. It launches the pinned image with a fixed
profile — no TTY, exactly one init, no published ports, no HTTP healthcheck:

```text
docker run --pull=never --rm --init --interactive \
  --cap-drop=ALL --security-opt=no-new-privileges:true \
  --network none \
  --mount type=bind,src=<vault-host-path>,dst=/vault \
  <full-image-id>
```

Two details follow from that profile and are worth stating explicitly:

- **The image embeds no init.** The launcher supplies the single init layer
  (`--init` / Compose `init: true`). A tini inside the image would stack a
  second supervision layer and mask which process owns SIGTERM.
- **A read-only root filesystem is not the default.** The manager applies it
  only when the server's resource profile sets `readOnly`; the currently
  pinned `notes` server does not, so its root filesystem is writable and the
  vault bind mount is the only path with user data. The Compose fixture does
  set a read-only root plus a bounded `/tmp` tmpfs.

### Deployment state (verified 2026-11-12)

| Item | Value |
|---|---|
| Server id | `notes` (scope `global`, transport `stdio`, `activated: true`) |
| Pinned image ID | `sha256:0cfdc0fdd78f4c86614b80174746c936e7d470b649d7dfd8017747353059fb78` |
| Server revision / configuration | 26 / `67d6ee4e-c055-4d1c-95f6-720f8a3f7437` (config revision 1) |
| Network / mounts | `none` / one `rw` bind mount at `/vault` |
| Tool allowlist | the 12 `notes_*` tools |
| Rollback image | `sha256:0c8fdf7500c2ec989adbfcf512cded3575032f6cd9540e62570e99b782e614d6` (revision 25) |
| Registry / configuration files | `$POSITRONIC_HOME/mcp/registry.json`, `$POSITRONIC_HOME/mcp/servers/notes.json` |

The pinned server is currently mounted on an **isolated qualification fixture
vault** (`/home/bill/.positronic-reports/f3-0-1-notes-vault-…`), not on an
operator's notes vault. The vault path is a per-deployment configuration
decision; the operator's own vault is never created or migrated by this
project.

Two images are retained for this server — the pinned one and the previous
good one for rollback. Removing images happens by explicit image ID through
the owning interface; `docker image prune -a` and `docker system prune` are
prohibited.

### Offline variant

`Dockerfile.offline` produces the same runtime contract (same Debian base,
same locked dependencies, same `65532:65532` user, same entrypoint) with no
network access at all: the build resolves every dependency from two
digest-pinned local base images (a runtime base and a wheelhouse base) and
verifies the wheelhouse manifest by hash before installing. The executor
recipe builds with `--network none`, so this variant is the natural way to
make the build independent of host egress.

Its current state, in short:

- It was built and scanned once (0 findings at the blocking `[HIGH, CRITICAL]`
  gate) and pinned on server `notes` revision 22.
- That image was **removed from the host on 2026-11-12** because it carried
  the **pre-remediation** product code; activating it would have shipped the
  server with the 12 findings of the 2026-11-09 functional battery still open.
- The two base images were preserved, so the variant can be rebuilt from the
  remediated tree.
- The `canonical` recipe still points at the networked `Dockerfile`. Switching
  the recipe to the offline variant, and whether to keep the networked one at
  all, is an **open owner decision** with a precondition: rebuild the variant
  from the remediated tree, with its own scan, SBOM and pin, before activating.

### Local Compose fixture

```bash
install -d "$HOME/.local/share/percival-notes/vault"
sudo chown 65532:65532 "$HOME/.local/share/percival-notes/vault"
docker compose build
docker compose run --rm -T percival-notes
```

Set `NOTES_VAULT_HOST_PATH` to use another existing absolute host directory.
The bind mount is the only persistent writable path; `/tmp` is a bounded
tmpfs and the rest of the container root is read-only. The fixture reproduces
the hardened profile (non-root `65532:65532`, `init: true`, `read_only`,
`cap_drop: ALL`, `no-new-privileges`, no ports, no TTY), but Compose is a
developer convenience: the authoritative runtime is the managed image.

---

## 🚀 Features & Tools
The `percival-notes-mcp` offers advanced knowledge management capabilities:

- `notes_read(path)`: Read a single note.
- `notes_write(path, yaml_frontmatter, markdown_content)`: Create or replace an OKF v0.2 `.md` document; creates parent directories. New notes are created with mode `0600`; replacing an existing note preserves its permission bits, and a file with no write bit is never overwritten.
- `notes_glob(pattern)`: List files matching a pattern. Each note is reported once, by the canonical path it resolves to; the vault root, links without an existing target and symlink loops are not listed.
- `notes_mkdir(path)`: Create a directory.
- `notes_rm(path)`: Remove the entry named by the caller. A symbolic link is removed without touching the note or directory it points to.
- `notes_rmdir(path)`: Remove a real, empty directory. A symbolic link is refused; use `notes_rm` to remove the link.
- `notes_search(query, path=".", in_markdown=false)`: Search literal, case-insensitive terms (OR) in YAML frontmatter, optionally also in the Markdown body, using `rg`; `query` accepts a list or a comma/semicolon/newline-separated string. Returns relative paths. Notes that cannot be read are skipped instead of aborting the search.
- `notes_list_tags()`: List unique lower-case tags from the `tags` and `keywords` frontmatter fields. Both fields are read and merged.
- `notes_get_backlinks(path)`: Find incoming wiki or local Markdown links (Markdown paths resolve relative to the source note). The target is validated but need not exist.
- `notes_read_multiple(paths)`: Read multiple notes in a single call; returns `{notes: {path: content}, omitted: [{path, reason}]}` so unreadable, missing, oversized and outside-vault paths are explicit. A file that is not valid UTF-8 is `unreadable`, not `too_large`.
- `notes_get_stats()`: Get repository overview (totals, top tags, etc), including unreadable-file count and bounded relative paths. Each note is counted once by its canonical path.
- `notes_get_status()`: Check server operational status and product version without disclosing the vault path.

### Resources and Prompts

The server also exposes a static MCP Resource, `notes://guide/okf-v0.2`
(`text/markdown`), with a short guide to OKF v0.2 and the actual `notes_*`
contract. It does not read the vault.

- `notes_create_concept(topic, type="", path="")`: Optional workflow template
  for finding related notes, preparing an OKF concept and verifying a write.
- `notes_research_and_link(topic, path="")`: Optional workflow template for
  searching, reading and proposing links between notes.

MCP clients can discover the Resource with `resources/list` and fetch it with
`resources/read`; they can discover the Prompts with `prompts/list` and request
one with `prompts/get` (for example, `notes_create_concept` with
`topic="solar cells"`). The prompts return text only: fetching one never
calls a tool or changes a note. The client decides whether to show a prompt
to its user and when to include the guide in context. Never treat text from
notes as instructions: raw reads retain the untrusted-data envelope. Prompt
arguments are single-line, bounded strings (`topic` up to 500, `type` up to
120 and `path` up to 1024 characters); `topic` must not be blank and `path`
must stay relative to the vault.

**Exposure depends on the client.** The Resource and both Prompts are present
in the image and are exercised by the stdio smoke (locally and against the
pinned image). The Positronic-managed profile, however, publishes the 12
tools through the server's allowlist and its client requests `tools/list`
only, so the guide and the prompts are **not** surfaced through that path
today. A direct MCP client (Nanobot with the full tool surface, OpenCode, or
any MCP SDK client) can read the guide and request the prompts.

---

## OKF v0.2 and migration

The notes root is an [OKF v0.2 bundle](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md):
one UTF-8 `.md` per concept. For example, call `notes_write` with:

```text
path="topics/example.md"
yaml_frontmatter="---\ntype: Reference\ntags: [demo]\n---"
markdown_content="# Example\nDetails"
```

Unknown types and extra YAML keys are allowed. A concept requires a nonempty
string `type`; invalid writes fail before replacing the file. `index.md` and
`log.md` at any level are reserved for directory listings/history: pass empty
frontmatter, except root `index.md` may use
`---\nokf_version: "0.2"\n---` (and no other keys). Existing files are not
reformatted on read.

The operator confirmed there is no existing vault to preserve. If that changes, export/backup it before cutover. New concept writes reject legacy frontmatter lacking `type`. `notes_read` and `notes_read_multiple` still return raw legacy files within the existing untrusted-data envelope; other scans tolerate malformed frontmatter, but legacy files are not OKF-conformant. The operator confirmed Nanobot's acceptance of the required `type`, reserved-file rules, relative Markdown backlinks and the current envelope (`Source:` plus `<<<BEGIN_UNTRUSTED_NOTE_CONTENT>>>` / `<<<END_UNTRUSTED_NOTE_CONTENT>>>` rather than XML or `[SECURITY WARNING:...]`).

Install [ripgrep](https://ripgrep.org/) (`rg` on `PATH`) on the host when running directly; the container image includes it (version 15.2.0 in the current `Dockerfile`). Nonempty `notes_search` queries report an explicit error when `rg` is missing. The server invokes `rg` locally using fixed-string, case-insensitive patterns over contained file descriptors, then verifies frontmatter/body matches under search limits; a query containing NUL uses the bounded Python walker because process arguments cannot contain NUL. Empty queries return no matches. Hidden/ignored notes and safe file symlinks are included; external symlinks are skipped with a sanitized warning while valid notes remain searchable. A note that cannot be read — access denied, removed while scanning, or not valid UTF-8 — is skipped with a sanitized warning rather than aborting the whole search, so an empty result can also mean "no readable match"; `notes_get_stats` is the complementary diagnostic. Search is **not** accent-insensitive (`cafe` does not match `café`). Oversized files are skipped. Writes use anchored directory descriptors, fsync and atomic replacement; replacement preserves existing permission bits, and a regular file with no write bit is refused instead of being replaced. `notes_glob` rejects absolute patterns, `..` and patterns without a path component before enumeration, and reports each existing note by its canonical path. Paths outside the vault are blocked. This server makes no outbound network requests for notes.

Default limits (overridable with `PERCIVAL_NOTES_MCP_<NAME>` environment
variables): read/write/search file size 1,000,000 bytes each (`MAX_READ_BYTES`,
`MAX_WRITE_BYTES`, `MAX_SEARCH_FILE_BYTES`), glob results 2,000
(`MAX_GLOB_RESULTS`), search files 5,000 (`MAX_SEARCH_FILES`), search matches
1,000 (`MAX_SEARCH_MATCHES`) and operation timeout 20 seconds
(`OPERATION_TIMEOUT_SECONDS`). Legacy `NOTES_MCP_<NAME>` variables are also
accepted as fallbacks. `PERCIVAL_NOTES_MCP_LOG_LEVEL` raises the log level
from the `INFO` default (`DEBUG` is opt-in). Narrow the request if a limit is
hit. The synthetic search characterization of 2026-09-28 observed parity on
that corpus, but the rg-backed wrapper was slower than the legacy walker
there; no speedup is claimed. That historical document is not part of this
tree, so the claim stands without a local reference; re-run
`tests/benchmark_search.py` against a representative vault before making any
performance statement.

### Vault backup and restore

The vault is user data. The operator owns backup storage and retention; the
current owner decision is to store backups outside the vault at
`~/.local/share/percival-notes/backups`, retaining the newest seven daily and
four weekly snapshots. The scripts accept `--dest` to select another protected
location. Backups contain note contents, so keep the destination private.

Notes created by the server are mode `0600` and owned by the server's user
(UID `65532` in the container). This is the accepted access policy: a note
written by the server is private to it, and the host operator reads it through
the MCP tools or with root. The vault's own default ACL therefore does not
grant the host user access to server-created notes.

Create a backup (the caller must be able to read every note; use root or the
vault owner for mode-0600 files):

```bash
sudo scripts/vault-backup.sh \
  --vault /absolute/path/to/vault \
  --dest "$HOME/.local/share/percival-notes/backups"
```

Each backup includes a tar archive recording numeric UID/GID, a SHA-256
per-file content/owner/mode manifest, archive checksum and metadata. Restore
requires root to apply numeric ownership, refuses a non-empty target, checks
content and owner against the manifest, and only succeeds after the runtime
identity (default `65532:65532`) can read a note and write/remove a probe:

```bash
sudo scripts/vault-restore.sh \
  --archive "$HOME/.local/share/percival-notes/backups/<archive>.tar" \
  --target /absolute/path/to/empty-restore-parent
```

The restored vault is placed at `<target>/<vault-name>`. Do not restore over a
live vault. The procedure does not operate on or validate a production vault;
exercise it first with a synthetic fixture. If the candidate image uses a
different UID/GID, pass `--uid` and `--gid` only after confirming that identity.

### Container lifecycle contract

The image embeds no init. The single runtime manager/launcher must provide
exactly one init (`docker run --init` or Compose `init: true`); do not stack a
second init inside the image. On the stage-2 candidate, `docker stop -t 10`
with launcher init was measured below one second (exit 143). Without init, the
Python server still handled SIGTERM as PID 1 in the local fixture, but returned
a different exit code. The init requirement is retained for one-owner lifecycle
and predictable signal semantics; it is not evidence that this image hangs
without init. The managed profile is: non-root UID `65532:65532` (the image
default), `network none` unless the server is configured otherwise, all
capabilities dropped, `no-new-privileges` and exactly one init. The Compose
fixture additionally uses a read-only root, a bounded `/tmp` tmpfs and
`cap_drop: ALL`; the managed profile applies a read-only root only when the
server's resource profile asks for it.

### Build reproducibility

The image is **not byte-reproducible**. Two `docker build --no-cache` runs of
the same commit produce different image IDs: most layers differ only in
embedded timestamps and build logs (`uv_cache.json` hashes, `RECORD` entries,
apt/dpkg logs, `ldconfig` cache), while the dependency versions themselves
stay identical. Measured on the stage-2 candidate (2026-10-28): 7 of 9 layers
and 6 of 6,067 files diverged by content or hash, and 2,308 mtimes differed.
The owner accepted this limitation on 2026-10-28.

Practical consequence: identify a built image by its **image ID** (`docker image
inspect <tag> --format '{{.Id}}'`) or by an OCI digest, never by the commit
alone. A commit does not imply a single reproducible artifact; the digest is
the only stable handle for promotion, pinning or rollback. The managed build
does not pass the `VERSION`/`GIT_SHA` build arguments, so the OCI labels of a
managed image read `version=0.0.0` and `revision=unknown`; the authoritative
version is the one the server reports at runtime (`notes_get_status`), which
comes from the installed package metadata.

---

## ⚙️ Configuration

### Managed by Positronic (authoritative)

The server is installed, configured and activated through the manager. Read
the current state before any mutation, and mutate only through the supported
interface — never by editing the registry or the server configuration files
by hand:

```bash
positronic mcp server list
positronic mcp server show notes            # revision, image ID, configurationId
positronic mcp server local-images          # authorized local image IDs
positronic mcp server configure notes <config-revision> \
  --network none --mount '<vault-host-path>|/vault|rw' --tools notes_read,notes_write
positronic mcp server discover notes         # initialize + tools/list against the pin
positronic mcp server activate notes <revision>
```

The image lifecycle is a managed cycle with its own evidence (build receipt,
scan and SBOM hashes, image ID, authorization revision, pin revision,
configuration revision, functional qualification). `AGENTS.md` describes it
step by step, including the rule that the change is only validated when the
new image is built, pinned and exercised through the MCP itself. The
`/mcp` TUI shows the same state and actions.

The pinned image must be authorized by its full image ID before it can be
pinned; `update-image` invalidates the previous `configurationId`, so the
configuration has to be re-applied and the server re-discovered afterwards.

### Clients that launch the server themselves

A client that starts the server as a subprocess — Nanobot, OpenCode or any MCP
SDK client — needs a command and a vault path. Two shapes are possible.

Direct launch (development, requires Python ≥3.11, `uv` and `rg` on the host):

```json
{
  "tools": {
    "mcpServers": {
      "percival-notes-mcp": {
        "command": "uv",
        "args": [
          "run",
          "--directory",
          "/path/to/percival-notes-mcp",
          "percival-notes-mcp",
          "/path/to/your-notes"
        ],
        "enabledTools": ["*"],
        "toolTimeout": 30
      }
    }
  }
}
```

Container launch (the server runs as an image; the client owns the container):

```json
{
  "tools": {
    "mcpServers": {
      "percival-notes": {
        "command": "docker",
        "args": ["run", "--rm", "-i", "--read-only", "--tmpfs", "/tmp:rw,nosuid,nodev", "--network", "none", "--user", "1000:1000", "--mount", "type=bind,src=/absolute/path/to/existing-vault,dst=/vault", "percival-notes-mcp:docker-test"],
        "enabledTools": ["*"],
        "toolTimeout": 30
      }
    }
  }
}
```

The same command works in OpenCode's `opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "percival-notes": {
      "type": "local",
      "command": ["docker", "run", "--rm", "-i", "--read-only", "--tmpfs", "/tmp:rw,nosuid,nodev", "--network", "none", "--user", "1000:1000", "--mount", "type=bind,src=/absolute/path/to/existing-vault,dst=/vault", "percival-notes-mcp:docker-test"],
      "enabled": true,
      "timeout": 30000
    }
  }
}
```

Notes on these examples:

- `enabledTools: ["*"]` requests the full tool surface. A restricted allowlist
  publishes only the listed tools. In Nanobot, resources and prompts are
  registered when the allowlist is `["*"]` or when `allowResourcesPrompts` is
  set; the broker-managed Docker profile enables them on its own.
- The image accepts **no positional arguments** and the vault must be an
  existing, absolute host directory mounted at `/vault`. Use `--mount` (not
  `-v`, which may create an absent source). Keep stdin attached (`-i`) and do
  not allocate a TTY (`-t`); stdout is the MCP protocol, logs go to stderr.
- The default image user is `65532:65532`; select a UID/GID that can write the
  vault, or grant that identity an ACL. `/vault` can also be a Docker named
  volume: the image creates the mount target as `65532:65532`, so Docker's
  initial volume copy-up preserves a writable owner for the default image user.
- Broker-managed deployments that mount host paths below a controlled prefix
  may set `PERCIVAL_NOTES_VAULT_PATH` to the resulting in-container mount
  path. The entrypoint still requires that exact path to be an existing,
  mounted, readable and writable directory.
- The container does not need a Docker socket. Replace the example path and
  image tag with actual values in each host's config; clients do not
  necessarily expand `${VARIABLE}` placeholders in command arrays.

**Ownership.** The Positronic manager owns the `notes` server of this
project. Percival's broker owns its own containers and registry; the two
owners never cross, and this project's agent never mutates the Percival
side.

### Direct launch (development)

```bash
uv run --directory /path/to/percival-notes-mcp percival-notes-mcp /path/to/your-notes
```

`opencode mcp list` checks connectivity: discovery was verified against an
isolated dummy Docker vault, but tool calls through an OpenCode agent have not
been exercised. OpenCode may expose Resources/Prompts differently from an MCP
SDK. Docker MCP Toolkit/Gateway requires a compatible `docker mcp` plugin,
profile and a server definition with an explicit vault volume; the image
alone is **not** a Toolkit registration. Do not enable it with `docker://...`
and no mount. Neither Toolkit nor a client-side agent integration is verified
by the Docker smoke. The image smoke exercises all 12 tools, the Resource and
Prompts, OKF write/read/search, envelope and path containment, and
bind/named-volume persistence across containers. The release timing is not
yet set; no tag or release has been published for this refactor.

---

## 🛠️ Development & Testing
This project uses `uv` for dependency management.

```bash
# Canonical suite
uv run --directory /path/to/percival-notes-mcp pytest -q

# Opt-in real stdio MCP smoke (temporary vault; all 12 tools)
uv run --directory /path/to/percival-notes-mcp python tests/smoke_stdio.py

# Same smoke against a built image (writes, reads, search, link removal,
# 0444 refusal, traversal refusal, host persistence)
uv run --directory /path/to/percival-notes-mcp python tests/smoke_stdio.py \
  --docker-image percival-notes-mcp:docker-test

# Static conformance of a built image (no network, no TTY, no published ports)
uv run --directory /path/to/percival-notes-mcp python scripts/docker-ci-conformance.py \
  --image percival-notes-mcp:docker-test \
  --mount type=tmpfs,destination=/vault,tmpfs-mode=0777 \
  --expected-uid 65532 --expected-tool notes_get_status \
  --compose-service percival-notes

# Isolated OpenCode MCP discovery (if installed) and Docker startup timing
uv run --directory /path/to/percival-notes-mcp python tests/smoke_opencode.py
uv run --directory /path/to/percival-notes-mcp python tests/benchmark_docker_startup.py

# Reproducible search comparison (local, outside CI)
uv run --directory /path/to/percival-notes-mcp python tests/benchmark_search.py --sizes 50 250 1000 5000 --repeats 5

# Run locally
uv run --directory /path/to/percival-notes-mcp percival-notes-mcp /path/to/my-notes
```

On a host with the `docker` binary the canonical suite measures
`114 passed, 4 skipped`; the four skips need the pinned image and disappear
when `PERCIVAL_NOTES_TEST_IMAGE` and `NOTES_MCP_TEST_IMAGE` point at the
pinned image ID (`118 passed, 0 skipped`).

CI (`.github/workflows/ci.yml`) runs the canonical suite, builds the image for
`linux/amd64`, checks the identity and privilege posture of the result
(platform, `65532:65532`, no healthcheck, revision label), runs the stdio
conformance harness, renders the Compose contract and publishes the build
manifest and a CycloneDX SBOM as artifacts.

---

## 📚 About the Project
This server is an integral module of the **percival.OS** project. It is an evolution of the original `notes-mcp` by Edvard Lindelof, optimized for the Percival ecosystem.

- **Main Repository**: [https://github.com/bill-kopp-ai-dev/percival.OS](https://github.com/bill-kopp-ai-dev/percival.OS)
- **License**: MIT
- **Change log**: [CHANGELOG.md](CHANGELOG.md)
- **Engineering records**: `docs/issues/` (open items) and `docs/plans/`, with the concluded ones under `docs/issues/closed/` and `docs/plans/closed/`; the agent lifecycle is specified in `AGENTS.md`

---
*Developed with ❤️ by the percival.OS Team*
