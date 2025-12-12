#!/usr/bin/env python3
"""
Quick test of authority filter on theory files
"""
import sys
sys.path.insert(0, 'tools')

# Force reload
import importlib
if 'authority_filter' in sys.modules:
    importlib.reload(sys.modules['authority_filter'])

from authority_filter import is_authoritative, get_authority_metadata

files = [
    'theory/README.md',
    'theory/architecture/README.md',
    'theory/architecture/index.md',
    'theory/formal/README.md',
    'theory/formal/efc-c0-model/README.md',
    'theory/formal/efc-c0-model/index.json',
]

print('Testing authority filter with theory files:')
print('=' * 60)

for f in files:
    auth = is_authoritative(f)
    if auth:
        meta = get_authority_metadata(f)
        print(f'✅ {f}')
        print(f'   {meta["authority_level"]}, trust={meta["trust_score"]}')
    else:
        print(f'❌ {f} - BLOCKED')

print('=' * 60)
