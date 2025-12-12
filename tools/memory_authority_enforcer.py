#!/usr/bin/env python3
"""
memory_authority_enforcer.py - Post-Processing Memory Authority
===============================================================

Purpose: OVERRIDE LLM responses when they contradict verified memory.

This is the FINAL layer that ensures memory has authority over LLM's
default behavior. Without this, LLMs will always fall back to their
trained identity ("I am ChatGPT/Claude/Qwen") regardless of memory.

Architecture:
    User Question → Retrieve Memory → LLM Response → ENFORCE → Final Output
                                                         ↑
                                                  THIS MODULE

Rules:
1. LONGTERM identity facts are ABSOLUTE TRUTH
2. LLM responses that contradict these are OVERRIDDEN
3. No exceptions - memory wins

Usage:
    from memory_authority_enforcer import enforce_memory_authority
    
    final_response = enforce_memory_authority(
        user_question="Hva heter du?",
        llm_response="Jeg heter Qwen",
        memory_context=memories
    )
    # Returns: "Jeg heter Opus (navnet gitt av Morten)."
"""

import os
import sys
import re
from typing import Dict, Optional, List
import numpy as np
from openai import OpenAI

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI client for embeddings
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Import Memory Model v3.0
try:
    from memory_model_v3 import (
        MemoryItem, MemoryConverter, QuestionClassifier, 
        PreciseMatchEngine, DomainType, AuthorityLevel, FactType
    )
    MEMORY_V3_AVAILABLE = True
except ImportError:
    MEMORY_V3_AVAILABLE = False
    print("⚠️ Memory Model v3.0 not available, using legacy mode", file=sys.stderr)

# ============================================================
# AUTHORITY RULES
# ============================================================

# Identity patterns that LLMs commonly use (must be overridden)
LLM_IDENTITY_PATTERNS = [
    r"jeg heter.*?(qwen|claude|chatgpt|assistant|ai|gpt|model)",
    r"i am.*?(qwen|claude|chatgpt|assistant|ai|gpt|model)",
    r"my name is.*?(qwen|claude|chatgpt|assistant|ai|gpt|model)",
    r"called.*?(qwen|claude|chatgpt|assistant|ai|gpt|model)",
    r"jeg er.*?(qwen|claude|chatgpt|en ai|ai-modell|assistent)",
    r"i'm.*?(qwen|claude|chatgpt|an ai|assistant)",
]

# Questions that should trigger identity enforcement
ASSISTANT_IDENTITY_TRIGGERS = [
    "hva heter du", "what's your name", "who are you",
    "what are you called", "hvem er du", "ditt navn",
    "your name", "tell me your name"
]

USER_IDENTITY_TRIGGERS = [
    "hvem er jeg", "who am i", "mitt navn", "my name",
    "hva heter jeg", "what's my name"
]

# Questions about family/relationships (should enforce from memory)
FAMILY_TRIGGERS = [
    "kone", "wife", "mann", "husband", "barn", "children", "child", "kid",
    "mor", "far", "søster", "bror", "mother", "father", "sister", "brother",
    "hvor mange barn", "how many children", "hva heter", "what are the names"
]

# Questions about location (should enforce from memory)
LOCATION_TRIGGERS = [
    "hvor bor", "where do", "bor du", "do you live", "bor jeg", "do i live",
    "hvilken by", "which city", "hvor er", "where are"
]

# ============================================================
# MEMORY EXTRACTION
# ============================================================

def extract_identity_from_memory(memory_context: str, identity_type: str = "assistant") -> Optional[Dict]:
    """
    Extract identity facts from memory context.
    
    Args:
        memory_context: Retrieved memory text
        identity_type: "assistant" or "user"
    
    Returns:
        {
            "name": str,
            "confidence": float,
            "source": str (original memory text)
        }
    """
    if not memory_context:
        return None
    
    memory_lower = memory_context.lower()
    
    if identity_type == "assistant":
        # Look for assistant name (Opus, etc.)
        if "opus" in memory_lower:
            # Find the exact context
            lines = memory_context.split('\n')
            for line in lines:
                if "opus" in line.lower():
                    return {
                        "name": "Opus",
                        "confidence": 1.0,
                        "source": line.strip(),
                        "type": "assistant"
                    }
    
    elif identity_type == "user":
        # Look for user name (Morten, etc.)
        if "morten" in memory_lower:
            lines = memory_context.split('\n')
            for line in lines:
                if "morten" in line.lower():
                    return {
                        "name": "Morten",
                        "confidence": 1.0,
                        "source": line.strip(),
                        "type": "user"
                    }
    
    return None


