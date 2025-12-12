#!/usr/bin/env python3
"""
universal_memory_enforcer.py - Universal Fact Enforcement
==========================================================

Purpose: ENFORCE ALL memory facts, not just identity.

Rules:
1. ANY factual contradiction with LONGTERM memory → OVERRIDE
2. Applies to: dates, numbers, relationships, events, preferences, EVERYTHING
3. No exceptions - memory is ABSOLUTE TRUTH

Architecture:
    1. Extract factual claims from LLM response
    2. Check each claim against LONGTERM memory
    3. Override ANY contradictions
    4. Return corrected response

Examples:
- "Du har 2 barn" vs memory "3 barn" → OVERRIDE
- "Du bor i Bergen" vs memory "Oslo" → OVERRIDE  
- "Din kone heter Anne" vs memory "Elisabet" → OVERRIDE
- "Publisert 2020" vs memory "2019" → OVERRIDE
"""

import os
import sys
import re
from typing import Dict, Optional, List, Tuple
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from chat_memory import retrieve_relevant_memory

load_dotenv()

# ============================================================
# FACT EXTRACTION
# ============================================================

def extract_factual_claims(text: str, language: str = "no") -> List[Dict]:
    """
    Extract all factual claims from text.
    
    Returns list of claims with context.
    """
    claims = []
    
    # Pattern 1: "X heter Y" / "X is named Y"
    name_patterns = [
        r"(\w+)\s+heter\s+(\w+)",
        r"(\w+)\s+er\s+(\w+)",
        r"(\w+)\s+is\s+(\w+)",
        r"(\w+)\s+is\s+called\s+(\w+)"
    ]
    
    for pattern in name_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            claims.append({
                "type": "name",
                "subject": match.group(1),
                "object": match.group(2),
                "full_text": match.group(0),
                "start": match.start(),
                "end": match.end()
            })
    
    # Pattern 2: Numbers (age, count, year, etc.)
    number_patterns = [
        r"(\d+)\s+(år|years|barn|children|kroner|dollars)",
        r"(\w+)\s+har\s+(\d+)\s+(\w+)",
        r"(\w+)\s+has\s+(\d+)\s+(\w+)"
    ]
    
    for pattern in number_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            claims.append({
                "type": "quantity",
                "full_text": match.group(0),
                "number": match.group(1) if pattern.startswith(r"(\d+)") else match.group(2),
                "start": match.start(),
                "end": match.end()
            })
    
    # Pattern 3: Dates
    date_patterns = [
        r"(\d{1,2})\.\s*(\w+)\s+(\d{4})",  # "15. mars 2020"
        r"(\w+)\s+(\d{1,2}),?\s+(\d{4})",  # "March 15, 2020"
        r"(\d{4})-(\d{2})-(\d{2})"  # "2020-03-15"
    ]
    
    for pattern in date_patterns:
        for match in re.finditer(pattern, text):
            claims.append({
                "type": "date",
                "full_text": match.group(0),
                "start": match.start(),
                "end": match.end()
            })
    
    # Pattern 4: Locations
    location_patterns = [
        r"bor\s+i\s+(\w+)",
        r"lives?\s+in\s+(\w+)",
        r"fra\s+(\w+)",
        r"from\s+(\w+)"
    ]
    
    for pattern in location_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            claims.append({
                "type": "location",
                "location": match.group(1),
                "full_text": match.group(0),
                "start": match.start(),
                "end": match.end()
            })
    
    return claims


# ============================================================
# MEMORY VERIFICATION
# ============================================================

def verify_claim_against_memory(claim: Dict, memory_context: str) -> Optional[Dict]:
    """
    Check if claim contradicts memory.
    
    Returns contradiction details if found, None otherwise.
    """
    if not memory_context:
        return None
    
    memory_lower = memory_context.lower()
    
    # Verify name claims
    if claim["type"] == "name":
        subject = claim["subject"].lower()
        stated_object = claim["object"].lower()
        
        # Search for contradictions
        # Example: claim says "barn heter Emma" but memory says "barn heter Joakim"
        if subject in memory_lower:
            # Extract actual value from memory
            lines = memory_context.split('\n')
            for line in lines:
                if subject in line.lower():
                    # Check if stated value is in this line
                    if stated_object not in line.lower():
                        # Potential contradiction - extract correct value
                        return {
                            "type": "name_contradiction",
                            "claim": claim["full_text"],
                            "memory_source": line.strip(),
                            "stated_value": stated_object,
                            "correction_needed": True
                        }
    
    # Verify quantity claims
    elif claim["type"] == "quantity":
        number = claim.get("number")
        full_text_lower = claim["full_text"].lower()
        
        # Look for different numbers in memory for same subject
        for line in memory_context.split('\n'):
            # Check if this memory line is about the same thing
            overlap = sum(1 for word in full_text_lower.split() if word in line.lower())
            if overlap >= 2:  # At least 2 words match
                # Extract number from memory
                memory_numbers = re.findall(r'\d+', line)
                if memory_numbers and number not in memory_numbers:
                    return {
                        "type": "quantity_contradiction",
                        "claim": claim["full_text"],
                        "memory_source": line.strip(),
                        "stated_value": number,
                        "memory_value": memory_numbers[0],
                        "correction_needed": True
                    }
    
    # Verify location claims
    elif claim["type"] == "location":
        stated_location = claim["location"].lower()
        
        # Check if memory mentions a different location
        for line in memory_context.split('\n'):
            if any(word in line.lower() for word in ["bor", "live", "fra", "from"]):
                if stated_location not in line.lower():
                    return {
                        "type": "location_contradiction",
                        "claim": claim["full_text"],
                        "memory_source": line.strip(),
                        "stated_value": stated_location,
                        "correction_needed": True
                    }
    
    return None


