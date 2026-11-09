"""Regressões permanentes dos 12 achados da bateria funcional de 2026-11-09.

Cada teste é discriminante: falha pela causa esperada antes da correção e
passa depois. Ver `docs/issues/2026-11-09-notes-functional-battery-findings.md`
e `docs/plans/2026-11-09-notes-functional-battery-remediation-plan.md`.
"""

import os
import shutil
import stat
from pathlib import Path

import pytest

import notes_mcp
from mcp.server.fastmcp.exceptions import ToolError
from test_advanced_features import _extract_tool_result

pytestmark = pytest.mark.asyncio


async def _call(mcp, name, **kwargs):
    return _extract_tool_result(await mcp.call_tool(name, kwargs))


def _write(root: Path, relative: str, text: str) -> Path:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


# --------------------------------------------------------------------------
# F-01 - uma nota ilegível aborta a busca inteira
# --------------------------------------------------------------------------


@pytest.mark.skipif(not shutil.which("rg"), reason="requires ripgrep")
async def test_f01_search_keeps_readable_match_when_another_note_is_unreadable(tmp_path):
    root = tmp_path.resolve()
    _write(root, "good.md", "---\ntype: A\ntitle: alpha\n---\n")
    locked = _write(root, "locked.md", "---\ntype: L\ntitle: secret\n---\n")
    locked.chmod(0o000)
    try:
        mcp = notes_mcp.create_mcp(root)
        assert await _call(mcp, "notes_search", query="alpha") == ["good.md"]
    finally:
        locked.chmod(0o600)


@pytest.mark.skipif(not shutil.which("rg"), reason="requires ripgrep")
async def test_f01_walker_path_keeps_readable_match_when_another_note_is_unreadable(tmp_path):
    """O walker Python (usado quando a query contém NUL) também deve degradar."""
    root = tmp_path.resolve()
    _write(root, "good.md", "---\ntype: A\n---\nalpha\x00beta\n")
    locked = _write(root, "locked.md", "---\ntype: L\ntitle: secret\n---\n")
    locked.chmod(0o000)
    try:
        mcp = notes_mcp.create_mcp(root)
        assert await _call(mcp, "notes_search", query="alpha\x00beta",
                           in_markdown=True) == ["good.md"]
    finally:
        locked.chmod(0o600)


@pytest.mark.skipif(not shutil.which("rg"), reason="requires ripgrep")
async def test_f01_search_returns_empty_list_when_every_note_is_unreadable(tmp_path):
    root = tmp_path.resolve()
    locked = _write(root, "locked.md", "---\ntype: L\ntitle: secret\n---\n")
    locked.chmod(0o000)
    try:
        mcp = notes_mcp.create_mcp(root)
        assert await _call(mcp, "notes_search", query="secret") == []
    finally:
        locked.chmod(0o600)


@pytest.mark.skipif(not shutil.which("rg"), reason="requires ripgrep")
async def test_f01_search_still_fails_on_real_scanner_errors(tmp_path, monkeypatch):
    """Uma falha real do ripgrep continua sendo erro, não lista vazia."""
    root = tmp_path.resolve()
    _write(root, "a.md", "---\ntype: A\n---\nalpha\n")
    fake = tmp_path / "fake-rg"
    fake.write_text("#!/bin/sh\nexit 2\n")
    fake.chmod(0o755)
    monkeypatch.setattr(notes_mcp.shutil, "which", lambda _: str(fake))
    mcp = notes_mcp.create_mcp(root)
    with pytest.raises(ToolError):
        await mcp.call_tool("notes_search", {"query": "alpha"})


# --------------------------------------------------------------------------
# F-02 - glob(".") estoura IndexError
# --------------------------------------------------------------------------