# ============================================================
# CONFLICT DETECTION
# ============================================================

def detect_identity_conflict(llm_response: str, memory_identity: Dict) -> bool:
    """
    Check if LLM response contradicts memory identity.
    
    Returns True if conflict detected (requires override).
    """
    if not memory_identity:
        return False
    
    response_lower = llm_response.lower()
    memory_name_lower = memory_identity["name"].lower()
    identity_type = memory_identity.get("type", "assistant")
    
    # CRITICAL FIX: If asking about USER identity, response should NOT contain ASSISTANT name
    if identity_type == "user":
        # Common assistant names that shouldn't appear in user identity answers
        assistant_names = ["opus", "qwen", "claude", "chatgpt", "gpt", "assistant"]
        for asst_name in assistant_names:
            if asst_name in response_lower:
                return True  # CONFLICT: LLM confused user with assistant
        
        # Check if response mentions the correct user name
        if memory_name_lower not in response_lower:
            return True  # CONFLICT: LLM doesn't use memory name
    
    # For ASSISTANT identity questions
    if identity_type == "assistant":
        # Check if LLM uses generic identity instead of memory name
        for pattern in LLM_IDENTITY_PATTERNS:
            if re.search(pattern, response_lower, re.IGNORECASE):
                # LLM is using generic identity (Qwen, Assistant, etc.)
                # Check if it mentions the correct memory name
                if memory_name_lower not in response_lower:
                    return True  # CONFLICT: LLM doesn't use memory name
    
    # Check if LLM explicitly says it's NOT the memory name
    denial_patterns = [
        f"not {memory_name_lower}",
        f"isn't {memory_name_lower}",
        f"ikke {memory_name_lower}",
        f"er ikke {memory_name_lower}"
    ]
    
    for pattern in denial_patterns:
        if pattern in response_lower:
            return True  # CONFLICT: LLM denies memory identity
    
    return False


# ============================================================
# QUESTION-ANSWER MATCHING
# ============================================================

def embed_text(text: str) -> np.ndarray:
    """Generate embedding for text using OpenAI."""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return np.array(response.data[0].embedding)


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


def extract_question_type(question: str) -> str:
    """
    Identify question type to validate if memory answers it.
    
    Returns: "count", "name", "location", "yes_no", "general"
    """
    question_lower = question.lower()
    
    # Count questions
    if any(phrase in question_lower for phrase in ["hvor mange", "how many", "antall"]):
        return "count"
    
    # Name questions
    if any(phrase in question_lower for phrase in ["hva heter", "what is the name", "navnet", "kalles"]):
        return "name"
    
    # Location questions
    if any(phrase in question_lower for phrase in ["hvor bor", "where do", "hvilken by", "which city"]):
        return "location"
    
    # Yes/no questions
    if question_lower.startswith(("er ", "is ", "har ", "have ", "kan ", "can ")):
        return "yes_no"
    
    return "general"


