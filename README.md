# 🤖 Percival Notes - percival.OS MCP

**Version 0.0.2**

[![Python](https://img.shields.io/badge/python-3.10+-yellow.svg)]()
[![MCP](https://img.shields.io/badge/mcp-server-blue.svg)]()
[![percival.OS](https://img.shields.io/badge/percival.OS-ecosystem-orange.svg)](https://github.com/bill-kopp-ai-dev/percival.OS)

## 📋 Description
MCP server for collaborative note management using Markdown + YAML frontmatter, with security hardening and deep integration with the Nanobot agent.

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
- `notes_write(path, yaml_frontmatter, markdown_content)`: Create or update a note.
- `notes_glob(pattern)`: List files matching a pattern.
- `notes_mkdir(path)`: Create a directory.
- `notes_rm(path)`: Remove a file.
- `notes_rmdir(path)`: Remove a directory.
- `notes_search(query, path=".", in_markdown=false)`: Search in frontmatter or content.
- `notes_list_tags()`: List all unique tags across notes.
- `notes_get_backlinks(path)`: Find notes linking to a specific note.
- `notes_read_multiple(paths)`: Read multiple notes in a single call.
- `notes_get_stats()`: Get repository overview (totals, top tags, etc).
- `notes_get_status()`: Check server operational status.

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
