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
