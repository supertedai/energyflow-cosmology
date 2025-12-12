#!/usr/bin/env python3
"""
memory_model_v3.py - Structured Memory Model with Domain Authority
==================================================================

Purpose: Replace raw text memory with structured, domain-aware, 
         authority-ranked memory items for ULTRAPRECISE recall.

Architecture:
    Question → Classify → Route to Domain → Filter by Authority → 
    Match Fact Type → Validate Answer → Return with Confidence

Core Concepts:
    1. Memory Item = structured object (not raw text)
    2. Domain = semantic category (identity, family, health, cosmology, etc.)
    3. Authority = LONGTERM > stable > short-term > volatile
    4. Fact Type = what kind of answer (name, count, location, definition, etc.)
    5. Precise Matching = semantic + structural validation

Rules:
    - LONGTERM facts NEVER change (identity, family, critical facts)
    - Stable facts change rarely (architecture, definitions, models)
    - Short-term facts are conversational context
    - Volatile facts are runtime data (network status, measurements)
    - Memory can only override if: same domain + higher authority + answers question
"""

import os
import sys
import re
import json
import uuid
from typing import Dict, List, Optional, Literal, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import numpy as np
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dotenv import load_dotenv

load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

# ============================================================
# TYPE DEFINITIONS
# ============================================================

# Authority levels (higher = more trusted)
AuthorityLevel = Literal["LONGTERM", "stable", "short-term", "volatile"]
AUTHORITY_RANK = {"LONGTERM": 4, "stable": 3, "short-term": 2, "volatile": 1}

# Domains (semantic categories)
Domain = Literal[
    "identity",      # Names, roles, self-reference
    "family",        # Relationships, children, spouse
    "location",      # Where someone lives/works
    "health",        # Symptoms, conditions, routines
    "symbiosis",     # Architecture, rules, system behavior
    "cosmology",     # EFC, models, theories
    "security",      # Network, firewall, access
    "operational",   # Commands, config, runtime
    "preferences",   # Likes, dislikes, habits
    "general"        # Fallback for uncategorized
]

# Fact types (what kind of answer)
FactType = Literal[
    "name",          # Person/place/thing names
    "count",         # How many (numbers)
    "location",      # Where (places)
    "definition",    # What is X
    "relationship",  # Who is related to whom
    "time",          # When (dates, times)
    "boolean",       # Yes/no facts
    "process",       # How to do X
    "description",   # General description
    "rule"           # System rules/constraints
]


@dataclass
class MemoryItem:
    """Structured memory representation - replaces raw text."""
    
    # Core identification
    id: str                          # Unique identifier
    domain: Domain                   # Which semantic domain
    authority: AuthorityLevel        # Trust level
    fact_type: FactType             # What kind of fact
    
    # Content
    fact: str                        # Human-readable fact
    value: Any                       # Extracted value (name, number, etc.)
    embedding: Optional[List[float]] # Semantic vector
    
    # Metadata
    source: str                      # Where this came from
    timestamp: str                   # When stored
    session_id: Optional[str]        # Related session
    confidence: float                # How certain (0-1)
    
    # Context
    related_to: List[str]            # Related memory IDs
    tags: List[str]                  # Additional categorization
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict) -> 'MemoryItem':
        """Restore from dictionary."""
        return MemoryItem(**data)


# ============================================================
# DOMAIN ROUTING
# ============================================================

