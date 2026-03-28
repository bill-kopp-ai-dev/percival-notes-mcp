# Percival Notes MCP
MCP server for collaborative note management using Markdown + YAML frontmatter, with security hardening and nanobot-focused integration.

## Original Project
This project is based on the original **notes-mcp** by Edvard Lindelof:
- Original repository: https://github.com/edvardlindelof/notes-mcp

`percival-notes-mcp` keeps the original idea and tool model, while adding production-oriented hardening and better agent interoperability.

## What Was Improved
- Full refactor to standardized stack: `uv`, `pyproject.toml`, `mcp.server.fastmcp` (FastMCP via MCP SDK).
- Safer filesystem handling with strict root containment (path traversal blocking).
- Explicit untrusted-data envelope in `read` output to reduce prompt-injection risk.
- Logical limits and timeouts for `read`, `write`, `glob`, and `search`.
- Stronger tool documentation (docstrings) to improve function-calling behavior in AI agents.
- Security-focused test coverage for traversal, payload limits, scan/match limits, and timeout behavior.

## Nanobot Optimization (Highlight)
This server was optimized to be reliable with **nanobot**:
- Tool signatures and docstrings are tuned for consistent tool selection and argument formatting.
- `search` accepts both `list[str]` and delimited `string` queries, improving robustness against LLM argument variability.
- Outputs are stable and relative-path based, reducing noisy context and token waste.
- `enabledTools` and `toolTimeout` usage is documented for predictable runtime control.

Nanobot config example (`~/.nanobot/config.json`):

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
          "/path/to/my-notes"
        ],
        "enabledTools": ["read", "write", "glob", "mkdir", "rm", "rmdir", "search"],
        "toolTimeout": 30
      }
    }
  }
}
```

## Tools
- `read(path)`
- `write(path, yaml_frontmatter, markdown_content)`
- `glob(pattern)`
- `mkdir(path)`
- `rm(path)`
- `rmdir(path)`
- `search(query, path=".", in_markdown=false)`

## Security Model
- Root directory sandboxing for every file operation.
- Prompt-injection mitigation by marking note payloads as **untrusted data**.
- Configurable guardrails for size/volume/time to prevent oversized or expensive operations.

Environment variables:
- `PERCIVAL_NOTES_MCP_MAX_READ_BYTES` (default: `1000000`)
- `PERCIVAL_NOTES_MCP_MAX_WRITE_BYTES` (default: `1000000`)
- `PERCIVAL_NOTES_MCP_MAX_SEARCH_FILE_BYTES` (default: `1000000`)
- `PERCIVAL_NOTES_MCP_MAX_GLOB_RESULTS` (default: `2000`)
- `PERCIVAL_NOTES_MCP_MAX_SEARCH_FILES` (default: `5000`)
- `PERCIVAL_NOTES_MCP_MAX_SEARCH_MATCHES` (default: `1000`)
- `PERCIVAL_NOTES_MCP_OPERATION_TIMEOUT_SECONDS` (default: `20`)

Legacy `NOTES_MCP_*` env vars are still accepted for backward compatibility.

## Quick Start (Claude Desktop)
Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "percival-notes": {
      "command": "uvx",
      "args": ["percival-notes-mcp", "C:\\Users\\me\\path\\to\\my-notes"]
    }
  }
}
```

## Local Development
```bash
uv run --directory /path/to/percival-notes-mcp pytest -q
uv run --directory /path/to/percival-notes-mcp percival-notes-mcp /path/to/my-notes
```

## License
MIT (same as original project).
