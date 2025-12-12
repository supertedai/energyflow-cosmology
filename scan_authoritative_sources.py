#!/usr/bin/env python3
"""
Scan Entire Repository for Authoritative Sources
=================================================

Scans all directories to find gold standard files for ingestion.
Uses authority_filter.py to classify files.

Target directories:
- docs/ (papers, specifications)
- meta/ (ontologies, schemas)
- methodology/ (theory, frameworks)
- theory/ (formal models)
- notebooks/ (validated experiments)
- models/ (simulations)
- Any other directories with scientific content
"""

import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from tools.authority_filter import (
    get_authority_metadata,
    get_file_statistics,
    is_authoritative
)


def scan_directory(root_dir: Path, exclude_dirs: set = None) -> dict:
    """
    Recursively scan directory for all files.
    
    Returns:
        {
            'all_files': list,
            'by_directory': dict,
            'by_extension': dict,
            'stats': dict
        }
    """
    if exclude_dirs is None:
        exclude_dirs = {
            '.git', 'node_modules', '__pycache__', '.venv', 'venv',
            '.pytest_cache', '.mypy_cache', 'dist', 'build',
            'symbiose_gnn_output', '_generated'
        }
    
    all_files = []
    by_directory = defaultdict(list)
    by_extension = defaultdict(list)
    
    for path in root_dir.rglob('*'):
        # Skip directories
        if path.is_dir():
            continue
        
        # Skip excluded directories
        if any(ex in path.parts for ex in exclude_dirs):
            continue
        
        # Skip hidden files
        if any(part.startswith('.') for part in path.parts):
            continue
        
        all_files.append(path)
        by_directory[path.parent].append(path)
        by_extension[path.suffix].append(path)
    
    return {
        'all_files': all_files,
        'by_directory': by_directory,
        'by_extension': by_extension,
    }


def categorize_by_authority(files: list) -> dict:
    """
    Categorize files by authority level.
    
    Returns:
        {
            'primary': list,
            'secondary': list,
            'reference': list,
            'non_authoritative': list
        }
    """
    primary = []
    secondary = []
    reference = []
    non_auth = []
    
    for file_path in files:
        meta = get_authority_metadata(file_path)
        
        if not meta['is_authoritative']:
            non_auth.append(file_path)
        elif meta['authority_level'] == 'PRIMARY':
            primary.append(file_path)
        elif meta['authority_level'] == 'SECONDARY':
            secondary.append(file_path)
        elif meta['authority_level'] == 'REFERENCE':
            reference.append(file_path)
    
    return {
        'primary': primary,
        'secondary': secondary,
        'reference': reference,
        'non_authoritative': non_auth
    }