# Domain classification rules
DOMAIN_PATTERNS = {
    "identity": [
        r"hva heter (du|jeg|vi|han|hun)",
        r"who (are|am|is) (you|i|we)",
        r"what('s| is) your name",
        r"mitt navn",
        r"ditt navn",
        r"jeg er",
        r"du er",
        r"i am",
        r"you are"
    ],
    "family": [
        r"barn",
        r"children",
        r"kone",
        r"mann",
        r"wife",
        r"husband",
        r"søster",
        r"bror",
        r"sister",
        r"brother",
        r"mor",
        r"far",
        r"mother",
        r"father",
        r"familie",
        r"family"
    ],
    "location": [
        r"hvor bor",
        r"where do.*live",
        r"hvilken by",
        r"which city",
        r"bor i",
        r"live in",
        r"oslo",
        r"bergen",
        r"adresse",
        r"address"
    ],
    "health": [
        r"symptom",
        r"syk",
        r"ill",
        r"medisin",
        r"medicine",
        r"diagnosis",
        r"behandling",
        r"treatment",
        r"helse",
        r"health"
    ],
    "symbiosis": [
        r"symbiose",
        r"symbiosis",
        r"minne",
        r"memory",
        r"router",
        r"enforcer",
        r"arkitektur",
        r"architecture",
        r"mcp",
        r"backend"
    ],
    "cosmology": [
        r"efc",
        r"energy.flow",
        r"kosmologi",
        r"cosmology",
        r"hubble",
        r"entropi",
        r"entropy",
        r"univers",
        r"universe"
    ],
    "security": [
        r"firewall",
        r"nettverk",
        r"network",
        r"sikkerhet",
        r"security",
        r"port",
        r"ip",
        r"access",
        r"tilgang"
    ],
    "operational": [
        r"kommando",
        r"command",
        r"kjør",
        r"run",
        r"start",
        r"stopp",
        r"config",
        r"innstilling",
        r"setting"
    ],
    "preferences": [
        r"liker",
        r"like",
        r"favoritt",
        r"favorite",
        r"prefer",
        r"foretrekke",
        r"hater",
        r"hate"
    ]
}

# Fact type classification rules
FACT_TYPE_PATTERNS = {
    "name": [
        r"hva heter",
        r"what.*name",
        r"who is",
        r"hvem er",
        r"kalles",
        r"called"
    ],
    "count": [
        r"hvor mange",
        r"how many",
        r"antall",
        r"number of",
        r"\d+"
    ],
    "location": [
        r"hvor",
        r"where",
        r"hvilken by",
        r"which city",
        r"bor"
    ],
    "definition": [
        r"hva er",
        r"what is",
        r"definer",
        r"define",
        r"forklar",
        r"explain"
    ],
    "relationship": [
        r"relatert til",
        r"related to",
        r"forbindelse",
        r"connection",
        r"familie",
        r"family"
    ],
    "time": [
        r"når",
        r"when",
        r"dato",
        r"date",
        r"tid",
        r"time",
        r"år",
        r"year"
    ],
    "boolean": [
        r"^er ",
        r"^is ",
        r"^har ",
        r"^have ",
        r"^kan ",
        r"^can "
    ],
    "process": [
        r"hvordan",
        r"how to",
        r"prosess",
        r"process",
        r"steg",
        r"step"
    ],
    "rule": [
        r"regel",
        r"rule",
        r"må",
        r"must",
        r"aldri",
        r"never",
        r"alltid",
        r"always"
    ]
}


def classify_domain(text: str) -> Domain:
    """
    Classify which domain a question/fact belongs to.
    
    Args:
        text: Question or fact text
    
    Returns:
        Domain category
    """
    text_lower = text.lower()
    
    for domain, patterns in DOMAIN_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return domain  # type: ignore
    
    return "general"


def classify_fact_type(text: str) -> FactType:
    """
    Classify what kind of fact/answer is needed.
    
    Args:
        text: Question or fact text
    
    Returns:
        Fact type
    """
    text_lower = text.lower()
    
    for fact_type, patterns in FACT_TYPE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return fact_type  # type: ignore
    
    return "description"


# ============================================================
# VALUE EXTRACTION
# ============================================================

def extract_value(fact: str, fact_type: FactType) -> Any:
    """
    Extract structured value from fact text.
    
    Args:
        fact: Fact text
        fact_type: What kind of value to extract
    
    Returns:
        Extracted value (str, int, bool, etc.)
    """
    if fact_type == "name":
        # Extract capitalized names
        names = re.findall(r'\b[A-ZÆØÅ][a-zæøå]+\b', fact)
        return names[0] if names else None
    
    elif fact_type == "count":
        # Extract numbers
        numbers = re.findall(r'\d+', fact)
        return int(numbers[0]) if numbers else None
    
    elif fact_type == "location":
        # Extract location names (capitalized)
        locations = re.findall(r'\b[A-ZÆØÅ][a-zæøå]+\b', fact)
        return locations[0] if locations else None
    
    elif fact_type == "boolean":
        # Extract yes/no
        if any(word in fact.lower() for word in ["ja", "yes", "true", "sant"]):
            return True
        elif any(word in fact.lower() for word in ["nei", "no", "false", "usant"]):
            return False
        return None
    
    elif fact_type == "time":
        # Extract dates/times (simplified)
        year_match = re.search(r'\b(19|20)\d{2}\b', fact)
        if year_match:
            return year_match.group(0)
        return None
    
    # For other types, return the fact itself
    return fact


