"""Opt-in real-process MCP smoke: uv run python tests/smoke_stdio.py."""

import asyncio
import json
import os
import shutil
import tempfile
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def run() -> None:
    command = shutil.which("percival-notes-mcp")
    assert command and shutil.which("rg"), "Install the console script and ripgrep first"
    with tempfile.TemporaryDirectory(prefix="notes-okf-smoke-") as vault:
        params = StdioServerParameters(command=command, args=[vault])
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as client:
                await client.initialize()
                tools = {tool.name for tool in (await client.list_tools()).tools}
                assert tools == {"notes_read", "notes_write", "notes_glob", "notes_mkdir",
                                  "notes_rm", "notes_rmdir", "notes_search", "notes_list_tags",
                                  "notes_get_backlinks", "notes_read_multiple", "notes_get_stats",
                                  "notes_get_status"}

                resources = (await client.list_resources()).resources
                assert len(resources) == 1
                assert str(resources[0].uri) == "notes://guide/okf-v0.2"
                assert resources[0].mimeType == "text/markdown"
                guide = (await client.read_resource(resources[0].uri)).contents[0].text
                assert "type" in guide and "in_markdown=True" in guide
                assert "<<<BEGIN_UNTRUSTED_NOTE_CONTENT>>>" in guide

                prompts = {p.name: p for p in (await client.list_prompts()).prompts}
                assert set(prompts) == {"notes_create_concept", "notes_research_and_link"}
                assert {a.name: a.required for a in prompts["notes_create_concept"].arguments} == {
                    "topic": True, "type": False, "path": False}
                create = await client.get_prompt("notes_create_concept", {"topic": "solar cells"})
                assert "solar cells" in create.messages[0].content.text
                assert "notes_write" in create.messages[0].content.text
                research = await client.get_prompt("notes_research_and_link", {
                    "topic": "solar cells", "path": "group"})
                assert "group" in research.messages[0].content.text
                assert "notes_get_backlinks" in research.messages[0].content.text
                assert list(Path(vault).iterdir()) == []  # Discovery/retrieval never reads or writes notes.

                async def call(name: str, **kwargs):
                    response = await client.call_tool(name, kwargs)
                    assert not response.isError, (name, response)
                    structured = response.structuredContent
                    if structured is not None:
                        return structured.get("result", structured)
                    return json.loads(response.content[0].text)

                await call("notes_mkdir", path="group")
                await call("notes_write", path="group/one.md",
                           yaml_frontmatter="---\ntype: Reference\ntags: [local]\n---",
                           markdown_content="BodySearch [other](./two.md)")
                await call("notes_write", path="group/two.md",
                           yaml_frontmatter="---\ntype: Playbook\n---",
                           markdown_content="Second body")
                content = await call("notes_read", path="group/one.md")
                assert "Source: group/one.md" in content
                assert "<<<BEGIN_UNTRUSTED_NOTE_CONTENT>>>" in content
                assert "<<<END_UNTRUSTED_NOTE_CONTENT>>>" in content
                assert await call("notes_search", query="Reference") == ["group/one.md"]
                assert await call("notes_search", query="BodySearch", in_markdown=True) == ["group/one.md"]
                assert await call("notes_search", query="BodySearch") == []
                assert await call("notes_glob", pattern="**/*.md") == ["group/one.md", "group/two.md"]
                assert await call("notes_list_tags") == ["local"]
                assert await call("notes_get_backlinks", path="group/two.md") == ["group/one.md"]
                multiple = await call("notes_read_multiple", paths=["group/one.md", "../bad.md"])
                assert set(multiple) == {"group/one.md"}
                assert "<<<BEGIN_UNTRUSTED_NOTE_CONTENT>>>" in multiple["group/one.md"]
                assert (await call("notes_get_stats"))["total_notes"] == 2
                assert "operational" in await call("notes_get_status")
                response = await client.call_tool("notes_read", {"path": "../bad.md"})
                assert response.isError
                await call("notes_rm", path="group/one.md")
                await call("notes_rm", path="group/two.md")
                await call("notes_rmdir", path="group")
                assert not Path(vault, "group").exists()

        env = dict(os.environ, PATH="")
        async with stdio_client(StdioServerParameters(command=command, args=[vault], env=env)) as (reader, writer):
            async with ClientSession(reader, writer) as client:
                await client.initialize()
                response = await client.call_tool("notes_search", {"query": "term"})
                assert response.isError and "ripgrep" in response.content[0].text
    print("stdio smoke passed: 12 tools, resource, prompts, OKF read/write, rg, envelope, traversal, missing rg")


if __name__ == "__main__":
    asyncio.run(run())