def print_report(scan_result: dict, categories: dict, root_dir: Path):
    """Print comprehensive report."""
    
    print("\n" + "="*80)
    print("📊 REPOSITORY AUTHORITY SCAN")
    print("="*80)
    
    total_files = len(scan_result['all_files'])
    auth_files = len(categories['primary']) + len(categories['secondary'])
    
    print(f"\n📁 Root: {root_dir}")
    print(f"📄 Total files: {total_files}")
    print(f"✅ Authoritative: {auth_files} ({auth_files/total_files*100:.1f}%)")
    print(f"❌ Non-authoritative: {len(categories['non_authoritative'])} ({len(categories['non_authoritative'])/total_files*100:.1f}%)")
    
    # By authority level
    print("\n" + "-"*80)
    print("🏆 BY AUTHORITY LEVEL")
    print("-"*80)
    print(f"PRIMARY (trust=1.0):     {len(categories['primary']):4d} files")
    print(f"SECONDARY (trust=0.8):   {len(categories['secondary']):4d} files")
    print(f"REFERENCE (trust=0.5):   {len(categories['reference']):4d} files")
    print(f"NON-AUTHORITATIVE:       {len(categories['non_authoritative']):4d} files")
    
    # By extension
    print("\n" + "-"*80)
    print("📋 BY FILE TYPE")
    print("-"*80)
    
    ext_stats = {}
    for level, files in categories.items():
        for f in files:
            ext = f.suffix.lower() or '(no ext)'
            if ext not in ext_stats:
                ext_stats[ext] = {'primary': 0, 'secondary': 0, 'reference': 0, 'non_auth': 0}
            if level == 'primary':
                ext_stats[ext]['primary'] += 1
            elif level == 'secondary':
                ext_stats[ext]['secondary'] += 1
            elif level == 'reference':
                ext_stats[ext]['reference'] += 1
            else:
                ext_stats[ext]['non_auth'] += 1
    
    # Sort by total authoritative files
    sorted_exts = sorted(
        ext_stats.items(),
        key=lambda x: x[1]['primary'] + x[1]['secondary'],
        reverse=True
    )
    
    for ext, counts in sorted_exts[:15]:  # Top 15
        total = sum(counts.values())
        auth = counts['primary'] + counts['secondary']
        if auth > 0:
            print(f"{ext:12s} | Total: {total:4d} | ✅ Auth: {auth:4d} (P:{counts['primary']:3d} S:{counts['secondary']:3d})")
    
    # By directory
    print("\n" + "-"*80)
    print("📂 TOP DIRECTORIES (by authoritative files)")
    print("-"*80)
    
    dir_stats = defaultdict(lambda: {'primary': 0, 'secondary': 0})
    for level, files in [('primary', categories['primary']), ('secondary', categories['secondary'])]:
        for f in files:
            # Get relative path from root
            try:
                rel = f.relative_to(root_dir)
                # Get top-level dir
                top_dir = rel.parts[0] if len(rel.parts) > 1 else str(rel)
                dir_stats[top_dir][level] += 1
            except ValueError:
                continue
    
    sorted_dirs = sorted(
        dir_stats.items(),
        key=lambda x: x[1]['primary'] + x[1]['secondary'],
        reverse=True
    )
    
    for dirname, counts in sorted_dirs[:20]:  # Top 20
        total = counts['primary'] + counts['secondary']
        print(f"{dirname:30s} | ✅ {total:4d} (P:{counts['primary']:3d} S:{counts['secondary']:3d})")
    
    # Primary files detail
    print("\n" + "-"*80)
    print("🥇 PRIMARY SOURCE FILES (Gold Standard)")
    print("-"*80)
    
    primary_by_type = defaultdict(list)
    for f in categories['primary']:
        ext = f.suffix.lower() or '(no ext)'
        try:
            rel = f.relative_to(root_dir)
            primary_by_type[ext].append(str(rel))
        except ValueError:
            primary_by_type[ext].append(str(f))
    
    for ext in sorted(primary_by_type.keys()):
        files = primary_by_type[ext]
        print(f"\n{ext} ({len(files)} files):")
        for fp in sorted(files)[:10]:  # Show first 10
            print(f"  - {fp}")
        if len(files) > 10:
            print(f"  ... and {len(files)-10} more")


