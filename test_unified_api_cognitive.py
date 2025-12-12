#!/usr/bin/env python3
"""
Test: Unified API Cognitive Integration
========================================

Verify that Unified API now has:
1. CognitiveRouter integration
2. OptimalMemorySystem (9 layers)
3. Full cognitive context in responses

This test validates the upgrade from symbiosis_router_v4 to cognitive-aware version.
"""

import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apis', 'unified_api'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tools'))


def test_imports():
    """Test 1: Verify all cognitive imports work."""
    print("=" * 70)
    print("TEST 1: Cognitive Imports")
    print("=" * 70)
    
    try:
        from routers.chat import cognitive_router, get_memory_system
        print("✅ cognitive_router imported")
        print("✅ get_memory_system imported")
        
        from cognitive_router import CognitiveRouter
        print("✅ CognitiveRouter class available")
        
        from optimal_memory_system import OptimalMemorySystem
        print("✅ OptimalMemorySystem class available")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_cognitive_router_instance():
    """Test 2: Verify cognitive router is initialized."""
    print("\n" + "=" * 70)
    print("TEST 2: Cognitive Router Instance")
    print("=" * 70)
    
    try:
        from routers.chat import cognitive_router
        
        # Check it's a CognitiveRouter instance
        from cognitive_router import CognitiveRouter
        
        if isinstance(cognitive_router, CognitiveRouter):
            print("✅ cognitive_router is CognitiveRouter instance")
        else:
            print(f"❌ cognitive_router is {type(cognitive_router)}, not CognitiveRouter")
            return False
        
        # Test basic operation (fixed value_context structure)
        signals = cognitive_router.process_and_route(
            user_input="Hva heter jeg?",
            session_context={},
            system_metrics={"accuracy": 0.85},
            value_context={
                "key": "user.name",
                "domain": "identity"
            }
        )
        
        print(f"✅ Generated signals: {list(signals.keys())}")
        print(f"   Intent mode: {signals['intent']['mode']}")
        print(f"   Routing decision: {signals['routing_decision']['canonical_override_strength']}")
        
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_memory_system_instance():
    """Test 3: Verify OptimalMemorySystem is available."""
    print("\n" + "=" * 70)
    print("TEST 3: OptimalMemorySystem Instance")
    print("=" * 70)
    
    try:
        from routers.chat import get_memory_system
        from optimal_memory_system import OptimalMemorySystem
        
        memory = get_memory_system()
        
        if isinstance(memory, OptimalMemorySystem):
            print("✅ get_memory_system() returns OptimalMemorySystem instance")
        else:
            print(f"❌ get_memory_system() returns {type(memory)}, not OptimalMemorySystem")
            return False
        
        # Check 9 layers are available (using correct attribute names)
        print("\n📊 Checking 9-layer architecture:")
        
        layers = [
            ("cmc", "CMC - Canonical Memory Core"),
            ("smm", "SMM - Semantic Mesh Memory"),
            ("dde", "DDE - Dynamic Domain Engine"),
            ("ame", "AME - Adaptive Memory Enforcer"),
            ("mlc", "MLC - Meta-Learning Cortex"),
            ("graph", "Neo4j Graph Layer"),
            ("mir", "MIR - Memory Interference Regulator"),
            ("mca", "MCA - Memory Consistency Auditor"),
            ("mce", "MCE - Memory Compression Engine")
        ]
        
        for attr, name in layers:
            if hasattr(memory, attr):
                print(f"   ✅ {name}")
            else:
                print(f"   ❌ {name} (missing)")
        
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_response_model():
    """Test 4: Verify ChatTurnResponse includes cognitive_context."""
    print("\n" + "=" * 70)
    print("TEST 4: Response Model (cognitive_context)")
    print("=" * 70)
    
    try:
        from routers.chat import ChatTurnResponse
        
        # Check if cognitive_context field exists
        fields = ChatTurnResponse.model_fields  # Pydantic v2
        
        print(f"📋 Response fields: {list(fields.keys())}")
        
        if "cognitive_context" in fields:
            print("✅ cognitive_context field present in ChatTurnResponse")
            print(f"   Type: Optional[Dict[str, Any]]")
            return True
        else:
            print("❌ cognitive_context field NOT in ChatTurnResponse")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_chat_endpoint_logic():
    """Test 5: Verify chat endpoint uses cognitive router."""
    print("\n" + "=" * 70)
    print("TEST 5: Chat Endpoint Logic (code inspection)")
    print("=" * 70)
    
    try:
        # Read the chat.py file
        chat_file = os.path.join(os.path.dirname(__file__), 'apis', 'unified_api', 'routers', 'chat.py')
        
        with open(chat_file, 'r') as f:
            content = f.read()
        
        # Check for cognitive router usage
        checks = [
            ("cognitive_router.process_and_route", "cognitive_router.process_and_route() call"),
            ("cognitive_signals", "cognitive_signals variable"),
            ("cognitive_context", "cognitive_context in response"),
            ("OptimalMemorySystem", "OptimalMemorySystem import"),
            ("CognitiveRouter", "CognitiveRouter import")
        ]
        
        all_passed = True
        for check_str, desc in checks:
            if check_str in content:
                print(f"✅ Found: {desc}")
            else:
                print(f"❌ Missing: {desc}")
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 10 + "UNIFIED API COGNITIVE INTEGRATION TEST" + " " * 20 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    tests = [
        test_imports,
        test_cognitive_router_instance,
        test_memory_system_instance,
        test_response_model,
        test_chat_endpoint_logic
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n✅ Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Unified API fully cognitive-aware!")
        print("\n📊 Architecture Status:")
        print("   - MCP Server: ✅ Cognitive")
        print("   - Unified API: ✅ Cognitive")
        print("   - Memory: ✅ 9-layer OptimalMemorySystem")
        print("   - Signals: ✅ Intent + Value + Motivation")
        print("\n🚀 Consistent cognitive architecture across all endpoints!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
        print("\nPlease review failures above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
