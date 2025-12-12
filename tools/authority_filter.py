#!/usr/bin/env python3
"""
Gold Standard Authority Filter
===============================

Determines which files are authoritative sources (can be used for GNN training)
vs. non-authoritative (metadata/navigation only).

Hierarchy:
- PRIMARY: pdf, tex, py (theory/sim), ipynb (validated), jsonld, schema
- SECONDARY: md (full theory only, not README), yml/yaml (experiments)
- REFERENCE: bib (traceability, not knowledge)
- NON-AUTHORITATIVE: README, index, TODO, notes, chat logs, _generated

Usage:
    from tools.authority_filter import is_authoritative, get_trust_score
    
    if is_authoritative(file_path):
        score = get_trust_score(file_path)
"""

from pathlib import Path
from typing import Tuple
import re


# ============================================================================
# GOLD STANDARD DEFINITIONS
# ============================================================================

PRIMARY_EXTENSIONS = {
    '.pdf',      # Frozen, publishable truth
    '.tex',      # Formal mathematics, minimal ambiguity
    '.py',       # Operational physics (theory models, formulas, sims)
    '.ipynb',    # Reproducible empirics (validated experiments)
    '.jsonld',   # Machine-readable ontology
    '.json',     # Formal rules (when schema.json)
}

SECONDARY_EXTENSIONS = {
    '.md',       # Readable mirroring of PDF/TEX (theory only, not README)
    '.yml',      # Controlled runs (experiments)
    '.yaml',
}

REFERENCE_EXTENSIONS = {
    '.bib',      # Not knowledge, but traceability
}

# Non-authoritative patterns (exact matches or substrings)
# Note: theory/ folder READMEs ARE authoritative (contain actual theory)
NON_AUTHORITATIVE_PATTERNS = [
    'TODO.md',
    'todo.md',
    'notes.md',
    'NOTES.md',
    'CHANGELOG.md',
    'changelog.md',
    '_generated',
    'embeddings',
    'chat-log',
    'chatlog',
]

# Root-level navigation files (non-authoritative)
ROOT_NAV_FILES = {
    'README.md',
    'START-HERE.md',
    'OVERVIEW.md',
    'index.md',
    'INDEX.md',
}

# Non-authoritative directories (should be excluded entirely)
NON_AUTHORITATIVE_DIRS = {
    '_generated',
    'embeddings',
    'chat-logs',
    'chatlogs',
    '.git',
    'node_modules',
    '__pycache__',
    '.venv',
    'venv',
}

# Python files that are NOT theory/simulation (tooling/infrastructure)
NON_THEORY_PY_PATTERNS = [
    'test_',
    '_test.py',
    'setup.py',
    'conftest.py',
    '__init__.py',
    'orchestrator',
    'gnn_export',
    'gnn_train',
    'gnn_inference',
    'authority_filter',
    'rag_',
]

# Theory/simulation Python patterns (these ARE authoritative)
THEORY_PY_PATTERNS = [
    'efc_',
    'energy_flow',
    'entropy_',
    'simulation',
    'model',
    'theory',
    'formula',
    'equations',
]


# ============================================================================
# AUTHORITY DETERMINATION
# ============================================================================

def is_authoritative(file_path: str | Path, content_preview: str = None) -> bool:
    """
    Determine if a file is an authoritative source (gold standard).
    
    Rules:
    1. Can it be published in a journal? → ✅
    2. Can it be compiled or run deterministically? → ✅
    3. Is it only explanatory or administrative? → ❌
    4. Is it raw reflection or dialogue? → ❌
    
    Special case: theory/ folder README.md files ARE authoritative
    (they contain actual theory content, not just navigation)
    
    Args:
        file_path: Path to the file
        content_preview: Optional first 500 chars to check content heuristics
        
    Returns:
        True if authoritative, False otherwise
    """
    path = Path(file_path)
    path_str = str(path)
    
    # Check if in non-authoritative directory
    for part in path.parts:
        if part in NON_AUTHORITATIVE_DIRS:
            return False
    
    # Special case: theory/ folder - EVERYTHING is authoritative!
    # Include all files: README.md, index.md, notes, etc.
    if 'theory/' in path_str:
        return True
    
    # Check root-level navigation files (non-authoritative)
    if path.name in ROOT_NAV_FILES and len(path.parts) <= 2:
        return False
    
    # Check non-authoritative patterns
    file_name = path.name.lower()
    file_str = path_str.lower()
    for pattern in NON_AUTHORITATIVE_PATTERNS:
        if pattern.lower() in file_str:
            return False
    
    # Get extension
    ext = path.suffix.lower()
    
    # PRIMARY extensions are always authoritative (except special cases)
    if ext in PRIMARY_EXTENSIONS:
        # Special case: Python files need content check
        if ext == '.py':
            return _is_theory_python(path)
        # Special case: JSON must be schema-related
        if ext == '.json':
            return 'schema' in file_str or 'ontology' in file_str
        return True
    
    # SECONDARY extensions need content validation
    if ext in SECONDARY_EXTENSIONS:
        # Markdown must NOT be README/index/etc (already checked above)
        # and should contain theory content
        if ext == '.md':
            if content_preview:
                return _is_theory_markdown(content_preview)
            # Conservative: assume theory if not README/index
            return True
        # YAML must be experiment config
        if ext in {'.yml', '.yaml'}:
            return 'experiment' in file_str or 'config' in file_str
    
    # REFERENCE extensions are marked but not authoritative for training
    if ext in REFERENCE_EXTENSIONS:
        return False
    
    # Unknown extension
    return False


