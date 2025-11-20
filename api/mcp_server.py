#!/usr/bin/env python3
from pathlib import Path
from mcp.server import Server
from mcp.types import ToolOutput

server = Server("efc-mcp")
ROOT = Path(".").resolve()

@server.tool()
def list_files(path: str = "") -> ToolOutput:
    p = (ROOT / path).resolve()
    items = []
    for item in p.iterdir():
        items.append({
            "name": item.name,
            "is_dir": item.is_dir()
        })
    return ToolOutput(content=items)

@server.tool()
def read_file(path: str) -> ToolOutput:
    p = (ROOT / path).resolve()
    text = p.read_text()
    return ToolOutput(content=text)

@server.tool()
def write_file(path: str, content: str) -> ToolOutput:
    p = (ROOT / path).resolve()
    p.write_text(content)
    return ToolOutput(content=f"Wrote: {path}")

if __name__ == "__main__":
    server.run()
