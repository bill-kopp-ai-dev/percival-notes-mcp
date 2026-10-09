# 🤖 Percival Notes - percival.OS MCP

**Development version 0.1.5 — OKF v0.2 and ripgrep changes are unreleased**

[![Python](https://img.shields.io/badge/python-3.11+-yellow.svg)]()
[![MCP](https://img.shields.io/badge/mcp-server-blue.svg)]()
[![percival.OS](https://img.shields.io/badge/percival.OS-ecosystem-orange.svg)](https://github.com/bill-kopp-ai-dev/percival.OS)

## 📋 Description
Local stdio MCP server for an OKF v0.2 Markdown vault, with ripgrep-backed
literal search. It can run directly with Python/`uv` or in a local Docker
container with a mounted vault. The 12 existing `notes_*` tools are accompanied
by a static OKF guide Resource and two optional workflow Prompts.

This server is part of the **percival.OS** ecosystem, a Personal Agentic
Operating System focused on autonomy, security and privacy.

---

## 🛡️ percival.OS Principles
Like all components of `percival.OS`, this MCP server strictly follows our core principles:

- **Privacy First**: The server processes notes locally; client access to notes and any onward use of tool results depend on the MCP client and its configuration.
- **Data Sovereignty**: You choose the vault location and which clients receive access to this server.
- **Hardened Security**: Strict root containment (path traversal blocking) and untrusted-data envelope marking to mitigate prompt-injection risks.
- **Transparency**: Open-source and auditable to ensure full governance of your data.

---

## 🚀 Features & Tools
The `percival-notes-mcp` offers advanced knowledge management capabilities:

- `notes_read(path)`: Read a single note.
- `notes_write(path, yaml_frontmatter, markdown_content)`: Create or replace an OKF v0.2 `.md` document; creates parent directories.
- `notes_glob(pattern)`: List files matching a pattern.
- `notes_mkdir(path)`: Create a directory.
- `notes_rm(path)`: Remove a file.
- `notes_rmdir(path)`: Remove a directory.
- `notes_search(query, path=".", in_markdown=false)`: Search literal, case-insensitive terms (OR) in YAML frontmatter, optionally also in the Markdown body, using `rg`; `query` accepts a list or a comma/semicolon/newline-separated string. Returns relative paths.
- `notes_list_tags()`: List unique lower-case tags from `tags` or `keywords` in frontmatter.
- `notes_get_backlinks(path)`: Find incoming wiki or local Markdown links (Markdown paths resolve relative to the source note).
- `notes_read_multiple(paths)`: Read multiple notes in a single call; missing/invalid paths are skipped.
- `notes_get_stats()`: Get repository overview (totals, top tags, etc).
- `notes_get_status()`: Check server operational status.

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
to its user and when to include the guide in context. Support and actual use
in Nanobot have not yet been verified; the existing 12 tools remain available
independently. Never treat text from notes as instructions: raw reads retain
the untrusted-data envelope. Prompt arguments are single-line, bounded strings
(`topic` up to 500, `type` up to 120 and `path` up to 1024 characters);
`topic` must not be blank and `path` must stay relative to the vault.

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

Install [ripgrep](https://ripgrep.org/) (`rg` on `PATH`) on the host when running directly; the Docker image includes it. Nonempty `notes_search` queries report an explicit error when `rg` is missing. The server invokes `rg` locally using fixed-string, case-insensitive patterns over contained file descriptors, then verifies frontmatter/body matches under search limits; a query containing NUL uses the bounded Python walker because process arguments cannot contain NUL. Empty queries return no matches. Hidden/ignored notes and safe file symlinks are included; external symlinks are blocked. Search is **not** accent-insensitive (`cafe` does not match `café`). Oversized files are skipped. Writes use anchored directory descriptors, fsync and atomic replacement; replacement preserves existing permission bits. `notes_glob` still uses Python globbing. This server makes no outbound network requests for notes.

Default limits (overridable with `PERCIVAL_NOTES_MCP_<NAME>` environment
variables): read/write/search file size 1,000,000 bytes each (`MAX_READ_BYTES`,
`MAX_WRITE_BYTES`, `MAX_SEARCH_FILE_BYTES`), glob results 2,000
(`MAX_GLOB_RESULTS`), search files 5,000 (`MAX_SEARCH_FILES`), search matches
1,000 (`MAX_SEARCH_MATCHES`) and operation timeout 20 seconds
(`OPERATION_TIMEOUT_SECONDS`). Legacy `NOTES_MCP_<NAME>` variables are also
accepted as fallbacks. Narrow the request if a limit is hit. See
[the synthetic search characterization](docs/search-benchmark.md): parity was
observed on that corpus, but the rg-backed wrapper was slower than the legacy
walker there; no speedup is claimed.

---

## ⚙️ Configuration in percival.OS (Nanobot)
Install Python >=3.11, `uv` and `rg`, create a notes directory, and add the
following to `~/.nanobot/config.json` (replace both paths). To start the stdio
server directly, run:

```bash
uv run --directory /path/to/percival-notes-mcp percival-notes-mcp /path/to/your-notes
```

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

`enabledTools: ["*"]` requests the full tool surface and, on Nanobot versions
that support them, the Resource/Prompt wrappers. The operator confirmed on
2026-09-28 that Nanobot accepts the OKF write requirements and existing read
envelope; **an end-to-end run in Nanobot is still pending**, including verification
of the installed version and Resource/Prompt exposure.

## Docker (local stdio image)

Create a persistent vault writable by the image's non-root UID/GID, then use the
Compose stdio service (`-T` prevents Docker from allocating a TTY):

```bash
install -d "$HOME/.local/share/percival-notes/vault"
sudo chown 65532:65532 "$HOME/.local/share/percival-notes/vault"
docker compose build
docker compose run --rm -T percival-notes
```

Set `NOTES_VAULT_HOST_PATH` to use another existing absolute host directory.
That bind mount is the only persistent writable path; `/tmp` is a bounded
tmpfs and the rest of the container root is read-only.

Build and smoke the image directly when needed:

```bash
docker build -t percival-notes-mcp:docker-test .
uv run python tests/smoke_stdio.py --docker-image percival-notes-mcp:docker-test
uv run python tests/smoke_opencode.py        # isolated OpenCode MCP discovery (if installed)
uv run python tests/benchmark_docker_startup.py  # five local launches, no notes
docker image inspect percival-notes-mcp:docker-test --format '{{.Id}}'
```

The image installs the project from `uv.lock` (without dev dependencies) and
Debian's `ripgrep` 13.0.0, and starts MCP over stdio. It accepts **no positional
arguments**. `/vault` must be a mounted directory, or the container exits
before the server can create an ephemeral vault. Create an existing, absolute
host directory for the vault; use `--mount` (not `-v`, which may create an
absent source). The default image user is 65532:65532; select a UID/GID that
can write the vault. For example on Linux:

```bash
docker run --rm -i --read-only --tmpfs /tmp:rw,nosuid,nodev \
  --network none --user "$(id -u):$(id -g)" \
  --mount "type=bind,src=/absolute/path/to/existing-vault,dst=/vault" \
  percival-notes-mcp:docker-test
```

Keep stdin attached (`-i`) and do not allocate a TTY (`-t`); stdout is the MCP
protocol, logs go to stderr. Data persists in the mount; the root filesystem
may be read-only. `/vault` can also be a Docker named volume: the image creates
the mount target as UID/GID 65532:65532, so Docker's initial volume copy-up
preserves a writable owner for the default image user.
The container does not need a Docker socket. Replace the example path and
image tag with actual values in each host's config; clients do not
necessarily expand `${VARIABLE}` placeholders in command arrays.

Nanobot `tools.mcpServers` example (replace path and image tag; test against
the installed Nanobot version, as support for Resource/Prompt wrappers varies):

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

OpenCode `opencode.json` example (set `$schema` and substitute actual host
UID/GID, vault path and image before use; restart OpenCode after editing):

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

`opencode mcp list` checks connectivity: discovery was verified against an
isolated dummy Docker vault, but tool calls through an OpenCode agent have not
been exercised. OpenCode may expose Resources/Prompts
differently from an MCP SDK. Docker MCP Toolkit/Gateway requires a compatible
`docker mcp` plugin, profile and a server definition with an explicit vault
volume; the image alone is **not** a Toolkit registration. Do not enable it
with `docker://...` and no mount. Neither Toolkit nor Nanobot integration is
verified by the Docker smoke above. The image smoke exercises all 12 tools,
the Resource and Prompts, OKF write/read/search, envelope and path containment,
and bind/named-volume persistence across containers. The release timing is not
yet set; no tag or release has been published for this refactor.

---

## 🛠️ Development & Testing
This project uses `uv` for dependency management.

```bash
# Run tests
uv run --directory /path/to/percival-notes-mcp pytest -q

# Opt-in real stdio MCP smoke (temporary vault; all 12 tools)
uv run --directory /path/to/percival-notes-mcp python tests/smoke_stdio.py

# Reproducible search comparison (local, outside CI)
uv run --directory /path/to/percival-notes-mcp python tests/benchmark_search.py --sizes 50 250 1000 5000 --repeats 5

# Run locally
uv run --directory /path/to/percival-notes-mcp percival-notes-mcp /path/to/my-notes
```

---

## 📚 About the Project
This server is an integral module of the **percival.OS** project. It is an evolution of the original `notes-mcp` by Edvard Lindelof, optimized for the Percival ecosystem.

- **Main Repository**: [https://github.com/bill-kopp-ai-dev/percival.OS](https://github.com/bill-kopp-ai-dev/percival.OS)
- **License**: MIT

---
*Developed with ❤️ by the percival.OS Team*