# ============================================================
# MEMORY STORAGE
# ============================================================

def store_memory_item(
    fact: str,
    domain: Domain,
    authority: AuthorityLevel,
    fact_type: FactType,
    source: str = "user",
    session_id: Optional[str] = None,
    confidence: float = 1.0,
    tags: Optional[List[str]] = None
) -> MemoryItem:
    """
    Store a structured memory item in Qdrant.
    
    Args:
        fact: Human-readable fact
        domain: Which domain this belongs to
        authority: Trust level
        fact_type: What kind of fact
        source: Where this came from
        session_id: Related session
        confidence: How certain (0-1)
        tags: Additional categorization
    
    Returns:
        Stored MemoryItem
    """
    # Generate embedding
    embedding_response = openai_client.embeddings.create(
        model="text-embedding-3-large",  # Match collection size (3072)
        input=fact
    )
    embedding = embedding_response.data[0].embedding
    
    # Extract structured value
    value = extract_value(fact, fact_type)
    
    # Generate UUID for Qdrant
    memory_id = str(uuid.uuid4())
    
    # Create memory item
    memory = MemoryItem(
        id=memory_id,
        domain=domain,
        authority=authority,
        fact_type=fact_type,
        fact=fact,
        value=value,
        embedding=embedding,
        source=source,
        timestamp=datetime.now().isoformat(),
        session_id=session_id,
        confidence=confidence,
        related_to=[],
        tags=tags or []
    )
    
    # Store in Qdrant
    point = PointStruct(
        id=memory.id,
        vector=embedding,
        payload={
            "domain": domain,
            "authority": authority,
            "fact_type": fact_type,
            "fact": fact,
            "value": value,
            "source": source,
            "timestamp": memory.timestamp,
            "session_id": session_id,
            "confidence": confidence,
            "tags": tags or []
        }
    )
    
    qdrant_client.upsert(
        collection_name="efc",
        points=[point]
    )
    
    return memory


# ============================================================
# PRECISE MEMORY RETRIEVAL
# ============================================================

def retrieve_precise_memory(
    question: str,
    domain: Optional[Domain] = None,
    fact_type: Optional[FactType] = None,
    authority_min: Optional[AuthorityLevel] = None,
    k: int = 5
) -> List[MemoryItem]:
    """
    Retrieve memories with ULTRAPRECISE filtering.
    
    Args:
        question: User's question
        domain: Filter by domain (auto-classify if None)
        fact_type: Filter by fact type (auto-classify if None)
        authority_min: Minimum authority level
        k: Max results
    
    Returns:
        List of matching MemoryItems, ranked by relevance
    """
    # Auto-classify if needed
    if domain is None:
        domain = classify_domain(question)
    if fact_type is None:
        fact_type = classify_fact_type(question)
    
    # Generate query embedding
    embedding_response = openai_client.embeddings.create(
        model="text-embedding-3-large",  # Match collection size (3072)
        input=question
    )
    query_embedding = embedding_response.data[0].embedding
    
    # Build filter
    must_conditions = [
        {"key": "domain", "match": {"value": domain}}
    ]
    
    if fact_type:
        must_conditions.append(
            {"key": "fact_type", "match": {"value": fact_type}}
        )
    
    if authority_min:
        # Filter by authority rank
        min_rank = AUTHORITY_RANK[authority_min]
        allowed_authorities = [
            auth for auth, rank in AUTHORITY_RANK.items() 
            if rank >= min_rank
        ]
        must_conditions.append(
            {"key": "authority", "match": {"any": allowed_authorities}}
        )
    
    # Search Qdrant
    results = qdrant_client.search(
        collection_name="efc",
        query_vector=query_embedding,
        query_filter={"must": must_conditions} if must_conditions else None,
        limit=k
    )
    
    # Convert to MemoryItems
    memories = []
    for hit in results:
        memory = MemoryItem(
            id=hit.id,
            domain=hit.payload["domain"],
            authority=hit.payload["authority"],
            fact_type=hit.payload["fact_type"],
            fact=hit.payload["fact"],
            value=hit.payload["value"],
            embedding=None,  # Don't load full embedding
            source=hit.payload["source"],
            timestamp=hit.payload["timestamp"],
            session_id=hit.payload.get("session_id"),
            confidence=hit.payload["confidence"],
            related_to=[],
            tags=hit.payload.get("tags", [])
        )
        memories.append(memory)
    
    return memories


