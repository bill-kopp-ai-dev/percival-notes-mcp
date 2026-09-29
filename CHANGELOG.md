# Changelog

## Unreleased — OKF v0.2 + ripgrep

- Add a local Docker stdio image with locked Python dependencies, ripgrep and a non-root runtime; require an explicit `/vault` mount before startup. Extend the MCP smoke to run against the read-only image and verify host persistence, mode-preserving replacement and security checks.
- Review the Docker integration smoke: prove bind and named-volume persistence across container restarts rather than only during a live process; isolate OpenCode discovery from inherited user configuration and state.
- Add a static OKF v0.2 guide Resource and two optional workflow Prompts for creating concepts and researching/linking notes. Bound prompt arguments and reject blank topics, control characters and paths outside the vault. They do not read the vault or execute tools when retrieved; Nanobot support remains to be validated.
- New concept writes require OKF YAML frontmatter with nonempty `type`; reserve `index.md` and `log.md` at every level and allow the optional root version declaration. Write validation is performed before atomic replacement.
- Search uses local ripgrep as a bounded prefilter and retains literal OR matching against frontmatter (and optionally body) with Python verification. The `rg` executable is required for nonempty searches.
- Preserve 12 MCP tool names/signatures, raw read envelopes and existing status/stats shapes; resolve bundle-relative and source-relative Markdown links for backlinks.
- Restore baseline tests by calling registered `notes_*` names; add parity tests, real stdio smoke and reproducible timing harness.
- Review fixes: avoid backlink matches across homonymous directories; anchor file operations to vault directories to prevent symlink-swap redirects; preserve file permissions on replacement; reject non-finite timeouts; retain literal search for NUL queries via the bounded walker.

The operator confirmed on 2026-09-28 that there is no existing vault to preserve and Nanobot accepts the required `type`, reserved-file rules, relative Markdown backlinks and existing non-XML read envelope. Pending before release: an end-to-end run in Nanobot itself and release timing. No migration or release is performed here.
