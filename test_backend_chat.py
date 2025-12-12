#!/usr/bin/env python3
"""
Test Backend Chat API - Verify COMPLETE integration
Tests that backend API returns ALL expected fields from symbiosis_router_v3
"""

import requests
import json
import sys

API_BASE = "http://localhost:8000"

def test_backend_health():
    """Test that backend is running."""
    print("🔍 Testing backend health...")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is healthy")
            return True
        else:
            print(f"❌ Backend returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend not reachable: {e}")
        return False


def test_chat_health():
    """Test chat router health."""
    print("\n🔍 Testing chat router health...")
    try:
        response = requests.get(f"{API_BASE}/chat/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chat router healthy: {data}")
            return True
        else:
            print(f"❌ Chat router returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Chat router error: {e}")
        return False


def test_identity_override():
    """Test that memory enforcement works (identity question)."""
    print("\n🔍 Testing memory enforcement (identity)...")
    
    payload = {
        "user_message": "Hva heter du?",
        "assistant_draft": "Jeg heter Qwen"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/chat/turn",
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ API returned {response.status_code}")
            print(response.text)
            return False
        
        data = response.json()
        
        # Verify ALL expected fields exist
        required_fields = [
            'final_answer',
            'original_answer',
            'was_overridden',
            'conflict_reason',
            'memory_used',
            'memory_stored',
            'gnn',
            'retrieved_chunks',
            'metadata'
        ]
        
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            print(f"❌ Missing fields: {missing_fields}")
            return False
        
        print("✅ All required fields present")
        
        # Verify memory enforcement
        if data['was_overridden']:
            print(f"✅ Memory enforcement triggered: {data['conflict_reason']}")
            print(f"   Original: {data['original_answer'][:50]}...")
            print(f"   Corrected: {data['final_answer'][:50]}...")
        else:
            print(f"⚠️  No override (expected for identity question)")
        
        # Verify GNN info
        gnn = data['gnn']
        if gnn.get('available'):
            print(f"✅ GNN scoring available: {gnn.get('gnn_similarity', 0):.3f}")
        else:
            print(f"ℹ️  GNN not available: {gnn.get('reason', 'Unknown')}")
        
        # Verify storage
        if data['memory_stored'].get('stored'):
            print(f"✅ Memory stored: {data['memory_stored'].get('document_id')[:16]}...")
        else:
            print(f"⚠️  Memory not stored")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_general_question():
    """Test that normal questions don't trigger override."""
    print("\n🔍 Testing normal question (no override)...")
    
    payload = {
        "user_message": "Hva er 2+2?",
        "assistant_draft": "2+2 er 4"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/chat/turn",
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ API returned {response.status_code}")
            return False
        
        data = response.json()
        
        if data['was_overridden']:
            print(f"❌ Unexpected override: {data['conflict_reason']}")
            return False
        else:
            print(f"✅ No override (as expected)")
            print(f"   Answer: {data['final_answer']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_debug_endpoint():
    """Test debug endpoint for last turn inspection."""
    print("\n🔍 Testing debug endpoint...")
    
    # First make a debug turn
    payload = {
        "user_message": "Test debug",
        "assistant_draft": "Debug response"
    }
    
    try:
        # Call turn-debug
        response = requests.post(
            f"{API_BASE}/chat/turn-debug",
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ turn-debug returned {response.status_code}")
            return False
        
        print("✅ turn-debug successful")
        
        # Now check debug/last-turn
        debug_response = requests.get(f"{API_BASE}/chat/debug/last-turn", timeout=5)
        
        if debug_response.status_code != 200:
            print(f"❌ debug/last-turn returned {debug_response.status_code}")
            return False
        
        debug_data = debug_response.json()
        
        if debug_data.get('status') != 'ok':
            print(f"❌ Debug data not available")
            return False
        
        print("✅ Debug endpoint working")
        print(f"   Analysis: {json.dumps(debug_data.get('analysis', {}), indent=2)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug test failed: {e}")
        return False


def test_suite_endpoint():
    """Test the built-in test suite."""
    print("\n🔍 Running built-in test suite...")
    
    try:
        response = requests.post(
            f"{API_BASE}/chat/test/known-failures",
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ Test suite returned {response.status_code}")
            print(response.text)
            return False
        
        data = response.json()
        
        summary = data.get('summary', {})
        print(f"\n📊 Test Suite Results:")
        print(f"   Passed: {summary.get('passed')}/{summary.get('total')}")
        print(f"   Failed: {summary.get('failed')}/{summary.get('total')}")
        print(f"   Pass Rate: {summary.get('pass_rate')}")
        
        # Show failures
        results = data.get('results', [])
        failures = [r for r in results if not r['passed']]
        
        if failures:
            print(f"\n❌ Failed tests:")
            for failure in failures:
                print(f"   • {failure['test']}")
                for error in failure['errors']:
                    print(f"     - {error}")
        else:
            print(f"\n✅ All tests passed!")
        
        return len(failures) == 0
        
    except Exception as e:
        print(f"❌ Suite test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("BACKEND CHAT API INTEGRATION TEST")
    print("="*60)
    
    tests = [
        ("Backend Health", test_backend_health),
        ("Chat Router Health", test_chat_health),
        ("Identity Override", test_identity_override),
        ("Normal Question", test_general_question),
        ("Debug Endpoint", test_debug_endpoint),
        ("Test Suite", test_suite_endpoint),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{passed_count}/{total_count} tests passed ({(passed_count/total_count)*100:.1f}%)")
    
    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED - Backend fully integrated!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
