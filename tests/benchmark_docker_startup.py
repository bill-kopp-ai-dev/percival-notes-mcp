"""Opt-in Docker MCP startup/discovery timing on an empty dummy vault."""

import asyncio
import os
import statistics
import tempfile
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    samples = []
    with tempfile.TemporaryDirectory(prefix="notes-startup-") as vault:
        params = StdioServerParameters(command="docker", args=[
            "run", "--rm", "-i", "--read-only", "--tmpfs", "/tmp:rw,nosuid,nodev",
            "--network", "none", "--user", f"{os.getuid()}:{os.getgid()}",
            "--mount", f"type=bind,src={vault},dst=/vault", "percival-notes-mcp:docker-test",
        ])
        for _ in range(5):
            start = time.perf_counter()
            async with stdio_client(params) as (reader, writer):
                async with ClientSession(reader, writer) as client:
                    await client.initialize()
                    assert len((await client.list_tools()).tools) == 12
                    samples.append((time.perf_counter() - start) * 1000)
    print(f"Docker launch + MCP initialize + tools/list (ms): "
          f"min={min(samples):.0f}, median={statistics.median(samples):.0f}, "
          f"max={max(samples):.0f}; samples={[round(sample) for sample in samples]}")


if __name__ == "__main__":
    asyncio.run(main())