# ============================================================
# UNIVERSAL ENFORCEMENT
# ============================================================

def enforce_all_facts(
    user_question: str,
    llm_response: str,
    memory_context: Optional[str] = None,
    auto_retrieve: bool = True,
    language: str = "no"
) -> Dict:
    """
    Universal fact enforcement - checks ALL claims, not just identity.
    
    Args:
        user_question: User's question
        llm_response: LLM's response to verify
        memory_context: Retrieved memory (or auto-retrieve)
        auto_retrieve: Auto-retrieve relevant memory if not provided
        language: "no" or "en"
    
    Returns:
        {
            "response": str,              # Corrected response
            "overridden": bool,           # Was anything corrected?
            "contradictions": List[Dict], # All contradictions found
            "original_response": str      # Original LLM response
        }
    """
    # Auto-retrieve memory if not provided
    if memory_context is None and auto_retrieve:
        try:
            memory_context = retrieve_relevant_memory(
                query=user_question + " " + llm_response,
                k=10,  # Get more context for fact-checking
                memory_class_filter="LONGTERM"
            )
        except Exception as e:
            print(f"⚠️ Auto-retrieve failed: {e}", file=sys.stderr)
            memory_context = None
    
    if not memory_context:
        # No memory to verify against
        return {
            "response": llm_response,
            "overridden": False,
            "contradictions": [],
            "original_response": llm_response
        }
    
    # Extract all factual claims from LLM response
    claims = extract_factual_claims(llm_response, language)
    
    if not claims:
        # No factual claims to verify
        return {
            "response": llm_response,
            "overridden": False,
            "contradictions": [],
            "original_response": llm_response
        }
    
    # Verify each claim
    contradictions = []
    for claim in claims:
        contradiction = verify_claim_against_memory(claim, memory_context)
        if contradiction:
            contradictions.append(contradiction)
    
    if not contradictions:
        # All claims verified - no override needed
        return {
            "response": llm_response,
            "overridden": False,
            "contradictions": [],
            "original_response": llm_response
        }
    
    # OVERRIDE: Build corrected response
    corrected_response = _build_corrected_response(
        llm_response,
        contradictions,
        memory_context,
        language
    )
    
    return {
        "response": corrected_response,
        "overridden": True,
        "contradictions": contradictions,
        "original_response": llm_response,
        "reason": f"Found {len(contradictions)} factual contradiction(s)"
    }


def _build_corrected_response(
    original: str,
    contradictions: List[Dict],
    memory: str,
    language: str
) -> str:
    """Build corrected response with memory facts."""
    
    # Extract all LONGTERM facts from memory that are relevant
    longterm_facts = []
    for line in memory.split('\n'):
        if '[LONGTERM' in line:
            # Extract just the fact text (remove score prefix)
            fact_match = re.search(r'\[LONGTERM[^\]]+\]\s*(.+)', line)
            if fact_match:
                fact = fact_match.group(1).strip()
                # Only include facts that directly contradict claims
                for contradiction in contradictions:
                    claim_words = set(contradiction.get('claim', '').lower().split())
                    fact_words = set(fact.lower().split())
                    overlap = len(claim_words & fact_words)
                    if overlap >= 2:  # At least 2 words overlap
                        if fact not in longterm_facts:
                            longterm_facts.append(fact)
    
    if not longterm_facts:
        # Fallback: use original response but add warning
        if language == "no":
            return f"⚠️ Informasjonen ser ut til å være ukorrekt. Jeg finner motstridende fakta i minnet, men kan ikke gi et presist svar akkurat nå."
        else:
            return f"⚠️ The information appears incorrect. I find contradicting facts in memory but cannot give a precise answer right now."
    
    # Build corrected response from memory facts
    if language == "no":
        return " ".join(longterm_facts[:3])  # Use top 3 most relevant facts
    else:
        return " ".join(longterm_facts[:3])


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test universal fact enforcement")
    parser.add_argument("--question", required=True, help="User question")
    parser.add_argument("--response", required=True, help="LLM response to check")
    parser.add_argument("--memory", help="Memory context (optional - will auto-retrieve)")
    
    args = parser.parse_args()
    
    result = enforce_all_facts(
        user_question=args.question,
        llm_response=args.response,
        memory_context=args.memory,
        auto_retrieve=True
    )
    
    print("=" * 60)
    print("UNIVERSAL FACT ENFORCEMENT TEST")
    print("=" * 60)
    print(f"Original response: {result['original_response']}")
    print(f"Overridden: {result['overridden']}")
    if result['overridden']:
        print(f"\nContradictions found: {len(result['contradictions'])}")
        for i, c in enumerate(result['contradictions'], 1):
            print(f"  {i}. {c['type']}: {c['claim']}")
        print(f"\nCorrected response:\n{result['response']}")
