#!/usr/bin/env python3
"""
Batch Ingest - Ingest entire repository using Orchestrator v2
=============================================================

This script processes all files in the repository through the
deterministic orchestrator pipeline, ensuring:
- Token-based chunking
- LLM concept extraction
- Perfect Qdrant ↔ Neo4j sync
- Rollback safety

Features:
- 📊 Real-time progress bar with tqdm
- ✅ Success/failure tracking
- 🔄 Resume capability (skip already processed)
- 📝 Detailed logging
- 📈 Statistics summary

Usage:
    python tools/batch_ingest.py --dir theory/
    python tools/batch_ingest.py --all
    python tools/batch_ingest.py --resume batch_ingest.log
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from orchestrator_v2 import orchestrate

# Import tqdm for progress bar
try:
    from tqdm import tqdm
except ImportError:
    print("⚠️  Installing tqdm for progress bars...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "tqdm"], check=True)
    from tqdm import tqdm

# File patterns to include
INCLUDE_PATTERNS = [
    "*.md",
    "*.py",
    "*.txt",
    "*.json",
    "*.jsonld",
    "*.yaml",
    "*.yml"
]

# Directories to exclude
EXCLUDE_DIRS = [
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".pytest_cache",
    "symbiose_gnn_output",
    ".vscode"
]

def should_process_file(file_path: Path) -> bool:
    """Check if file should be processed"""
    # Skip if in excluded directory
    for exclude in EXCLUDE_DIRS:
        if exclude in file_path.parts:
            return False
    
    # Check if matches include pattern
    for pattern in INCLUDE_PATTERNS:
        if file_path.match(pattern):
            return True
    
    return False

def collect_files(root_dir: Path) -> List[Path]:
    """Collect all files to process"""
    files = []
    
    for file_path in root_dir.rglob("*"):
        if file_path.is_file() and should_process_file(file_path):
            files.append(file_path)
    
    return sorted(files)

def load_processed_files(log_file: Path) -> set:
    """Load already processed files from log"""
    processed = set()
    if not log_file.exists():
        return processed
    
    with open(log_file) as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry.get("status") == "success":
                    processed.add(entry["file"])
            except:
                pass
    
    return processed

def batch_ingest(root_dir: Path, dry_run: bool = False, resume: Path = None, log_file: Path = None):
    """
    Ingest all files from root directory
    
    Args:
        root_dir: Root directory to process
        dry_run: If True, just list files without processing
        resume: Log file to resume from
        log_file: Log file to write results to
    """
    print(f"🔍 Scanning {root_dir}...")
    files = collect_files(root_dir)
    
    print(f"📁 Found {len(files)} files to process")
    
    # Resume logic
    processed = set()
    if resume and resume.exists():
        processed = load_processed_files(resume)
        print(f"📂 Resuming: skipping {len(processed)} already processed files")
    
    # Filter already processed
    remaining = [f for f in files if str(f.relative_to(root_dir)) not in processed]
    
    if not remaining:
        print("✅ All files already processed!")
        return
    
    print(f"📊 Processing {len(remaining)} files...\n")
    
    if dry_run:
        print("DRY RUN - Files that would be processed:")
        for f in remaining:
            print(f"  - {f.relative_to(root_dir)}")
        return
    
    results = []
    errors = []
    
    # Setup logging
    if log_file is None:
        log_file = Path("batch_ingest.log")
    log_handle = open(log_file, "a")
    
    # Progress bar with statistics
    stats = {"chunks": 0, "concepts": 0, "tokens": 0}
    
    with tqdm(total=len(remaining), desc="Ingesting", unit="file") as pbar:
        for file_path in remaining:
            relative_path = file_path.relative_to(root_dir)
            
            # Update progress bar description
            pbar.set_description(f"Processing {str(relative_path)[:40]}")
            
            try:
                # Read file
                text = file_path.read_text(encoding='utf-8', errors='ignore')
                
                if len(text.strip()) < 50:
                    # Log skip
                    log_entry = {
                        "timestamp": datetime.now().isoformat(),
                        "file": str(relative_path),
                        "status": "skipped",
                        "reason": "too short"
                    }
                    log_handle.write(json.dumps(log_entry) + "\n")
                    log_handle.flush()
                    pbar.update(1)
                    continue
                
                # Determine type
                input_type = "document"
                if "chat" in str(relative_path).lower() or "conversation" in str(relative_path).lower():
                    input_type = "chat"
                elif ".log" in file_path.suffix:
                    input_type = "log"
                
                # Process through orchestrator
                result = orchestrate(
                    text=text,
                    source=str(relative_path),
                    input_type=input_type,
                    metadata={
                        "file_path": str(file_path),
                        "file_type": file_path.suffix,
                        "file_size": len(text)
                    }
                )
                
                # Update statistics
                stats["chunks"] += len(result["chunk_ids"])
                stats["concepts"] += len(result["concepts"])
                stats["tokens"] += result["total_tokens"]
                
                result_entry = {
                    "file": str(relative_path),
                    "status": "success",
                    "document_id": result["document_id"],
                    "chunks": len(result["chunk_ids"]),
                    "concepts": len(result["concepts"]),
                    "tokens": result["total_tokens"]
                }
                results.append(result_entry)
                
                # Log success
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    **result_entry
                }
                log_handle.write(json.dumps(log_entry) + "\n")
                log_handle.flush()
                
                # Update progress bar with stats
                pbar.set_postfix({
                    "✅": len(results),
                    "❌": len(errors),
                    "chunks": stats["chunks"],
                    "concepts": stats["concepts"]
                })
            
            except Exception as e:
                error_entry = {
                    "file": str(relative_path),
                    "error": str(e)
                }
                errors.append(error_entry)
                
                # Log error
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "file": str(relative_path),
                    "status": "error",
                    "error": str(e)
                }
                log_handle.write(json.dumps(log_entry) + "\n")
                log_handle.flush()
                
                # Update progress bar
                pbar.set_postfix({
                    "✅": len(results),
                    "❌": len(errors),
                    "chunks": stats["chunks"],
                    "concepts": stats["concepts"]
                })
            
            # Update progress
            pbar.update(1)
    
    log_handle.close()    # Summary
    print("\n" + "=" * 80)
    print("📊 BATCH INGEST SUMMARY")
    print("=" * 80)
    print(f"✅ Successful:  {len(results)}/{len(remaining)}")
    print(f"❌ Errors:      {len(errors)}/{len(remaining)}")
    print(f"⏭️  Skipped:     {len(processed)} (already processed)")
    print(f"📦 Total files: {len(files)}")
    
    if results:
        print(f"\n📈 Statistics:")
        print(f"   Total chunks:   {stats['chunks']:,}")
        print(f"   Total concepts: {stats['concepts']:,}")
        print(f"   Total tokens:   {stats['tokens']:,}")
        print(f"   Avg chunks/file:   {stats['chunks'] / len(results):.1f}")
        print(f"   Avg concepts/file: {stats['concepts'] / len(results):.1f}")
    
    # Save summary
    summary_file = Path("batch_ingest_summary.json")
    with open(summary_file, "w") as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat(),
            "root_dir": str(root_dir),
            "total_files": len(files),
            "processed": len(results) + len(errors),
            "successful": len(results),
            "errors": len(errors),
            "skipped": len(processed),
            "statistics": stats,
            "recent_errors": errors[-10:] if errors else []
        }, f, indent=2)
    
    print(f"\n💾 Summary:  {summary_file}")
    print(f"📝 Log:      {log_file}")
    
    if errors:
        print(f"\n⚠️  {len(errors)} files failed:")
        for err in errors[:10]:  # Show first 10
            print(f"   - {err['file']}")
            print(f"     {err['error'][:100]}")
        if len(errors) > 10:
            print(f"   ... and {len(errors) - 10} more (see log file)")
    
    print("=" * 80)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch ingest repository files with progress tracking")
    parser.add_argument("--dir", help="Directory to process (default: current)")
    parser.add_argument("--all", action="store_true", help="Process entire repository")
    parser.add_argument("--dry-run", action="store_true", help="List files without processing")
    parser.add_argument("--resume", type=Path, help="Resume from log file (skip already processed)")
    parser.add_argument("--log", type=Path, default=Path("batch_ingest.log"), help="Log file path")
    
    args = parser.parse_args()
    
    if args.all:
        root = Path.cwd()
    elif args.dir:
        root = Path(args.dir)
    else:
        root = Path.cwd()
    
    if not root.exists():
        print(f"❌ Directory not found: {root}")
        sys.exit(1)
    
    batch_ingest(root, dry_run=args.dry_run, resume=args.resume, log_file=args.log)