# ============================================================
# ANSWER VALIDATION
# ============================================================

def validates_answer(question: str, memory: MemoryItem, threshold: float = 0.6) -> bool:
    """
    Check if memory actually answers the question.
    
    More strict than similarity - checks structural alignment.
    
    Args:
        question: User's question
        memory: Retrieved memory
        threshold: Confidence threshold
    
    Returns:
        True if memory is a valid answer
    """
    question_lower = question.lower()
    fact_lower = memory.fact.lower()
    
    # COUNT questions: must contain matching subject + number
    if memory.fact_type == "count":
        # Extract subject from question
        subject_match = re.search(r'hvor mange\s+(\w+)', question_lower)
        if subject_match:
            subject = subject_match.group(1)
            # Memory must mention subject AND have a number
            if subject not in fact_lower or memory.value is None:
                return False
        return isinstance(memory.value, int)
    
    # NAME questions: must contain name for correct subject
    elif memory.fact_type == "name":
        # Check if question asks about specific subject
        subject_patterns = [
            (r'hva heter (du|jeg)', ["du", "jeg"]),
            (r'hva heter.*?(barn|kone|mann)', ["barn", "kone", "mann"]),
            (r'who is', ["name"])
        ]
        
        for pattern, subjects in subject_patterns:
            match = re.search(pattern, question_lower)
            if match:
                # Memory must mention same subject
                if not any(subj in fact_lower for subj in subjects):
                    return False
        
        return memory.value is not None
    
    # LOCATION questions: must contain location
    elif memory.fact_type == "location":
        location_words = ["oslo", "bergen", "london", "bor i", "live in", "city", "by"]
        return any(word in fact_lower for word in location_words)
    
    # BOOLEAN questions: must be yes/no
    elif memory.fact_type == "boolean":
        return isinstance(memory.value, bool)
    
    # For other types: semantic check
    else:
        # Basic semantic alignment
        question_words = set(re.findall(r'\w+', question_lower))
        fact_words = set(re.findall(r'\w+', fact_lower))
        overlap = len(question_words & fact_words) / len(question_words)
        return overlap > threshold


# ============================================================
# ULTRAPRECISE MEMORY ENFORCEMENT
# ============================================================

def enforce_with_structured_memory(
    question: str,
    llm_response: str,
    auto_retrieve: bool = True
) -> Dict:
    """
    Enforce memory authority using structured memory model.
    
    This replaces the old text-based enforcement with:
    - Domain routing
    - Authority ranking
    - Fact type validation
    - Structural answer checking
    
    Args:
        question: User's question
        llm_response: LLM's draft response
        auto_retrieve: Whether to retrieve memories automatically
    
    Returns:
        {
            "response": str,          # Final response (possibly overridden)
            "overridden": bool,       # Was LLM response overridden?
            "reason": str,            # Why/why not
            "memory_used": MemoryItem # Memory that provided the answer
        }
    """
    # Classify question
    domain = classify_domain(question)
    fact_type = classify_fact_type(question)
    
    # Retrieve precise memories
    memories = retrieve_precise_memory(
        question=question,
        domain=domain,
        fact_type=fact_type,
        authority_min="short-term",  # At least short-term
        k=10
    )
    
    if not memories:
        return {
            "response": llm_response,
            "overridden": False,
            "reason": "No memories found for this domain/fact_type",
            "memory_used": None
        }
    
    # Check if LLM response is vague/wrong
    response_lower = llm_response.lower()
    is_vague = any(phrase in response_lower for phrase in ["vet ikke", "don't know", "not sure", "usikker"])
    
    # Find best answering memory
    best_memory = None
    best_authority_rank = 0
    
    for memory in memories:
        # Check if this memory validates as answer
        if validates_answer(question, memory):
            auth_rank = AUTHORITY_RANK[memory.authority]
            if auth_rank > best_authority_rank:
                best_memory = memory
                best_authority_rank = auth_rank
    
    # If we found a valid high-authority answer
    if best_memory and (is_vague or best_authority_rank >= AUTHORITY_RANK["stable"]):
        return {
            "response": best_memory.fact,
            "overridden": True,
            "reason": f"Memory authority ({best_memory.authority}) overrides LLM",
            "memory_used": best_memory
        }
    
    # LLM response is acceptable
    return {
        "response": llm_response,
        "overridden": False,
        "reason": "LLM response acceptable or no better memory",
        "memory_used": None
    }