def _is_theory_python(path: Path) -> bool:
    """Check if Python file contains theory/simulation (not tooling)."""
    file_name = path.name.lower()
    
    # Exclude non-theory patterns
    for pattern in NON_THEORY_PY_PATTERNS:
        if pattern in file_name:
            return False
    
    # Include theory patterns
    for pattern in THEORY_PY_PATTERNS:
        if pattern in file_name:
            return True
    
    # Check directory context
    path_str = str(path).lower()
    if any(x in path_str for x in ['theory/', 'models/', 'simulation/']):
        return True
    
    # Conservative: exclude if uncertain
    return False


def _is_theory_markdown(content_preview: str) -> bool:
    """
    Check if markdown contains theory content (not just navigation).
    
    Heuristics:
    - Has equations (LaTeX)
    - Has scientific references
    - Has structured theory sections
    - NOT just links/navigation
    """
    if not content_preview:
        return False
    
    preview_lower = content_preview.lower()
    
    # Strong theory indicators
    theory_indicators = [
        r'\$\$',           # LaTeX block equations
        r'\$[^$]+\$',      # Inline LaTeX
        'theorem',
        'lemma',
        'proof',
        'equation',
        'entropy',
        'energy flow',
        'field theory',
        'cosmology',
    ]
    
    theory_score = sum(1 for ind in theory_indicators if re.search(ind, preview_lower))
    
    # Weak navigation indicators
    nav_indicators = [
        '## table of contents',
        '## navigation',
        '## links',
        '## overview',
        '## getting started',
        '## installation',
    ]
    
    nav_score = sum(1 for ind in nav_indicators if ind in preview_lower)
    
    # Decision: theory if more theory indicators than nav
    return theory_score > nav_score


# ============================================================================
# TRUST SCORE SYSTEM
# ============================================================================

def get_trust_score(file_path: str | Path) -> float:
    """
    Get trust score for a file (0.0 - 1.0).
    
    Trust hierarchy:
    - PRIMARY: 1.0 (pdf, tex, py-theory, ipynb, jsonld, schema, theory/* files)
    - SECONDARY: 0.8 (md-theory, yml-experiment)
    - REFERENCE: 0.5 (bib)
    - NON-AUTHORITATIVE: 0.0
    
    Special: ALL files in theory/ folder get PRIMARY trust (1.0)
    
    Args:
        file_path: Path to the file
        
    Returns:
        Trust score between 0.0 and 1.0
    """
    if not is_authoritative(file_path):
        return 0.0
    
    path = Path(file_path)
    path_str = str(path)
    ext = path.suffix.lower()
    
    # Special: ALL theory/ files are PRIMARY
    if 'theory/' in path_str:
        return 1.0
    
    # PRIMARY
    if ext in {'.pdf', '.tex', '.jsonld'}:
        return 1.0
    if ext == '.py' and _is_theory_python(path):
        return 1.0
    if ext == '.ipynb':
        return 1.0
    if ext == '.json' and ('schema' in path.name.lower() or 'ontology' in path.name.lower()):
        return 1.0
    
    # SECONDARY
    if ext == '.md':
        return 0.8
    if ext in {'.yml', '.yaml'}:
        return 0.8
    
    # REFERENCE
    if ext == '.bib':
        return 0.5
    
    # Default for authoritative but unclassified
    return 0.7


