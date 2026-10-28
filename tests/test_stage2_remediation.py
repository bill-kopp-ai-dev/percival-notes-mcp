"""Stage-2 remediation checks (A-001, A-008, A-009, A-010, A-011)."""

import logging
import shutil

import pytest

import notes_mcp
from mcp.server.fastmcp.exceptions import ToolError
from test_advanced_features import _extract_tool_result


@pytest.mark.asyncio
async def test_search_tool_skips_external_symlink_and_keeps_valid_notes(tmp_path):
    outside = tmp_path.parent / "outside-search.md"
    outside.write_text("---\ntype: Secret\ntags: [leaked]\n---\nsecret", encoding="utf-8")
    (tmp_path / "escape.md").symlink_to(outside)
    (tmp_path / "valid.md").write_text("---\ntype: Note\n---\nbody", encoding="utf-8")
    mcp = notes_mcp.create_mcp(tmp_path)
    assert _extract_tool_result(
        await mcp.call_tool("notes_search", {"query": "type"})) == ["valid.md"]


def test_search_paths_skip_external_symlinks_without_leaking_paths(tmp_path, caplog):
    outside = tmp_path.parent / "outside-search.md"
    outside.write_text("---\ntype: Secret\ntags: [leaked]\n---\nsecret", encoding="utf-8")
    (tmp_path / "escape.md").symlink_to(outside)
    (tmp_path / "valid.md").write_text("---\ntype: Note\n---\nbody", encoding="utf-8")
    limits = notes_mcp._load_runtime_limits()
    args = dict(root_dir=tmp_path, base_dir=tmp_path, normalized_query=["type"],
                in_markdown=False, limits=limits)
    with caplog.at_level(logging.WARNING, logger="percival-notes-mcp"):
        assert notes_mcp._search_notes_rg(**args) == ["valid.md"]
        assert notes_mcp._search_notes(**args) == ["valid.md"]
    assert "leaked" not in caplog.text
    assert str(outside) not in caplog.text
    assert "secret" not in caplog.text
    assert "outside the notes root" in caplog.text


@pytest.mark.asyncio
async def test_glob_rejects_escaping_patterns_before_enumeration(tmp_path, caplog):
    (tmp_path / "note.md").write_text("---\ntype: Note\n---\n", encoding="utf-8")
    mcp = notes_mcp.create_mcp(tmp_path)
    with caplog.at_level(logging.WARNING, logger="percival-notes-mcp"):
        with pytest.raises(ToolError, match="must not contain"):
            await mcp.call_tool("notes_glob", {"pattern": "../../*"})
        with pytest.raises(ToolError, match="Non-relative"):
            await mcp.call_tool("notes_glob", {"pattern": "/etc/*"})
        with pytest.raises(ToolError, match="must not be empty"):
            await mcp.call_tool("notes_glob", {"pattern": "  "})
    assert "../" not in caplog.text
    assert "/etc" not in caplog.text


@pytest.mark.asyncio
async def test_status_hides_internal_path_and_reports_product_version(tmp_path):
    mcp = notes_mcp.create_mcp(tmp_path)
    status = _extract_tool_result(await mcp.call_tool("notes_get_status", {}))
    assert "operational" in status
    assert notes_mcp.PRODUCT_VERSION in status
    assert str(tmp_path) not in status
    assert "/vault" not in status


@pytest.mark.asyncio
async def test_initialize_reports_the_product_version(tmp_path):
    mcp = notes_mcp.create_mcp(tmp_path)
    options = mcp._mcp_server.create_initialization_options()
    assert options.server_name == notes_mcp.SERVER_NAME
    assert options.server_version == notes_mcp.PRODUCT_VERSION
    assert options.server_version != notes_mcp.importlib.metadata.version("mcp")