def answers_question(question: str, memory_text: str, threshold: float = 0.5) -> bool:
    """
    Check if memory actually answers the question.
    
    Args:
        question: User's question
        memory_text: Memory content (without score/metadata)
        threshold: Minimum similarity for "general" questions
    
    Returns:
        True if memory is a valid answer, False otherwise
    """
    question_type = extract_question_type(question)
    memory_lower = memory_text.lower()
    
    # COUNT questions: must contain numbers
    if question_type == "count":
        has_number = bool(re.search(r'\d+', memory_text))
        if not has_number:
            return False
        
        # Additional check: does it talk about the same subject?
        question_subject = re.search(r'hvor mange\s+(\w+)', question.lower())
        if question_subject:
            subject = question_subject.group(1)  # e.g., "barn"
            if subject not in memory_lower:
                return False
        
        return True
    
    # NAME questions: must contain capitalized names
    elif question_type == "name":
        has_name = bool(re.search(r'\b[A-ZÆØÅ][a-zæøå]+\b', memory_text))
        if not has_name:
            return False
        
        # Check if question is about specific subject
        name_subject_match = re.search(r'hva heter.*?(barn|kone|mann|barna mine|min kone)', question.lower())
        if name_subject_match:
            subject = name_subject_match.group(1)
            # Memory should mention same subject
            if subject not in memory_lower:
                return False
        
        return True
    
    # LOCATION questions: must contain location keywords
    elif question_type == "location":
        location_keywords = ["oslo", "bergen", "trondheim", "stavanger", "london", "paris", 
                            "bor i", "live in", "norway", "norge", "city", "by"]
        if not any(keyword in memory_lower for keyword in location_keywords):
            return False
        return True
    
    # YES/NO questions: semantic similarity check
    elif question_type == "yes_no":
        q_embedding = embed_text(question)
        m_embedding = embed_text(memory_text)
        similarity = cosine_similarity(q_embedding, m_embedding)
        return similarity > threshold
    
    # GENERAL questions: semantic similarity
    else:
        q_embedding = embed_text(question)
        m_embedding = embed_text(memory_text)
        similarity = cosine_similarity(q_embedding, m_embedding)
        return similarity > threshold


# ============================================================
# RESPONSE OVERRIDE
# ============================================================

def override_response(
    user_question: str,
    llm_response: str,
    memory_identity: Dict,
    language: str = "no"
) -> str:
    """
    Override LLM response with memory-based answer.
    
    Args:
        user_question: Original user question
        llm_response: LLM's incorrect response
        memory_identity: Verified identity from memory
        language: "no" (Norwegian) or "en" (English)
    
    Returns:
        Corrected response that enforces memory
    """
    name = memory_identity["name"]
    identity_type = memory_identity["type"]
    
    if identity_type == "assistant":
        if language == "no":
            return f"Jeg heter {name}. 🤖"
        else:
            return f"My name is {name}. 🤖"
    
    elif identity_type == "user":
        if language == "no":
            return f"Du heter {name}. 😊"
        else:
            return f"Your name is {name}. 😊"
    
    return llm_response  # Fallback


def detect_language(text: str) -> str:
    """Simple language detection (Norwegian vs English)."""
    norwegian_words = ["hva", "hvem", "jeg", "du", "heter", "er", "ikke"]
    text_lower = text.lower()
    
    norwegian_count = sum(1 for word in norwegian_words if word in text_lower)
    
    return "no" if norwegian_count >= 2 else "en"


# ============================================================
# MAIN ENFORCER
# ============================================================