def get_authority_metadata(file_path: str | Path) -> dict:
    """
    Get complete authority metadata for a file.
    
    Returns:
        {
            'is_authoritative': bool,
            'trust_score': float,
            'authority_level': str,  # PRIMARY, SECONDARY, REFERENCE, NONE
            'reasoning': str
        }
    """
    path = Path(file_path)
    is_auth = is_authoritative(path)
    trust = get_trust_score(path)
    
    if not is_auth:
        return {
            'is_authoritative': False,
            'trust_score': 0.0,
            'authority_level': 'NONE',
            'reasoning': 'Non-authoritative (README, navigation, or tooling)'
        }
    
    ext = path.suffix.lower()
    
    # Determine level
    if trust == 1.0:
        level = 'PRIMARY'
        reasoning = f'Gold standard: {ext} is frozen/publishable/operational truth'
    elif trust >= 0.8:
        level = 'SECONDARY'
        reasoning = f'Authoritative: {ext} mirrors primary sources'
    elif trust >= 0.5:
        level = 'REFERENCE'
        reasoning = f'Reference: {ext} provides traceability'
    else:
        level = 'UNCERTAIN'
        reasoning = f'Authoritative but uncertain classification'
    
    return {
        'is_authoritative': True,
        'trust_score': trust,
        'authority_level': level,
        'reasoning': reasoning
    }


# ============================================================================
# BATCH FILTERING
# ============================================================================

def filter_authoritative_files(file_paths: list[str | Path]) -> list[Path]:
    """
    Filter list of files to only authoritative sources.
    
    Args:
        file_paths: List of file paths
        
    Returns:
        List of Path objects for authoritative files only
    """
    return [Path(p) for p in file_paths if is_authoritative(p)]


def get_file_statistics(file_paths: list[str | Path]) -> dict:
    """
    Get statistics about authority levels in file list.
    
    Returns:
        {
            'total': int,
            'authoritative': int,
            'non_authoritative': int,
            'primary': int,
            'secondary': int,
            'reference': int,
            'by_extension': dict
        }
    """
    stats = {
        'total': len(file_paths),
        'authoritative': 0,
        'non_authoritative': 0,
        'primary': 0,
        'secondary': 0,
        'reference': 0,
        'by_extension': {}
    }
    
    for path in file_paths:
        meta = get_authority_metadata(path)
        ext = Path(path).suffix.lower()
        
        # Update extension counts
        if ext not in stats['by_extension']:
            stats['by_extension'][ext] = {'total': 0, 'authoritative': 0}
        stats['by_extension'][ext]['total'] += 1
        
        if meta['is_authoritative']:
            stats['authoritative'] += 1
            stats['by_extension'][ext]['authoritative'] += 1
            
            if meta['authority_level'] == 'PRIMARY':
                stats['primary'] += 1
            elif meta['authority_level'] == 'SECONDARY':
                stats['secondary'] += 1
            elif meta['authority_level'] == 'REFERENCE':
                stats['reference'] += 1
        else:
            stats['non_authoritative'] += 1
    
    return stats


# ============================================================================
# CLI TESTING
# ============================================================================

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python authority_filter.py <file_path>")
        print("\nTest cases:")
        test_files = [
            'docs/papers/efc/paper.pdf',
            'docs/papers/efc/paper.tex',
            'docs/papers/efc/paper.md',
            'docs/papers/efc/README.md',
            'theory/efc_entropy_model.py',
            'tools/orchestrator_v2.py',
            'experiments/simulation.ipynb',
            'schema/ontology.jsonld',
        ]
        for tf in test_files:
            meta = get_authority_metadata(tf)
            print(f"\n{tf}:")
            print(f"  ✅ {meta['authority_level']} (trust={meta['trust_score']:.1f})")
            print(f"  → {meta['reasoning']}")
        sys.exit(0)
    
    # Test specific file
    file_path = sys.argv[1]
    meta = get_authority_metadata(file_path)
    
    print(f"\n📄 File: {file_path}")
    print(f"{'='*60}")
    print(f"Authoritative: {meta['is_authoritative']}")
    print(f"Trust Score:   {meta['trust_score']:.2f}")
    print(f"Level:         {meta['authority_level']}")
    print(f"Reasoning:     {meta['reasoning']}")
    
    if meta['is_authoritative']:
        print(f"\n✅ GNN Training: YES")
        print(f"✅ Qdrant Weight: {meta['trust_score']:.2f}")
    else:
        print(f"\n❌ GNN Training: NO")
        print(f"⚠️  Use for: Navigation/metadata only")