@pytest.mark.asyncio
async def test_write_accepts_trailing_newline_and_crlf_frontmatter(tmp_path):
    mcp = notes_mcp.create_mcp(tmp_path)
    await mcp.call_tool("notes_write", {"path": "a.md",
                                        "yaml_frontmatter": "---\ntype: Reference\n---\n",
                                        "markdown_content": "# Body"})
    assert (tmp_path / "a.md").read_text(encoding="utf-8") == "---\ntype: Reference\n---\n# Body"
    await mcp.call_tool("notes_write", {"path": "b.md",
                                        "yaml_frontmatter": "---\r\ntype: Reference\r\n---\r\n",
                                        "markdown_content": "# Body"})
    assert (tmp_path / "b.md").read_text(encoding="utf-8") == "---\ntype: Reference\n---\n# Body"
    read = _extract_tool_result(await mcp.call_tool("notes_read", {"path": "b.md"}))
    assert "type: Reference" in read


@pytest.mark.asyncio
async def test_stats_and_read_multiple_expose_unreadable_files(tmp_path):
    mcp = notes_mcp.create_mcp(tmp_path)
    (tmp_path / "ok.md").write_text("---\ntype: Note\ntags: [x]\n---\nbody", encoding="utf-8")
    blocked = tmp_path / "blocked.md"
    blocked.write_text("---\ntype: Note\ntags: [y]\n---\nbody", encoding="utf-8")
    blocked.chmod(0o000)
    (tmp_path / "folder").mkdir()
    try:
        stats = _extract_tool_result(await mcp.call_tool("notes_get_stats", {}))
        assert stats["total_notes"] == 2
        assert stats["unreadable_files"] == 1
        assert stats["unreadable_paths"] == ["blocked.md"]
        assert stats["total_tags"] == 1

        multiple = _extract_tool_result(await mcp.call_tool(
            "notes_read_multiple",
            {"paths": ["ok.md", "blocked.md", "missing.md", "../escape.md", "folder"]}))
        assert set(multiple["notes"]) == {"ok.md"}
        reasons = {item["path"]: item["reason"] for item in multiple["omitted"]}
        assert reasons["blocked.md"] == "unreadable"
        assert reasons["missing.md"] == "not_found"
        assert reasons["../escape.md"] == "outside_vault"
        assert reasons["folder"] == "not_a_file"
    finally:
        blocked.chmod(0o644)


@pytest.mark.asyncio
async def test_info_logs_do_not_disclose_note_paths(tmp_path, caplog):
    mcp = notes_mcp.create_mcp(tmp_path)
    front = "---\ntype: Note\n---\n"
    await mcp.call_tool("notes_write", {"path": "secret-topic.md",
                                        "yaml_frontmatter": front,
                                        "markdown_content": "body"})
    with caplog.at_level(logging.INFO, logger="percival-notes-mcp"):
        await mcp.call_tool("notes_read", {"path": "secret-topic.md"})
        await mcp.call_tool("notes_write", {"path": "secret-topic.md",
                                            "yaml_frontmatter": front,
                                            "markdown_content": "body"})
        await mcp.call_tool("notes_search", {"query": "type"})
        await mcp.call_tool("notes_glob", {"pattern": "*.md"})
        await mcp.call_tool("notes_get_stats", {})
        await mcp.call_tool("notes_get_status", {})
    assert "secret-topic.md" not in caplog.text
    assert str(tmp_path) not in caplog.text


@pytest.mark.asyncio
async def test_debug_level_is_opt_in(tmp_path, caplog, monkeypatch):
    monkeypatch.setenv("PERCIVAL_NOTES_MCP_LOG_LEVEL", "DEBUG")
    mcp = notes_mcp.create_mcp(tmp_path)
    await mcp.call_tool("notes_write", {"path": "visible.md",
                                        "yaml_frontmatter": "---\ntype: Note\n---",
                                        "markdown_content": "body"})
    with caplog.at_level(logging.DEBUG, logger="percival-notes-mcp"):
        await mcp.call_tool("notes_read", {"path": "visible.md"})
    assert "visible.md" in caplog.text