@pytest.mark.parametrize("pattern", [".", "./", ".//"])
async def test_f02_glob_rejects_pattern_without_component(tmp_path, pattern):
    """O erro deve ser de validação, não um IndexError interno do pathlib."""
    mcp = notes_mcp.create_mcp(tmp_path)
    with pytest.raises(ToolError) as excinfo:
        await mcp.call_tool("notes_glob", {"pattern": pattern})
    message = str(excinfo.value)
    assert "tuple index out of range" not in message
    assert "IndexError" not in message
    assert "component" in message


async def test_f02_glob_rejects_empty_pattern(tmp_path):
    mcp = notes_mcp.create_mcp(tmp_path)
    with pytest.raises(ToolError, match="must not be empty"):
        await mcp.call_tool("notes_glob", {"pattern": ""})


# --------------------------------------------------------------------------
# F-03 - glob("**") devolve "." como resultado espúrio
# --------------------------------------------------------------------------


async def test_f03_glob_star_star_never_returns_the_vault_root(tmp_path):
    _write(tmp_path, "note.md", "---\ntype: A\n---\n")
    (tmp_path / "sub").mkdir()
    mcp = notes_mcp.create_mcp(tmp_path)
    matches = await _call(mcp, "notes_glob", pattern="**")
    assert "." not in matches
    assert "" not in matches


async def test_f03_glob_star_star_md_has_no_root_entry(tmp_path):
    _write(tmp_path, "note.md", "---\ntype: A\n---\n")
    mcp = notes_mcp.create_mcp(tmp_path)
    assert await _call(mcp, "notes_glob", pattern="**/*.md") == ["note.md"]


# --------------------------------------------------------------------------
# F-04 - nota nova nasce 0600 (decisão D-01: somente 0600)
# --------------------------------------------------------------------------


async def test_f04_new_note_is_private_and_existing_mode_is_preserved(tmp_path):
    mcp = notes_mcp.create_mcp(tmp_path)
    await mcp.call_tool("notes_write", {"path": "new.md",
                                        "yaml_frontmatter": "---\ntype: Note\n---",
                                        "markdown_content": "body"})
    created = tmp_path / "new.md"
    assert stat.S_IMODE(created.stat().st_mode) == 0o600

    existing = _write(tmp_path, "existing.md", "old")
    existing.chmod(0o640)
    await mcp.call_tool("notes_write", {"path": "existing.md",
                                        "yaml_frontmatter": "---\ntype: Note\n---",
                                        "markdown_content": "new"})
    assert stat.S_IMODE(existing.stat().st_mode) == 0o640


# --------------------------------------------------------------------------
# F-05 - notes_rm remove o alvo do symlink
# --------------------------------------------------------------------------


async def test_f05_rm_removes_the_link_and_preserves_the_target(tmp_path):
    root = tmp_path.resolve()
    victim = _write(root, "victim.md", "conteudo real")
    (root / "alias.md").symlink_to(root / "victim.md")
    mcp = notes_mcp.create_mcp(root)
    result = await _call(mcp, "notes_rm", path="alias.md")
    assert result == "File removed: alias.md"
    assert not (root / "alias.md").is_symlink()
    assert not (root / "alias.md").exists()
    assert victim.read_text(encoding="utf-8") == "conteudo real"


async def test_f05_rm_removes_a_broken_internal_link(tmp_path):
    root = tmp_path.resolve()
    (root / "broken.md").symlink_to(root / "missing.md")
    mcp = notes_mcp.create_mcp(root)
    assert await _call(mcp, "notes_rm", path="broken.md") == "File removed: broken.md"
    assert not (root / "broken.md").is_symlink()


async def test_f05_rm_refuses_external_symlink(tmp_path):
    root = tmp_path.resolve()
    outside = tmp_path.parent / "outside-rm.md"
    outside.write_text("externo", encoding="utf-8")
    (root / "external.md").symlink_to(outside)
    mcp = notes_mcp.create_mcp(root)
    with pytest.raises(ToolError):
        await mcp.call_tool("notes_rm", {"path": "external.md"})
    assert outside.read_text(encoding="utf-8") == "externo"