def generate_ingest_script(categories: dict, root_dir: Path, output_file: str = "ingest_gold_standard.sh"):
    """Generate shell script to ingest all authoritative files."""
    
    # Combine primary and secondary
    files_to_ingest = categories['primary'] + categories['secondary']
    
    # Sort by directory for better processing
    files_to_ingest = sorted(files_to_ingest, key=lambda x: (x.parent, x.name))
    
    script_lines = [
        "#!/bin/bash",
        "#",
        "# AUTO-GENERATED: Ingest all authoritative sources",
        "# Generated by scan_authoritative_sources.py",
        "#",
        f"# Total files: {len(files_to_ingest)}",
        f"# Primary: {len(categories['primary'])}",
        f"# Secondary: {len(categories['secondary'])}",
        "#",
        "",
        "set -e  # Exit on error",
        "",
        "echo '🚀 Starting gold standard ingest...'",
        "echo '================================================'",
        "echo ''",
        "",
        f"total_files={len(files_to_ingest)}",
        "success_count=0",
        "error_count=0",
        "",
    ]
    
    for idx, file_path in enumerate(files_to_ingest, 1):
        try:
            rel_path = file_path.relative_to(root_dir)
        except ValueError:
            rel_path = file_path
        
        meta = get_authority_metadata(file_path)
        
        script_lines.extend([
            f"# [{idx}/{len(files_to_ingest)}] {meta['authority_level']} (trust={meta['trust_score']})",
            f"echo '[{idx}/{len(files_to_ingest)}] Processing: {rel_path}'",
            f"echo '-------------------------------------------'",
            f"if source .venv/bin/activate && python tools/orchestrator_v2.py --input \"{rel_path}\" --type document; then",
            f"    echo '✅ Success: {rel_path}'",
            f"    ((success_count++))",
            f"else",
            f"    echo '❌ Error: {rel_path}'",
            f"    ((error_count++))",
            f"fi",
            f"echo ''",
            "",
        ])
    
    # Final report
    script_lines.extend([
        "echo '================================================'",
        "echo '📊 FINAL REPORT'",
        "echo '================================================'",
        "echo \"Total files:   $total_files\"",
        "echo \"✅ Successful: $success_count\"",
        "echo \"❌ Errors:     $error_count\"",
        "echo ''",
        "",
        "# Database status",
        "echo '📊 Database status:'",
        "source .venv/bin/activate && python -c \"",
        "from neo4j import GraphDatabase",
        "from qdrant_client import QdrantClient",
        "import os",
        "from dotenv import load_dotenv",
        "load_dotenv()",
        "driver = GraphDatabase.driver(",
        "    os.getenv('NEO4J_URI'),",
        "    auth=(os.getenv('NEO4J_USER'), 'N-HPl8pKFVwsMgCzydGI26dsgJAMOP1ss6r1NhiHNjs')",
        ")",
        "with driver.session() as session:",
        "    concepts = session.run('MATCH (c:Concept) RETURN count(c) as total').single()['total']",
        "    docs = session.run('MATCH (d:Document) RETURN count(d) as total').single()['total']",
        "    chunks = session.run('MATCH (ch:Chunk) RETURN count(ch) as total').single()['total']",
        "    relations = session.run('MATCH ()-[r:RELATES_TO]->() RETURN count(r) as total').single()['total']",
        "client = QdrantClient(url=os.getenv('QDRANT_URL'), api_key=os.getenv('QDRANT_API_KEY'))",
        "vectors = client.get_collection('efc').points_count",
        "print(f'   Concepts: {concepts}')",
        "print(f'   Documents: {docs}')",
        "print(f'   Chunks: {chunks}')",
        "print(f'   Relations: {relations}')",
        "print(f'   Vectors: {vectors}')",
        "driver.close()",
        "\"",
        "",
        "echo ''",
        "echo '✅ Gold standard ingest complete!'",
    ])
    
    script_content = "\n".join(script_lines)
    
    output_path = root_dir / output_file
    output_path.write_text(script_content)
    output_path.chmod(0o755)  # Make executable
    
    print(f"\n✅ Generated: {output_path}")
    print(f"   Files to ingest: {len(files_to_ingest)}")
    print(f"   Run with: ./{output_file}")


if __name__ == '__main__':
    repo_root = Path(__file__).parent
    
    print("🔍 Scanning repository for authoritative sources...")
    print(f"📁 Root: {repo_root}")
    
    # Scan
    scan_result = scan_directory(repo_root)
    
    # Categorize
    categories = categorize_by_authority(scan_result['all_files'])
    
    # Print report
    print_report(scan_result, categories, repo_root)
    
    # Generate ingest script
    print("\n" + "="*80)
    generate_ingest_script(categories, repo_root)
    
    print("\n" + "="*80)
    print("✅ Scan complete!")
    print("="*80)
