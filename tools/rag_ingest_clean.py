#!/usr/bin/env python3
"""
Clean RAG Ingest for EFC Repository
====================================

Ingests clean text (not full JSON-LD) with proper metadata to Qdrant.

Features:
- Extracts description/summary from JSON-LD files
- Chunks text into 300-800 character segments
- Deduplicates via content hashing
- Adds rich metadata (layer, doi, source_type, section)
- Uses OpenAI embeddings (3072-dim)

Usage:
    python tools/rag_ingest_clean.py [--dry-run] [--limit N]
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qdrant_client import QdrantClient
from apis.unified_api.clients.qdrant_client import qdrant_ingest

ROOT = Path(__file__).resolve().parents[1]

# Directories to process
INCLUDE_DIRS = [
    "docs",
    "meta",
    "figshare",
    "jsonld",
    "schema",
    "api",
]

EXCLUDE_PATTERNS = {
    ".git", ".venv", "__pycache__", "node_modules",
    ".mypy_cache", ".pytest_cache", "build", "dist"
}


def extract_text_from_jsonld(data: dict) -> Optional[str]:
    """
    Extract clean text from JSON-LD structure.
    Priority: description > summary > abstract > text content
    """
    if isinstance(data, str):
        return data
    
    if not isinstance(data, dict):
        return None
    
    # Try common text fields
    for field in ["description", "summary", "abstract", "text", "content"]:
        if field in data and isinstance(data[field], str):
            text = data[field].strip()
            if len(text) > 50:  # Minimum viable text
                return text
    
    # Try nested @value
    if "@value" in data:
        return str(data["@value"])
    
    # Try articleBody for schema.org
    if "articleBody" in data:
        return str(data["articleBody"])
    
    return None


def extract_metadata(data: dict, file_path: Path) -> Dict:
    """
    Extract rich metadata from JSON-LD.
    """
    meta = {
        "source_type": "jsonld",
        "path": str(file_path.relative_to(ROOT)),
    }
    
    # Schema.org fields
    if "@type" in data:
        meta["type"] = data["@type"]
    
    if "name" in data:
        meta["title"] = data["name"]
    elif "title" in data:
        meta["title"] = data["title"]
    
    # DOI or identifier
    if "doi" in data:
        meta["doi"] = data["doi"]
    elif "identifier" in data:
        meta["doi"] = data["identifier"]
    
    # Author
    if "author" in data:
        if isinstance(data["author"], dict):
            meta["author"] = data["author"].get("name")
        elif isinstance(data["author"], str):
            meta["author"] = data["author"]
    
    # Layer detection (figshare, meta, docs, etc.)
    parts = file_path.parts
    if "figshare" in parts:
        meta["layer"] = "figshare"
    elif "meta" in parts:
        meta["layer"] = "meta"
    elif "docs" in parts:
        meta["layer"] = "docs"
    elif "api" in parts:
        meta["layer"] = "api"
    
    return meta


def process_jsonld_file(file_path: Path) -> Optional[Dict]:
    """
    Process a single JSON-LD file.
    Returns (text, metadata) tuple or None.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        text = extract_text_from_jsonld(data)
        if not text:
            return None
        
        metadata = extract_metadata(data, file_path)
        
        return {
            "text": text,
            "metadata": metadata,
            "source": f"repo:{file_path.relative_to(ROOT)}"
        }
        
    except Exception as e:
        print(f"⚠️  Error processing {file_path}: {e}")
        return None


def process_markdown_file(file_path: Path) -> Optional[Dict]:
    """
    Process a Markdown file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        if len(text.strip()) < 100:
            return None
        
        # Extract title from first heading
        title = None
        for line in text.split('\n')[:10]:
            if line.startswith('# '):
                title = line[2:].strip()
                break
        
        metadata = {
            "source_type": "markdown",
            "path": str(file_path.relative_to(ROOT)),
            "title": title,
        }
        
        # Layer detection
        parts = file_path.parts
        if "meta" in parts:
            metadata["layer"] = "meta"
        elif "docs" in parts:
            metadata["layer"] = "docs"
        elif "methodology" in parts:
            metadata["layer"] = "methodology"
        
        return {
            "text": text,
            "metadata": metadata,
            "source": f"repo:{file_path.relative_to(ROOT)}"
        }
        
    except Exception as e:
        print(f"⚠️  Error processing {file_path}: {e}")
        return None


def iter_files() -> List[Path]:
    """
    Iterate all relevant files in repository.
    """
    files = []
    
    for dir_name in INCLUDE_DIRS:
        dir_path = ROOT / dir_name
        if not dir_path.exists():
            continue
        
        for file_path in dir_path.rglob("*"):
            if not file_path.is_file():
                continue
            
            # Skip excluded patterns
            if any(excl in file_path.parts for excl in EXCLUDE_PATTERNS):
                continue
            
            # Only process JSON-LD and Markdown
            if file_path.suffix in [".jsonld", ".json"]:
                files.append(file_path)
            elif file_path.suffix == ".md":
                files.append(file_path)
    
    return files


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean RAG ingest for EFC")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually ingest")
    parser.add_argument("--limit", type=int, help="Limit number of files")
    args = parser.parse_args()
    
    # Check environment
    if not os.getenv("QDRANT_URL"):
        print("❌ QDRANT_URL not set")
        return 1
    
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set")
        return 1
    
    print("🔍 Scanning repository...")
    files = iter_files()
    
    if args.limit:
        files = files[:args.limit]
    
    print(f"📄 Found {len(files)} files")
    
    ingested = 0
    skipped = 0
    
    for i, file_path in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] Processing {file_path.name}...")
        
        # Process based on type
        if file_path.suffix in [".jsonld", ".json"]:
            result = process_jsonld_file(file_path)
        elif file_path.suffix == ".md":
            result = process_markdown_file(file_path)
        else:
            skipped += 1
            continue
        
        if not result:
            print(f"  ⏭️  Skipped (no extractable text)")
            skipped += 1
            continue
        
        # Show preview
        text_preview = result["text"][:150].replace('\n', ' ')
        print(f"  📝 Text: {text_preview}...")
        print(f"  🏷️  Meta: {result['metadata'].get('layer', 'N/A')} | {result['metadata'].get('title', 'N/A')[:50]}")
        
        if args.dry_run:
            print(f"  🚫 DRY RUN - would ingest")
            continue
        
        # Ingest
        ingest_result = qdrant_ingest(
            text=result["text"],
            source=result["source"],
            metadata=result["metadata"]
        )
        
        if ingest_result.get("status") == "ok":
            chunks = ingest_result.get("chunks_ingested", 0)
            print(f"  ✅ Ingested {chunks} chunks")
            ingested += 1
        else:
            print(f"  ❌ Failed: {ingest_result.get('error')}")
            skipped += 1
    
    print(f"\n{'='*60}")
    print(f"✨ Done!")
    print(f"   Ingested: {ingested} files")
    print(f"   Skipped:  {skipped} files")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