async def test_f05_rm_of_a_link_to_directory_removes_only_the_link(tmp_path):
    root = tmp_path.resolve()
    (root / "realdir").mkdir()
    (root / "dirlink").symlink_to(root / "realdir", target_is_directory=True)
    mcp = notes_mcp.create_mcp(root)
    assert await _call(mcp, "notes_rm", path="dirlink") == "File removed: dirlink"
    assert not (root / "dirlink").is_symlink()
    assert (root / "realdir").is_dir()


# --------------------------------------------------------------------------
# F-06 - notes_rmdir apaga o diretório real por trás do symlink
# --------------------------------------------------------------------------


async def test_f06_rmdir_refuses_a_symlink_and_keeps_the_target(tmp_path):
    root = tmp_path.resolve()
    target = root / "emptytarget"
    target.mkdir()
    (root / "emptylink").symlink_to(target, target_is_directory=True)
    mcp = notes_mcp.create_mcp(root)
    with pytest.raises(ToolError):
        await mcp.call_tool("notes_rmdir", {"path": "emptylink"})
    assert (root / "emptylink").is_symlink()
    assert target.is_dir()


async def test_f06_rmdir_removes_a_real_empty_directory(tmp_path):
    root = tmp_path.resolve()
    (root / "emptydir").mkdir()
    mcp = notes_mcp.create_mcp(root)
    assert await _call(mcp, "notes_rmdir", path="emptydir") == "Directory removed: emptydir"
    assert not (root / "emptydir").exists()


async def test_f06_rmdir_keeps_a_populated_directory(tmp_path):
    root = tmp_path.resolve()
    (root / "full").mkdir()
    _write(root, "full/child.md", "child")
    mcp = notes_mcp.create_mcp(root)
    with pytest.raises(ToolError):
        await mcp.call_tool("notes_rmdir", {"path": "full"})
    assert (root / "full" / "child.md").exists()


# --------------------------------------------------------------------------
# F-07 - UTF-8 inválido rotulado como too_large
# --------------------------------------------------------------------------


async def test_f07_read_multiple_reports_invalid_utf8_as_unreadable(tmp_path):
    root = tmp_path.resolve()
    (root / "bin.md").write_bytes(b"---\ntype: X\n---\n\xff\xfe")
    mcp = notes_mcp.create_mcp(root)
    result = await _call(mcp, "notes_read_multiple", paths=["bin.md"])
    assert result["omitted"] == [{"path": "bin.md", "reason": "unreadable"}]


async def test_f07_read_multiple_keeps_too_large_for_oversized_files(tmp_path, monkeypatch):
    root = tmp_path.resolve()
    (root / "big.md").write_text("x" * 5000, encoding="utf-8")
    monkeypatch.setenv("PERCIVAL_NOTES_MCP_MAX_READ_BYTES", "100")
    mcp = notes_mcp.create_mcp(root)
    result = await _call(mcp, "notes_read_multiple", paths=["big.md"])
    assert result["omitted"] == [{"path": "big.md", "reason": "too_large"}]


async def test_f07_read_multiple_returns_readable_notes_alongside_omissions(tmp_path):
    root = tmp_path.resolve()
    _write(root, "ok.md", "---\ntype: Note\n---\ncorpo")
    (root / "bin.md").write_bytes(b"\xff\xfe")
    mcp = notes_mcp.create_mcp(root)
    result = await _call(mcp, "notes_read_multiple", paths=["ok.md", "bin.md"])
    assert set(result["notes"]) == {"ok.md"}
    assert result["omitted"] == [{"path": "bin.md", "reason": "unreadable"}]


async def test_f07_read_reports_invalid_utf8_as_a_clear_error(tmp_path):
    root = tmp_path.resolve()
    (root / "bin.md").write_bytes(b"---\ntype: X\n---\n\xff\xfe")
    mcp = notes_mcp.create_mcp(root)
    with pytest.raises(ToolError, match="UTF-8"):
        await mcp.call_tool("notes_read", {"path": "bin.md"})


