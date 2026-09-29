# 🤖 Percival Notes - percival.OS MCP

**Development version 0.1.5 (unreleased OKF refactor)**

[![Python](https://img.shields.io/badge/python-3.11+-yellow.svg)]()
[![MCP](https://img.shields.io/badge/mcp-server-blue.svg)]()
[![percival.OS](https://img.shields.io/badge/percival.OS-ecosystem-orange.svg)](https://github.com/bill-kopp-ai-dev/percival.OS)

## 📋 Description
Local MCP server for OKF v0.2 Markdown notes, with ripgrep-backed literal search.
The operator confirmed on 2026-09-28 that the Nanobot consumer accepts the
required `type` on new concept writes and the existing read envelope.

This server is part of the **percival.OS** ecosystem, a Personal Agentic Operating System designed for autonomy, security, and absolute privacy.

---

## 🛡️ percival.OS Principles
Like all components of `percival.OS`, this MCP server strictly follows our core principles:

- **Privacy First**: All note processing is performed locally. Your notes never leave your infrastructure.
- **Data Sovereignty**: You have absolute control over where your notes are stored and how they are accessed.
- **Hardened Security**: Strict root containment (path traversal blocking) and untrusted-data envelope marking to mitigate prompt-injection risks.
- **Transparency**: Open-source and auditable to ensure full governance of your data.

---

## 🚀 Features & Tools
The `percival-notes-mcp` offers advanced knowledge management capabilities:

- `notes_read(path)`: Read a single note.
- `notes_write(path, yaml_frontmatter, markdown_content)`: Create or update an OKF v0.2 document.
- `notes_glob(pattern)`: List files matching a pattern.
- `notes_mkdir(path)`: Create a directory.
- `notes_rm(path)`: Remove a file.
- `notes_rmdir(path)`: Remove a directory.
- `notes_search(query, path=".", in_markdown=false)`: Search literal terms (OR) in YAML frontmatter, optionally also in the Markdown body, using `rg`.
- `notes_list_tags()`: List all unique tags across notes.
- `notes_get_backlinks(path)`: Find notes linking to a specific note.
- `notes_read_multiple(paths)`: Read multiple notes in a single call.
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

The notes root is an [OKF v0.2 bundle](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md): one UTF-8 `.md` per concept. For example, call `notes_write` with `path="topics/example.md"`, `yaml_frontmatter="---\ntype: Reference\ntags: [demo]\n---"` and `markdown_content="# Example\nDetails"`. Unknown types and extra YAML keys are allowed. A concept requires a nonempty string `type`; invalid writes fail before replacing the file. `index.md` and `log.md` at any level are reserved for directory listings/history: pass empty frontmatter, except root `index.md` may use `---\nokf_version: "0.2"\n---`. Existing files are not reformatted on read.

The operator confirmed there is no existing vault to preserve. If that changes, export/backup it before cutover. New concept writes reject legacy frontmatter lacking `type`. `notes_read` and `notes_read_multiple` still return raw legacy files within the existing untrusted-data envelope; other scans tolerate malformed frontmatter, but legacy files are not OKF-conformant. The operator confirmed Nanobot's acceptance of the required `type`, reserved-file rules, relative Markdown backlinks and the current envelope (`Source:` plus `<<<BEGIN_UNTRUSTED_NOTE_CONTENT>>>` / `<<<END_UNTRUSTED_NOTE_CONTENT>>>` rather than XML or `[SECURITY WARNING:...]`).

Install [ripgrep](https://ripgrep.org/) (`rg` on `PATH`) on the MCP host. `notes_search` reports an explicit error when `rg` is missing. It invokes `rg` locally using fixed-string, case-insensitive patterns over contained file descriptors, then verifies frontmatter/body matches under the existing search limits; a query containing NUL uses the bounded Python walker because process arguments cannot contain NUL. Hidden/ignored notes and safe file symlinks are included; external symlinks are blocked. Writes use anchored directory descriptors, fsync and atomic replacement; replacement preserves existing permission bits. `notes_glob` still uses Python globbing. No note contents are sent over the network by this server.

---

## ⚙️ Configuration in percival.OS (Nanobot)
Add the following configuration to your `~/.nanobot/config.json`:

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
        "enabledTools": ["notes_read", "notes_write", "notes_glob", "notes_mkdir", "notes_rm", "notes_rmdir", "notes_search"],
        "toolTimeout": 30
      }
    }
  }
}
```

## Docker (local stdio image)

Build and test the image locally:

```bash
docker build -t percival-notes-mcp:docker-test .
uv run python tests/smoke_stdio.py --docker-image percival-notes-mcp:docker-test
uv run python tests/smoke_opencode.py        # isolated OpenCode MCP discovery (if installed)
uv run python tests/benchmark_docker_startup.py  # five local launches, no notes
docker image inspect percival-notes-mcp:docker-test --format '{{.Id}}'
```

The image installs the project from `uv.lock` (without dev dependencies) and
Debian's `ripgrep`, and starts MCP over stdio. It accepts **no positional
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
may be read-only. `/vault` can also be a Docker named volume, with suitable
ownership and `volume-nocopy` in the mount options to avoid Docker copying the
image's root-owned `/vault` directory into the volume. Initialize ownership of
a new named volume before starting the server as the default UID (65532).
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

`opencode mcp list` checks connectivity; test the tool workflow with the host
before claiming consumer integration. OpenCode may expose Resources/Prompts
differently from an MCP SDK. Docker MCP Toolkit/Gateway requires a compatible
`docker mcp` plugin, profile and a server definition with an explicit vault
volume; the image alone is **not** a Toolkit registration. Do not enable it
with `docker://...` and no mount. Neither Toolkit nor Nanobot integration is
verified by the Docker smoke above.

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