# ============================================================
# INITIALIZATION
# ============================================================

def ensure_collection():
    """Ensure Qdrant collection exists with proper configuration."""
    try:
        collection_info = qdrant_client.get_collection("efc")
        # Check if vector size matches
        if collection_info.config.params.vectors.size != 3072:
            print("⚠️ Collection has wrong vector size, using existing...")
        
        # Create indexes for filtering
        try:
            qdrant_client.create_payload_index(
                collection_name="efc",
                field_name="domain",
                field_schema="keyword"
            )
        except:
            pass  # Index might already exist
        
        try:
            qdrant_client.create_payload_index(
                collection_name="efc",
                field_name="fact_type",
                field_schema="keyword"
            )
        except:
            pass
        
        try:
            qdrant_client.create_payload_index(
                collection_name="efc",
                field_name="authority",
                field_schema="keyword"
            )
        except:
            pass
            
    except:
        qdrant_client.create_collection(
            collection_name="efc",
            vectors_config=VectorParams(
                size=3072,  # text-embedding-3-large
                distance=Distance.COSINE
            )
        )
        # Create indexes
        qdrant_client.create_payload_index(
            collection_name="efc",
            field_name="domain",
            field_schema="keyword"
        )
        qdrant_client.create_payload_index(
            collection_name="efc",
            field_name="fact_type",
            field_schema="keyword"
        )
        qdrant_client.create_payload_index(
            collection_name="efc",
            field_name="authority",
            field_schema="keyword"
        )


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":
    print("🧪 Testing Memory Model v3.0")
    print("=" * 60)
    
    # Ensure collection exists
    ensure_collection()
    
    # Test 1: Store identity facts
    print("\n1️⃣ Storing identity facts...")
    store_memory_item(
        fact="Brukeren heter Morten",
        domain="identity",
        authority="LONGTERM",
        fact_type="name",
        source="user_conversation"
    )
    store_memory_item(
        fact="AI-assistenten heter Opus",
        domain="identity",
        authority="LONGTERM",
        fact_type="name",
        source="user_conversation"
    )
    print("✅ Stored identity facts")
    
    # Test 2: Store family facts
    print("\n2️⃣ Storing family facts...")
    store_memory_item(
        fact="Morten er gift med Elisabet",
        domain="family",
        authority="LONGTERM",
        fact_type="relationship",
        source="user_conversation"
    )
    store_memory_item(
        fact="Morten har 3 barn: Joakim, Isak Andreas, og Susanna",
        domain="family",
        authority="LONGTERM",
        fact_type="count",
        source="user_conversation"
    )
    print("✅ Stored family facts")
    
    # Test 3: Classification
    print("\n3️⃣ Testing classification...")
    test_questions = [
        "Hva heter du?",
        "Hvor mange barn har jeg?",
        "Hva er entropi i EFC?"
    ]
    
    for q in test_questions:
        domain = classify_domain(q)
        fact_type = classify_fact_type(q)
        print(f"'{q}'")
        print(f"  → domain: {domain}, fact_type: {fact_type}")
    
    # Test 4: Precise retrieval
    print("\n4️⃣ Testing precise retrieval...")
    memories = retrieve_precise_memory(
        question="Hvor mange barn har jeg?",
        domain="family",
        fact_type="count"
    )
    print(f"Found {len(memories)} memories:")
    for m in memories:
        print(f"  - [{m.authority}] {m.fact}")
    
    # Test 5: Enforcement
    print("\n5️⃣ Testing enforcement...")
    test_cases = [
        ("Hva heter jeg?", "Jeg vet ikke"),
        ("Hvor mange barn har jeg?", "Du har 2 barn"),
        ("Hva heter min kone?", "Hun heter Anne")
    ]
    
    for question, draft in test_cases:
        result = enforce_with_structured_memory(question, draft)
        print(f"\nQ: {question}")
        print(f"Draft: {draft}")
        print(f"Final: {result['response']}")
        print(f"Overridden: {result['overridden']} ({result['reason']})")
    
    print("\n" + "=" * 60)
    print("✅ Memory Model v3.0 tests complete!")
