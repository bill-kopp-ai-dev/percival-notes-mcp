import pytest
import json
from pathlib import Path
from notes_mcp import _extract_tags, _extract_links, _split_frontmatter, create_mcp

def test_extract_tags():
    assert _extract_tags({"tags": "work, urgent"}) == ["urgent", "work"]
    assert _extract_tags({"keywords": ["personal", "todo"]}) == ["personal", "todo"]
    assert _extract_tags({"tags": "Work; Urgent"}) == ["urgent", "work"]
    assert _extract_tags({}) == []

def test_extract_links():
    content = """
    Check [[Note A]] and [[Note B|Alias]].
    Also see [Markdown Link](note_c.md) and [Another](sub/note_d).
    Ignore [External](https://google.com).
    """
    links = _extract_links(content)
    assert "Note A" in links
    assert "Note B" in links
    assert "note_c.md" in links
    assert "sub/note_d" in links
    assert "https://google.com" not in links

def test_split_frontmatter_advanced():
    content = "---\ntags: [a, b]\n---\nBody content"
    yaml_raw, md_part, yaml_dict = _split_frontmatter(content)
    assert yaml_dict == {"tags": ["a", "b"]}
    assert md_part == "\nBody content"

@pytest.fixture
def notes_dir(tmp_path):
    d = tmp_path / "notes"
    d.mkdir()
    (d / "note1.md").write_text("---\ntags: [work]\n---\nLink to [[note2]]", encoding="utf-8")
    (d / "note2.md").write_text("---\ntags: [work, personal]\n---\nLink to [[note1]]", encoding="utf-8")
    (d / "note3.md").write_text("No frontmatter, link to [[note1]]", encoding="utf-8")
    return d

def _extract_tool_result(result):
    """Helper to extract the original return value from FastMCP.call_tool result."""
    # FastMCP.call_tool result can be:
    # 1. A list of content objects (e.g. [TextContent(...)])
    # 2. A tuple (content_list, meta_dict)
    
    if isinstance(result, tuple):
        content, meta = result
        if "result" in meta:
            return meta["result"]
        result = content
    
    if isinstance(result, list) and len(result) > 0:
        # If it's a list of TextContent, try to parse JSON if it looks like it
        text = result[0].text
        try:
            return json.loads(text)
        except:
            # If not JSON, maybe it's just a list of strings?
            # FastMCP might have put each string in a separate TextContent
            return [c.text for c in result]
            
    return result

@pytest.mark.asyncio
async def test_list_tags(notes_dir):
    mcp = create_mcp(notes_dir)
    result = await mcp.call_tool("list_tags", {})
    tags = _extract_tool_result(result)
    assert tags == ["personal", "work"]

@pytest.mark.asyncio
async def test_get_backlinks(notes_dir):
    mcp = create_mcp(notes_dir)
    result = await mcp.call_tool("get_backlinks", {"path": "note1.md"})
    backlinks = _extract_tool_result(result)
    assert "note2.md" in backlinks
    assert "note3.md" in backlinks
    assert "note1.md" not in backlinks

@pytest.mark.asyncio
async def test_read_multiple(notes_dir):
    mcp = create_mcp(notes_dir)
    result = await mcp.call_tool("read_multiple", {"paths": ["note1.md", "note2.md"]})
    results = _extract_tool_result(result)
    assert len(results) == 2
    assert "note1.md" in results
    assert "note2.md" in results

@pytest.mark.asyncio
async def test_get_stats(notes_dir):
    mcp = create_mcp(notes_dir)
    result = await mcp.call_tool("get_stats", {})
    stats = _extract_tool_result(result)
    assert stats["total_notes"] == 3
    assert stats["total_tags"] == 2
    assert "work" in stats["most_used_tags"]
    assert stats["most_used_tags"]["work"] == 2
