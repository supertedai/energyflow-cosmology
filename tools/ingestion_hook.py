#!/usr/bin/env python3
"""
Ingestion Hook - Force ALL new data through Orchestrator v2
===========================================================

This module provides wrappers that ensure all data ingestion
goes through the deterministic orchestrator pipeline.

Use this instead of direct Qdrant/Neo4j writes.

Example:
    from tools.ingestion_hook import ingest_text, ingest_file
    
    # Instead of direct insert:
    result = ingest_text("My content", source="manual_input")
    
    # Ingest from file:
    result = ingest_file("docs/new_paper.md")
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from orchestrator_v2 import orchestrate

def ingest_text(
    text: str,
    source: str,
    input_type: str = "document",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Ingest text through orchestrator pipeline
    
    THIS IS THE ONLY APPROVED WAY TO ADD NEW TEXT DATA
    
    Args:
        text: The text content to ingest
        source: Human-readable source identifier
        input_type: Type of input ("document", "chat", "log")
        metadata: Optional metadata dict
    
    Returns:
        Result dict with document_id, chunk_ids, concepts, etc.
    """
    print(f"🔒 Ingestion Hook: Forcing through Orchestrator v2...")
    
    result = orchestrate(
        text=text,
        source=source,
        input_type=input_type,
        metadata=metadata or {}
    )
    
    print(f"✅ Ingestion complete: {len(result['chunk_ids'])} chunks, {len(result['concepts'])} concepts")
    return result

def ingest_file(
    file_path: str,
    input_type: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Ingest file through orchestrator pipeline
    
    THIS IS THE ONLY APPROVED WAY TO ADD NEW FILE DATA
    
    Args:
        file_path: Path to file
        input_type: Type of input (auto-detected if None)
        metadata: Optional metadata dict
    
    Returns:
        Result dict with document_id, chunk_ids, concepts, etc.
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Read file
    text = path.read_text(encoding='utf-8', errors='ignore')
    
    # Auto-detect type if not provided
    if input_type is None:
        if "chat" in str(path).lower() or "conversation" in str(path).lower():
            input_type = "chat"
        elif ".log" in path.suffix:
            input_type = "log"
        else:
            input_type = "document"
    
    # Build metadata
    meta = metadata or {}
    meta.update({
        "file_path": str(path),
        "file_name": path.name,
        "file_type": path.suffix,
        "file_size": len(text)
    })
    
    return ingest_text(
        text=text,
        source=path.name,
        input_type=input_type,
        metadata=meta
    )

def ingest_multiple(
    texts: list[tuple[str, str]],
    input_type: str = "document"
) -> list[Dict[str, Any]]:
    """
    Ingest multiple texts through orchestrator pipeline
    
    Args:
        texts: List of (text, source) tuples
        input_type: Type of input for all texts
    
    Returns:
        List of result dicts
    """
    results = []
    
    for i, (text, source) in enumerate(texts, 1):
        print(f"\n[{i}/{len(texts)}] Processing: {source}")
        result = ingest_text(text, source, input_type)
        results.append(result)
    
    return results

# API-compatible wrapper
def add_to_knowledge_base(
    content: str,
    source: str = "api",
    **kwargs
) -> Dict[str, Any]:
    """
    API-compatible wrapper for external integrations
    
    Use this endpoint from FastAPI routes, webhooks, etc.
    """
    return ingest_text(
        text=content,
        source=source,
        input_type=kwargs.get("type", "document"),
        metadata=kwargs.get("metadata", {})
    )

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest data through hook")
    parser.add_argument("--file", help="File to ingest")
    parser.add_argument("--text", help="Text to ingest")
    parser.add_argument("--source", default="manual", help="Source identifier")
    parser.add_argument("--type", default="document", help="Input type")
    
    args = parser.parse_args()
    
    if args.file:
        result = ingest_file(args.file, input_type=args.type)
    elif args.text:
        result = ingest_text(args.text, source=args.source, input_type=args.type)
    else:
        print("❌ Provide --file or --text")
        sys.exit(1)
    
    print(f"\n✅ Document ID: {result['document_id']}")
    print(f"📦 Chunks: {len(result['chunk_ids'])}")
    print(f"🧠 Concepts: {result['concepts']}")
