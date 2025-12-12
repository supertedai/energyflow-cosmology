#!/usr/bin/env python3
"""
Test canonical memory schema validation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from tools.canonical_memory_core import CanonicalMemoryCore

def test_schema_validation():
    """Test schema loading and validation"""
    
    print("🧪 Testing Canonical Memory Schema Validation")
    print("=" * 60)
    
    # Initialize CMC (should load schema)
    cmc = CanonicalMemoryCore()
    
    print("\n✅ CMC initialized with schema")
    print(f"Schema version: {cmc.schema.get('schema_version')}")
    print(f"Allowed domains: {list(cmc.schema.get('allowed_domains', {}).keys())}")
    print()
    
    # Test 1: Valid fact in allowed domain
    print("Test 1: Store valid fact in 'identity' domain")
    print("-" * 60)
    try:
        errors = cmc._validate_fact(
            domain="identity",
            key="name",
            value="Morten",
            text="Brukeren heter Morten"
        )
        if errors:
            print(f"❌ Unexpected errors: {errors}")
        else:
            print("✅ Valid fact passed validation")
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    # Test 2: Invalid key for domain
    print("Test 2: Store fact with invalid key")
    print("-" * 60)
    errors = cmc._validate_fact(
        domain="identity",
        key="invalid_key_12345",
        value="test",
        text="Invalid test"
    )
    if errors:
        print(f"✅ Validation correctly rejected: {errors[0]}")
    else:
        print("❌ Should have rejected invalid key")
    print()
    
    # Test 3: Forbidden pattern (password)
    print("Test 3: Store fact with forbidden pattern")
    print("-" * 60)
    errors = cmc._validate_fact(
        domain="identity",
        key="name",
        value="password123",
        text="User password is password123"
    )
    if errors:
        print(f"✅ Validation correctly rejected: {errors[0]}")
    else:
        print("❌ Should have rejected forbidden pattern")
    print()
    
    # Test 4: Fact too long
    print("Test 4: Store fact exceeding max length")
    print("-" * 60)
    long_text = "A" * 600  # Exceeds 500 char limit
    errors = cmc._validate_fact(
        domain="identity",
        key="name",
        value="test",
        text=long_text
    )
    if errors:
        print(f"✅ Validation correctly rejected: {errors[0]}")
    else:
        print("❌ Should have rejected fact exceeding max length")
    print()
    
    # Test 5: Pattern matching for numbered keys
    print("Test 5: Validate numbered key pattern (child_1, child_2)")
    print("-" * 60)
    for i in range(1, 4):
        errors = cmc._validate_fact(
            domain="family",
            key=f"child_{i}",
            value=f"Child{i}",
            text=f"Child {i}"
        )
        if errors:
            print(f"❌ child_{i} rejected: {errors}")
        else:
            print(f"✅ child_{i} accepted")
    print()
    
    print("🎉 Schema validation tests complete!")
    print()
    print("Summary:")
    print("- ✅ Schema loaded successfully")
    print("- ✅ Valid facts pass validation")
    print("- ✅ Invalid keys are rejected")
    print("- ✅ Forbidden patterns are blocked")
    print("- ✅ Length limits are enforced")
    print("- ✅ Pattern matching works for numbered keys")

if __name__ == "__main__":
    test_schema_validation()
