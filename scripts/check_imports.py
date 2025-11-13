"""
check_imports.py
Simple module import test for EFC package structure.
"""

def test(name):
    try:
        __import__(name)
        print(f"✓ {name}")
    except Exception as e:
        print(f"✗ {name}: {e}")


print("🔍 Testing EFC module imports...\n")

TESTS = [
    "src",
    "src.efc",
    "src.efc.core.efc_core",
    "src.efc.entropy.efc_entropy",
    "src.efc.potential.efc_potential",
    "src.efc.validation.efc_validation",
]

for t in TESTS:
    test(t)

print("\nDone.")