# --------------------------------------------------------------------------
# F-08 - keywords ignorado quando tags existe
# --------------------------------------------------------------------------


async def test_f08_list_tags_merges_tags_and_keywords(tmp_path):
    root = tmp_path.resolve()
    _write(root, "note.md", "---\ntype: Note\ntags: [T1, shared]\nkeywords: [K1, SHARED]\n---\n")
    mcp = notes_mcp.create_mcp(root)
    assert await _call(mcp, "notes_list_tags") == ["k1", "shared", "t1"]


async def test_f08_list_tags_reads_each_field_independently(tmp_path):
    root = tmp_path.resolve()
    _write(root, "a.md", "---\ntype: Note\ntags: []\nkeywords: [k1]\n---\n")
    _write(root, "b.md", "---\ntype: Note\nkeywords: [k2]\n---\n")
    _write(root, "c.md", "---\ntype: Note\ntags: [t3]\n---\n")
    mcp = notes_mcp.create_mcp(root)
    assert await _call(mcp, "notes_list_tags") == ["k1", "k2", "t3"]


async def test_f08_stats_counts_a_shared_tag_once_per_note(tmp_path):
    root = tmp_path.resolve()
    _write(root, "note.md",
           "---\ntype: Note\ntags: [shared]\nkeywords: [shared, other]\n---\n")
    mcp = notes_mcp.create_mcp(root)
    stats = await _call(mcp, "notes_get_stats")
    assert stats["most_used_tags"]["shared"] == 1
    assert stats["most_used_tags"]["other"] == 1
    assert stats["total_tags"] == 2


# --------------------------------------------------------------------------
# F-09 - path de alvo de backlinks não é validado
# --------------------------------------------------------------------------


@pytest.mark.parametrize("target", ["../a.md", "/etc/passwd", "", "   ", "sub/../a.md"])
async def test_f09_backlinks_reject_invalid_targets(tmp_path, target):
    _write(tmp_path, "a.md", "---\ntype: Note\n---\n")
    mcp = notes_mcp.create_mcp(tmp_path)
    with pytest.raises(ToolError):
        await mcp.call_tool("notes_get_backlinks", {"path": target})


async def test_f09_backlinks_reject_a_nul_byte(tmp_path):
    mcp = notes_mcp.create_mcp(tmp_path)
    with pytest.raises(ToolError):
        await mcp.call_tool("notes_get_backlinks", {"path": "a\x00b"})


async def test_f09_backlinks_accept_valid_targets(tmp_path):
    root = tmp_path.resolve()
    _write(root, "sub/a.md", "---\ntype: Note\n---\n")
    _write(root, "source.md", "---\ntype: Note\n---\n[alvo](sub/a.md)\n")
    mcp = notes_mcp.create_mcp(root)
    assert await _call(mcp, "notes_get_backlinks", path="sub/a.md") == ["source.md"]
    assert await _call(mcp, "notes_get_backlinks", path="./sub/a.md") == ["source.md"]
    assert await _call(mcp, "notes_get_backlinks", path="inexistente.md") == []


async def test_f09_backlinks_match_a_wiki_name_without_extension(tmp_path):
    root = tmp_path.resolve()
    _write(root, "project a.md", "---\ntype: Note\n---\n")
    _write(root, "source.md", "---\ntype: Note\n---\n[[Project A]]\n")
    mcp = notes_mcp.create_mcp(root)
    assert await _call(mcp, "notes_get_backlinks", path="Project A") == ["source.md"]
    assert await _call(mcp, "notes_get_backlinks", path="project a.md") == ["source.md"]


