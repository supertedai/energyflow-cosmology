#!/usr/bin/env python3
import json
import os
from pathlib import Path
from mcp import Server, tool, Message

server = Server("efc-mcp")

ROOT = Path(".").resolve()

@tool
def list_files(path: str = ""):
    p = (ROOT / path).resolve()
    files = []
    for item in p.iterdir():
        files.append({
            "name": item.name,
            "is_dir": item.is_dir()
        })
    return files

@tool
def read_file(path: str):
    p = (ROOT / path).resolve()
    return p.read_text()

@tool
def write_file(path: str, content: str):
    p = (ROOT / path).resolve()
    p.write_text(content)
    return {"written": path}

if __name__ == "__main__":
    server.run()
