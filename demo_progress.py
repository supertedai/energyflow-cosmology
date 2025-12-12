#!/usr/bin/env python3
"""
Demo Progress Bar - Viser hvordan batch_ingest.py ser ut
"""
import time
from tqdm import tqdm

print("🔍 Scanning files...")
print("📁 Found 587 files to process")
print("📊 Processing files...\n")

# Simuler file processing med progress bar
stats = {"success": 0, "failed": 0, "chunks": 0, "concepts": 0}

files = [f"file_{i}.md" for i in range(50)]  # 50 filer for demo

with tqdm(total=len(files), desc="Ingesting", unit="file") as pbar:
    for i, filename in enumerate(files):
        # Update description
        pbar.set_description(f"Processing {filename[:30]}")
        
        # Simuler processing
        time.sleep(0.1)  # Rask for demo
        
        # Simuler success (95% success rate)
        if i % 20 != 0:  # Success
            stats["success"] += 1
            stats["chunks"] += 15
            stats["concepts"] += 5
        else:  # Occasional failure
            stats["failed"] += 1
        
        # Update progress bar with live stats
        pbar.set_postfix({
            "✅": stats["success"],
            "❌": stats["failed"],
            "chunks": stats["chunks"],
            "concepts": stats["concepts"]
        })
        
        pbar.update(1)

print("\n" + "=" * 80)
print("📊 INGESTION SUMMARY")
print("=" * 80)
print(f"✅ Successful:  {stats['success']}/{len(files)}")
print(f"❌ Failed:      {stats['failed']}/{len(files)}")
print(f"\n📈 Statistics:")
print(f"   Total chunks:   {stats['chunks']:,}")
print(f"   Total concepts: {stats['concepts']:,}")
print(f"   Avg chunks/file:   {stats['chunks'] / stats['success']:.1f}")
print(f"   Avg concepts/file: {stats['concepts'] / stats['success']:.1f}")
print("=" * 80)