async def test_f09_relative_markdown_links_keep_resolving_against_the_source(tmp_path):
    """A validação do parâmetro não confunde o link do corpo de uma nota."""
    root = tmp_path.resolve()
    _write(root, "sub/target.md", "---\ntype: Note\n---\n")
    _write(root, "sub/source.md", "---\ntype: Note\n---\n[alvo](../sub/target.md)\n")
    mcp = notes_mcp.create_mcp(root)
    assert await _call(mcp, "notes_get_backlinks", path="sub/target.md") == ["sub/source.md"]


# --------------------------------------------------------------------------
# F-10 - stats infla total_notes com symlink interno
# --------------------------------------------------------------------------


async def test_f10_stats_and_glob_agree_on_the_same_vault(tmp_path):
    root = tmp_path.resolve()
    _write(root, "a.md", "---\ntype: Note\n---\n")
    _write(root, "victim.md", "---\ntype: Note\n---\n")
    (root / "alias.md").symlink_to(root / "victim.md")
    mcp = notes_mcp.create_mcp(root)
    assert await _call(mcp, "notes_glob", pattern="*.md") == ["a.md", "victim.md"]
    stats = await _call(mcp, "notes_get_stats")
    assert stats["total_notes"] == 2


async def test_f10_stats_does_not_multiply_tag_frequency_by_alias(tmp_path):
    root = tmp_path.resolve()
    _write(root, "victim.md", "---\ntype: Note\ntags: [shared]\n---\n")
    (root / "alias.md").symlink_to(root / "victim.md")
    mcp = notes_mcp.create_mcp(root)
    stats = await _call(mcp, "notes_get_stats")
    assert stats["total_notes"] == 1
    assert stats["most_used_tags"] == {"shared": 1}


# --------------------------------------------------------------------------
# F-11 - escrita sobrescreve arquivo 0444
# --------------------------------------------------------------------------


async def test_f11_write_refuses_a_read_only_target_and_preserves_it(tmp_path):
    root = tmp_path.resolve()
    target = _write(root, "ro.md", "original")
    target.chmod(0o444)
    before = target.stat()
    mcp = notes_mcp.create_mcp(root)
    with pytest.raises(ToolError, match="read-only"):
        await mcp.call_tool("notes_write", {"path": "ro.md",
                                            "yaml_frontmatter": "---\ntype: Note\n---",
                                            "markdown_content": "novo"})
    after = target.stat()
    assert target.read_text(encoding="utf-8") == "original"
    assert stat.S_IMODE(after.st_mode) == 0o444
    assert after.st_mtime == before.st_mtime
    assert not list(root.glob(".notes-*"))


async def test_f11_write_still_replaces_an_authorized_target(tmp_path):
    root = tmp_path.resolve()
    target = _write(root, "rw.md", "original")
    target.chmod(0o640)
    mcp = notes_mcp.create_mcp(root)
    await mcp.call_tool("notes_write", {"path": "rw.md",
                                        "yaml_frontmatter": "---\ntype: Note\n---",
                                        "markdown_content": "novo"})
    assert "novo" in target.read_text(encoding="utf-8")
    assert stat.S_IMODE(target.stat().st_mode) == 0o640


# --------------------------------------------------------------------------
# F-12 - glob devolve caminho que não existe
# --------------------------------------------------------------------------


async def test_f12_glob_omits_a_broken_symlink_target(tmp_path):
    root = tmp_path.resolve()
    _write(root, "real.md", "---\ntype: Note\n---\n")
    (root / "broken.md").symlink_to(root / "nonexistent.md")
    mcp = notes_mcp.create_mcp(root)
    assert await _call(mcp, "notes_glob", pattern="*.md") == ["real.md"]
    stats = await _call(mcp, "notes_get_stats")
    assert stats["total_notes"] == 1


async def test_f12_glob_omits_a_symlink_loop(tmp_path):
    root = tmp_path.resolve()
    (root / "loop_a.md").symlink_to(root / "loop_b.md")
    (root / "loop_b.md").symlink_to(root / "loop_a.md")
    mcp = notes_mcp.create_mcp(root)
    assert await _call(mcp, "notes_glob", pattern="*.md") == []
