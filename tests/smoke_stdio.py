"""Opt-in real-process MCP smoke, locally or against the Docker image."""

import argparse
import asyncio
import json
import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def call_tool(client: ClientSession, name: str, **kwargs):
    response = await client.call_tool(name, kwargs)
    assert not response.isError, (name, response)
    structured = response.structuredContent
    if structured is not None:
        return structured.get("result", structured)
    return json.loads(response.content[0].text)


async def run(image: str | None = None) -> None:
    command = shutil.which("docker" if image else "percival-notes-mcp")
    assert command, "Install Docker or the console script first"
    if not image:
        assert shutil.which("rg"), "Install ripgrep first"
    with tempfile.TemporaryDirectory(prefix="notes-okf-smoke-") as vault:
        if image:
            args = ["run", "--rm", "-i", "--read-only", "--tmpfs", "/tmp:rw,nosuid,nodev",
                    "--network", "none", "--pids-limit", "128", "--memory", "512m",
                    "--user", f"{os.getuid()}:{os.getgid()}", "--mount",
                    f"type=bind,src={vault},dst=/vault", image]
        else:
            args = [vault]
        params = StdioServerParameters(command=command, args=args)
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
                    return await call_tool(client, name, **kwargs)

                assert await call("notes_search", query="empty vault") == []
                await call("notes_mkdir", path="group")
                await call("notes_write", path="group/one.md",
                           yaml_frontmatter="---\ntype: Reference\ntags: [local]\n---",
                           markdown_content="BodySearch [other](./two.md)")
                await call("notes_write", path="group/two.md",
                           yaml_frontmatter="---\ntype: Playbook\n---",
                           markdown_content="Second body")
                assert "type: Reference" in Path(vault, "group/one.md").read_text()
                Path(vault, "group/one.md").chmod(0o640)
                await call("notes_write", path="group/one.md",
                           yaml_frontmatter="---\ntype: Reference\ntags: [local]\n---",
                           markdown_content="BodySearch [other](./two.md)")
                assert stat.S_IMODE(Path(vault, "group/one.md").stat().st_mode) == 0o640
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
                if image:
                    Path(vault, "group/outside.md").symlink_to("/etc/passwd")
                    response = await client.call_tool("notes_read", {"path": "group/outside.md"})
                    assert response.isError
                    Path(vault, "group/outside.md").unlink()
                await call("notes_rm", path="group/one.md")
                await call("notes_rm", path="group/two.md")
                await call("notes_rmdir", path="group")
                assert not Path(vault, "group").exists()
                await call("notes_write", path="durable.md",
                           yaml_frontmatter="---\ntype: Reference\n---",
                           markdown_content="DurableSearch")

        # Verify survival after the first process exits, then read/search in a new one.
        assert "DurableSearch" in Path(vault, "durable.md").read_text()
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as reopened:
                await reopened.initialize()
                assert "Source: durable.md" in await call_tool(reopened, "notes_read", path="durable.md")
                assert await call_tool(reopened, "notes_search", query="DurableSearch",
                                       in_markdown=True) == ["durable.md"]
                await call_tool(reopened, "notes_rm", path="durable.md")
        assert not Path(vault, "durable.md").exists()

        if image:
            absent = subprocess.run([command, "run", "--rm", image], capture_output=True,
                                    text=True, timeout=30, check=False)
            assert absent.returncode != 0 and "/vault must be a mounted directory" in absent.stderr
            assert not absent.stdout
            missing = vault + "-missing"
            absent_source = subprocess.run([command, "run", "--rm", "--mount",
                                            f"type=bind,src={missing},dst=/vault", image],
                                           capture_output=True, text=True, timeout=30, check=False)
            assert absent_source.returncode != 0 and not Path(missing).exists()
            extra_arg = subprocess.run([command, "run", "--rm", "--mount",
                                        f"type=bind,src={vault},dst=/vault", image, "/elsewhere"],
                                       capture_output=True, text=True, timeout=30, check=False)
            assert extra_arg.returncode != 0 and "takes no arguments" in extra_arg.stderr
            assert not extra_arg.stdout
            readonly = subprocess.run([command, "run", "--rm", "--user",
                                       f"{os.getuid()}:{os.getgid()}", "--mount",
                                       f"type=bind,src={vault},dst=/vault,readonly", image],
                                      capture_output=True, text=True, timeout=30, check=False)
            assert readonly.returncode != 0 and "not readable and writable" in readonly.stderr
            assert not readonly.stdout
            # Docker named volumes must also satisfy the mount policy.
            volume = "notes-smoke-" + Path(vault).name
            subprocess.run([command, "volume", "create", volume], check=True, capture_output=True)
            try:
                subprocess.run([command, "run", "--rm", "--user", "0:0", "--entrypoint",
                                "chown", "--mount", f"type=volume,src={volume},dst=/vault,volume-nocopy",
                                image, "65532:65532", "/vault"], check=True, capture_output=True)
                volume_params = StdioServerParameters(command=command, args=[
                    "run", "--rm", "-i", "--mount",
                    f"type=volume,src={volume},dst=/vault,volume-nocopy", image,
                ])
                async with stdio_client(volume_params) as (reader, writer):
                    async with ClientSession(reader, writer) as mounted:
                        await mounted.initialize()
                        await call_tool(mounted, "notes_write", path="volume.md",
                                        yaml_frontmatter="---\ntype: Reference\n---",
                                        markdown_content="VolumeSurvivesRestart")
                async with stdio_client(volume_params) as (reader, writer):
                    async with ClientSession(reader, writer) as reopened_volume:
                        await reopened_volume.initialize()
                        assert "VolumeSurvivesRestart" in await call_tool(
                            reopened_volume, "notes_read", path="volume.md")
                        await call_tool(reopened_volume, "notes_rm", path="volume.md")
            finally:
                subprocess.run([command, "volume", "rm", volume], check=True, capture_output=True)
        else:
            env = dict(os.environ, PATH="")
            async with stdio_client(StdioServerParameters(command=command, args=[vault], env=env)) as (reader, writer):
                async with ClientSession(reader, writer) as client:
                    await client.initialize()
                    response = await client.call_tool("notes_search", {"query": "term"})
                    assert response.isError and "ripgrep" in response.content[0].text
    print("stdio smoke passed: 12 tools, resource, prompts, OKF read/write, rg, envelope, traversal"
          + (", mounted image and host persistence" if image else ", missing rg"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--docker-image", help="Local image to smoke via docker run")
    asyncio.run(run(parser.parse_args().docker_image))