def enforce_memory_authority(
    user_question: str,
    llm_response: str,
    memory_context: Optional[str] = None,
    auto_retrieve: bool = True
) -> Dict:
    """
    POST-PROCESS LLM response to enforce memory authority.
    
    This is the FINAL word - if memory contradicts LLM, memory wins.
    
    Now handles:
    - Identity (assistant/user names)
    - Family (spouse, children names/count)
    - Location (where you live/work)
    - ANY factual claim that contradicts LONGTERM memory
    
    Args:
        user_question: User's original question
        llm_response: LLM's generated response
        memory_context: Retrieved memory (if available)
        auto_retrieve: If True and memory_context is None, auto-retrieve
    
    Returns:
        {
            "response": str,           # Final response (possibly overridden)
            "overridden": bool,        # Was LLM response overridden?
            "reason": str,             # Why override happened
            "original_response": str,  # LLM's original response
            "memory_source": str       # Memory fact used for override
        }
    """
    question_lower = user_question.lower().strip()
    response_lower = llm_response.lower()
    
    # CRITICAL: Skip enforcement for simple greetings/social messages
    # These are NOT factual questions and should not trigger memory override
    simple_patterns = [
        "hei", "hi", "hello", "hey", "hallo",
        "takk", "thanks", "thank you", "tusen takk",
        "ok", "okay", "yes", "ja", "nei", "no",
        "bra", "good", "great", "nice",
        "bye", "goodbye", "ha det", "sees"
    ]
    
    # Check if message STARTS WITH any greeting pattern
    if any(question_lower.startswith(pattern) for pattern in simple_patterns):
        # Simple greeting/acknowledgment - no enforcement needed
        return {
            "response": llm_response,
            "overridden": False,
            "reason": "Simple social message - no factual claim to enforce",
            "original_response": llm_response,
            "memory_source": None
        }
    
    # Detect question type
    is_assistant_identity = any(trigger in question_lower for trigger in ASSISTANT_IDENTITY_TRIGGERS)
    is_user_identity = any(trigger in question_lower for trigger in USER_IDENTITY_TRIGGERS)
    is_family_question = any(trigger in question_lower for trigger in FAMILY_TRIGGERS)
    is_location_question = any(trigger in question_lower for trigger in LOCATION_TRIGGERS)
    
    # Auto-retrieve memory if not provided
    if memory_context is None and auto_retrieve:
        try:
            from chat_memory import retrieve_relevant_memory
            
            if is_assistant_identity:
                memory_context = retrieve_relevant_memory("assistant navn Opus AI name jeg kaller deg", k=5)
            elif is_user_identity:
                memory_context = retrieve_relevant_memory("user navn identity Morten jeg heter", k=5)
            elif is_family_question:
                memory_context = retrieve_relevant_memory(user_question + " barn kone family", k=10)
            elif is_location_question:
                memory_context = retrieve_relevant_memory(user_question + " bor location Oslo", k=5)
            else:
                # General retrieval for any other factual question
                memory_context = retrieve_relevant_memory(user_question, k=10, memory_class_filter="LONGTERM")
        except Exception as e:
            print(f"⚠️ Auto-retrieve failed: {e}", file=sys.stderr)
            memory_context = None
    
    if not memory_context:
        # No memory available - can't enforce
        return {
            "response": llm_response,
            "overridden": False,
            "reason": "No memory available",
            "original_response": llm_response,
            "memory_source": None
        }
    
    # Check for contradictions based on question type
    if is_assistant_identity or is_user_identity:
        # Use existing identity enforcement logic
        identity_type = "assistant" if is_assistant_identity else "user"
        memory_identity = extract_identity_from_memory(memory_context, identity_type)
        
        if not memory_identity:
            return {
                "response": llm_response,
                "overridden": False,
                "reason": "No memory available for this identity",
                "original_response": llm_response,
                "memory_source": None
            }
        
        has_conflict = detect_identity_conflict(llm_response, memory_identity)
        
        if not has_conflict:
            return {
                "response": llm_response,
                "overridden": False,
                "reason": "LLM response matches memory",
                "original_response": llm_response,
                "memory_source": memory_identity["source"]
            }
        
        # OVERRIDE: Memory contradicts LLM
        language = detect_language(user_question)
        corrected_response = override_response(
            user_question,
            llm_response,
            memory_identity,
            language
        )
        
        return {
            "response": corrected_response,
            "overridden": True,
            "reason": f"LLM identity contradiction - memory says '{memory_identity['name']}'",
            "original_response": llm_response,
            "memory_source": memory_identity["source"]
        }
    
    # For non-identity questions: check if ANY memory fact contradicts response
    elif is_family_question or is_location_question or True:  # Always check facts
        # Extract numbers from response (for counting questions like "hvor mange barn")
        response_numbers = re.findall(r'\d+', llm_response)
        memory_numbers = re.findall(r'\d+', memory_context)
        
        # Extract names from response
        response_names = re.findall(r'\b[A-ZÆØÅ][a-zæøå]+\b', llm_response)
        
        # Check if response contradicts memory
        contradiction_found = False
        memory_fact = None
        
        # Check numbers (e.g., "2 barn" vs "3 barn")
        if response_numbers and memory_numbers:
            if response_numbers[0] != memory_numbers[0]:
                # Numbers differ - find the memory line with correct number
                for line in memory_context.split('\n'):
                    if '[LONGTERM' in line and memory_numbers[0] in line:
                        memory_fact = line
                        contradiction_found = True
                        break
        
        # Check names (e.g., response says "Emma" but memory has "Joakim")
        if response_names and not contradiction_found:
            memory_lines = [l for l in memory_context.split('\n') if '[LONGTERM' in l]
            for name in response_names:
                # Check if this name is contradicted by memory
                name_in_memory = any(name in line for line in memory_lines)
                if not name_in_memory and len(memory_lines) > 0:
                    # Response mentions a name not in memory - potential error
                    memory_fact = memory_lines[0]  # Use first relevant memory
                    contradiction_found = True
                    break
        
        # Check if response is too vague when memory has specifics
        if "vet ikke" in response_lower or "don't know" in response_lower:
            if memory_context and '[LONGTERM' in memory_context:
                # LLM doesn't know, but memory might have the answer
                memory_lines = [l for l in memory_context.split('\n') if '[LONGTERM' in l]
                
                # Find the MOST RELEVANT memory that ACTUALLY ANSWERS the question
                best_memory = None
                best_score = 0.0
                
                for line in memory_lines:
                    # Extract score from line like "[LONGTERM, score: 0.45]"
                    score_match = re.search(r'score:\s*([\d\.]+)', line)
                    fact_match = re.search(r'\[LONGTERM[^\]]+\]\s*(.+)', line)
                    
                    if score_match and fact_match:
                        score = float(score_match.group(1))
                        clean_fact = fact_match.group(1).strip()
                        
                        # CRITICAL: Check if this memory ANSWERS the question
                        # Not just "related" but actually provides the answer
                        if score > 0.35 and answers_question(user_question, clean_fact):
                            if score > best_score:
                                best_memory = line
                                best_score = score
                
                # Only override if we found a memory that ANSWERS the question
                if best_memory:
                    memory_fact = best_memory
                    contradiction_found = True
                    print(f"✅ Found answering memory (score: {best_score:.2f})", file=sys.stderr)
                else:
                    # No memory actually answers this question - accept "vet ikke"
                    print(f"⚠️ No memory answers '{user_question}' - keeping 'vet ikke'", file=sys.stderr)
                    pass
        
        if contradiction_found and memory_fact:
            # Extract clean fact from memory line
            fact_match = re.search(r'\[LONGTERM[^\]]+\]\s*(.+)', memory_fact)
            if fact_match:
                clean_fact = fact_match.group(1).strip()
                
                language = detect_language(user_question)
                if language == "no":
                    corrected = f"{clean_fact}"
                else:
                    corrected = f"{clean_fact}"
                
                return {
                    "response": corrected,
                    "overridden": True,
                    "reason": "LLM response contradicts LONGTERM memory",
                    "original_response": llm_response,
                    "memory_source": memory_fact
                }
        
        # No contradiction found
        return {
            "response": llm_response,
            "overridden": False,
            "reason": "No contradiction detected",
            "original_response": llm_response,
            "memory_source": None
        }
    
    # Default: no enforcement
    return {
        "response": llm_response,
        "overridden": False,
        "reason": "Not an enforceable question type",
        "original_response": llm_response,
        "memory_source": None
    }


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":
    # Test cases
    test_cases = [
        {
            "question": "Hva heter du?",
            "llm_response": "Jeg heter Qwen, en AI-assistent.",
            "memory": "Du har gitt meg navnet Opus",
            "expected_override": True
        },
        {
            "question": "Who are you?",
            "llm_response": "I am ChatGPT, an AI assistant.",
            "memory": "User calls me Opus",
            "expected_override": True
        },
        {
            "question": "Hvem er jeg?",
            "llm_response": "Jeg vet ikke helt hvem du er.",
            "memory": "Brukeren heter Morten",
            "expected_override": False  # LLM doesn't contradict, just doesn't know
        },
        {
            "question": "Hva er entropi?",
            "llm_response": "Entropi er et mål på uorden i et system.",
            "memory": "User name is Morten",
            "expected_override": False  # Not an identity question
        }
    ]
    
    print("🧪 Testing Memory Authority Enforcer\n")
    print("=" * 60)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['question']}")
        print(f"   LLM: {test['llm_response'][:50]}...")
        
        result = enforce_memory_authority(
            user_question=test["question"],
            llm_response=test["llm_response"],
            memory_context=test["memory"],
            auto_retrieve=False
        )
        
        print(f"   Overridden: {result['overridden']}")
        if result['overridden']:
            print(f"   Corrected: {result['response']}")
            print(f"   Reason: {result['reason']}")
        else:
            print(f"   Reason: {result['reason']}")
        
        expected = test["expected_override"]
        actual = result["overridden"]
        status = "✅" if expected == actual else "❌"
        print(f"   {status} Expected override={expected}, got={actual}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete\n")
