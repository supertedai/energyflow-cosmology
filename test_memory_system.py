#!/usr/bin/env python3
"""
Quick test of Symbiosis Memory System
Tests all personal facts via API
"""

import requests
import json

API_URL = "http://localhost:8000"

def test_memory(question: str):
    """Test a single question against memory."""
    response = requests.post(
        f"{API_URL}/chat/turn",
        json={
            "user_message": question,
            "assistant_draft": "Jeg vet ikke"
        },
        timeout=15
    )
    
    data = response.json()
    return {
        "question": question,
        "answer": data.get("final_answer", "ERROR"),
        "overridden": data.get("was_overridden", False),
        "facts_used": data.get("memory", {}).get("canonical_facts", 0)
    }

def main():
    print("🧪 Testing Symbiosis Memory System")
    print("=" * 60)
    print()
    
    # Check if API is running
    try:
        requests.get(f"{API_URL}/health", timeout=2)
        print("✅ API is running")
    except:
        print("❌ API not running on port 8000")
        print("   Run: ./start_memory_system.sh")
        return
    
    print()
    
    # Test questions
    questions = [
        "Hva heter jeg?",
        "Hvem er jeg gift med?",
        "Hva heter barna mine?",
        "Hvor mange barn har jeg?",
        "Hva heter AI-assistenten?"
    ]
    
    results = []
    for q in questions:
        print(f"Testing: {q}")
        try:
            result = test_memory(q)
            results.append(result)
            
            status = "✅" if result["overridden"] else "⚠️"
            print(f"  {status} {result['answer'][:80]}")
            print(f"     Facts used: {result['facts_used']}")
            print()
        except Exception as e:
            print(f"  ❌ Error: {e}")
            print()
    
    print("=" * 60)
    print("📊 Summary:")
    print(f"   Total tests: {len(results)}")
    print(f"   Overridden: {sum(1 for r in results if r['overridden'])}")
    print(f"   Average facts used: {sum(r['facts_used'] for r in results) / len(results):.1f}")
    print()
    
    # Check expected answers
    expected = {
        "Hva heter jeg?": "Morten",
        "Hvem er jeg gift med?": "Elisabet",
        "Hva heter barna mine?": ["Joakim", "Isak Andreas", "Susanna"],
        "Hvor mange barn har jeg?": "3",
        "Hva heter AI-assistenten?": "Opus"
    }
    
    print("🎯 Validation:")
    for result in results:
        q = result["question"]
        answer = result["answer"]
        
        if q in expected:
            exp = expected[q]
            if isinstance(exp, list):
                # Check if all names are in answer
                if all(name in answer for name in exp):
                    print(f"  ✅ {q}")
                else:
                    print(f"  ❌ {q} - Missing names")
            else:
                if exp in answer:
                    print(f"  ✅ {q}")
                else:
                    print(f"  ❌ {q} - Expected '{exp}'")
    
    print()
    print("✅ All tests complete!")

if __name__ == "__main__":
    main()
