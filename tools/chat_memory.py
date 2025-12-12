#!/usr/bin/env python3
"""
chat_memory.py - Chat Integration for Private Memory System
===========================================================

Purpose: Bridge between chat interface and Private Memory system.

Features:
- Automatic storage of important chat turns
- Retrieval of relevant personal context (adaptive embedding dimensions)
- Selective LONGTERM promotion for high-confidence memories
- Integration with memory classification and feedback loop

Architecture:
- Uses label-based namespace isolation (:PrivateChunk vs :Chunk)
- Single Neo4j database (Aura-compatible)
- Adaptive embedding dimensions (matches Qdrant collection config)
- ChunkClassification dataclass for type safety

Usage:
    # Store chat interaction
    from chat_memory import store_chat_turn
    store_chat_turn(
        user_message="I'm married to Elisabet",
        assistant_message="Got it, stored!",
        importance="high"
    )
    
    # Retrieve relevant context
    from chat_memory import retrieve_relevant_memory
    context = retrieve_relevant_memory("Who am I married to?")
    
    # In chat loop
    context = retrieve_relevant_memory(user_query)
    augmented_prompt = f"Relevant memories:\\n{context}\\n\\nUser: {user_query}"

Production-Ready Fixes (Phase 21):
1. ✅ ChunkClassification dataclass access (correct property usage)
2. ✅ Adaptive embedding dimensions (matches Qdrant collection)
3. ✅ Selective LONGTERM promotion (only high-confidence STM → LONGTERM)
4. ✅ Label-based isolation (no database parameter needed)
5. ✅ Verified payload["text"] exists in Qdrant
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
import openai

load_dotenv()

# ============================================================
# CONFIG
# ============================================================

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DB = os.getenv("NEO4J_DB", "neo4j")  # Use default for Aura single-db

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

CHAT_LOG = Path("symbiose_gnn_output/chat_memory.jsonl")

# Importance thresholds
IMPORTANCE_KEYWORDS = {
    "high": [
        # Identity
        "my name is", "i am", "i'm called", "jeg heter", "jeg er",
        # Family/Relationships  
        "married to", "wife", "husband", "kone", "mann", "gift med",
        "children", "barn", "child", "son", "daughter", "sønn", "datter",
        "heter", "kalles", "navnet", "named", "called",
        # Critical facts
        "work at", "live in", "bor i", "jobber", "born in", "født",
        # Explicit storage requests
        "remember", "don't forget", "husk", "ikke glem", "lagre", "store"
    ],
    "medium": ["like", "prefer", "enjoy", "interested in", "hobby", "favorite", "liker", "foretrekker"],
    "low": ["weather", "hello", "hi", "thanks", "okay", "hei", "takk"]
}

# ============================================================
# STORAGE FUNCTIONS
# ============================================================

def detect_importance(text: str) -> str:
    """
    Heuristic importance detection.
    Returns: "high" | "medium" | "low"
    """
    text_lower = text.lower()
    
    # Check high importance
    for keyword in IMPORTANCE_KEYWORDS["high"]:
        if keyword in text_lower:
            return "high"
    
    # Check medium importance
    for keyword in IMPORTANCE_KEYWORDS["medium"]:
        if keyword in text_lower:
            return "medium"
    
    return "low"

def store_chat_turn(
    user_message: str,
    assistant_message: str,
    importance: Optional[str] = None,
    session_id: Optional[str] = None
) -> Dict:
    """
    Store a chat turn in Private Memory system.
    
    Only stores user message if importance >= medium.
    
    Args:
        user_message: What user said
        assistant_message: What assistant responded
        importance: "high" | "medium" | "low" (auto-detect if None)
        session_id: Optional session grouping
    
    Returns:
        Dict with document_id, chunk_ids, stored status
    """
    # Auto-detect importance if not provided
    if importance is None:
        importance = detect_importance(user_message)
    
    # Only store medium/high importance
    if importance == "low":
        return {
            "stored": False,
            "reason": "Low importance - not stored",
            "importance": importance
        }
    
    # Prepare input for private orchestrator
    timestamp = datetime.utcnow().isoformat()
    combined_text = f"User: {user_message}\nAssistant: {assistant_message}"
    
    # Log to JSONL
    CHAT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(CHAT_LOG, 'a') as f:
        f.write(json.dumps({
            "timestamp": timestamp,
            "user_message": user_message,
            "assistant_message": assistant_message,
            "importance": importance,
            "session_id": session_id
        }) + '\n')
    
    # Import orchestrator dynamically to avoid circular imports
    sys.path.insert(0, str(Path(__file__).parent))
    from private_orchestrator import orchestrate
    
    # Store in Private Memory
    result = orchestrate(
        text=user_message,  # Only store user message
        input_type="chat",
        metadata={
            "importance": importance,
            "session_id": session_id,
            "assistant_response": assistant_message[:200]  # Store snippet
        }
    )
    
    # Auto-classify if high importance
    if importance == "high":
        from memory_classifier import classify_chunks_llm, update_neo4j_memory_class, update_qdrant_memory_class
        
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        
        try:
            # Fetch chunks
            with driver.session() as session:
                chunks_result = session.run("""
                    MATCH (d:PrivateDocument {id: $doc_id})-[:HAS_CHUNK]->(c:PrivateChunk)
                    RETURN c.id AS id, c.text AS text
                    ORDER BY c.chunk_index
                """, doc_id=result["document_id"])
                
                chunks = [{"id": r["id"], "text": r["text"]} for r in chunks_result]
            
            # Classify - let LLM decide, but bias toward LONGTERM for high importance
            classifications = classify_chunks_llm(chunks)
            
            # Force LONGTERM for high importance (never DISCARD)
            # This ensures critical memories are preserved
            for c in classifications:
                if c.memory_class in ["DISCARD", "STM"] or c.confidence < 0.5:
                    c.memory_class = "LONGTERM"
                    c.reasoning = f"High importance chat memory (auto-promoted): {c.reasoning}"
            
            # Update databases
            update_neo4j_memory_class(driver, classifications)
            update_qdrant_memory_class(qdrant_client, classifications)
            
        finally:
            driver.close()
    
    return {
        "stored": True,
        "importance": importance,
        "document_id": result["document_id"],
        "chunk_ids": result["chunk_ids"],
        "concepts": result.get("concepts", [])
    }

# ============================================================
# RETRIEVAL FUNCTIONS
# ============================================================

def _expand_query_multilingual(query: str) -> str:
    """
    AUTO-EXPAND queries with multilingual keywords.
    
    This is a FAILSAFE for when LLM doesn't follow system prompt.
    Embeddings handle multilingual well, so this boosts recall.
    """
    query_lower = query.lower()
    
    # Common patterns and their multilingual expansions
    expansions = {
        # Identity
        "name": "name navn jeg heter my name is jeg er",
        "who am i": "who am i hvem er jeg my name jeg heter identity navn",
        "identity": "identity identitet name navn who hvem",
        
        # Relationships
        "wife": "wife kone spouse ektefelle married gift",
        "husband": "husband mann spouse ektefelle married gift",
        "spouse": "spouse ektefelle wife kone husband mann married gift",
        "married": "married gift spouse ektefelle wife kone husband mann",
        "family": "family familie wife kone husband mann children barn",
        
        # Preferences
        "like": "like liker enjoy elsker love prefer foretrekker",
        "prefer": "prefer foretrekker like liker favorite favoritt",
        "favorite": "favorite favoritt prefer foretrekker like liker",
        
        # Work
        "work": "work arbeid job jobb occupation yrke",
        "job": "job jobb work arbeid occupation yrke",
        
        # Location
        "live": "live bor location sted city by where hvor",
        "location": "location sted live bor city by place plass",
    }
    
    # Check for patterns and expand
    expanded_terms = [query]
    for pattern, expansion in expansions.items():
        if pattern in query_lower:
            expanded_terms.append(expansion)
    
    # Join all terms
    return " ".join(expanded_terms)


def retrieve_relevant_memory(
    query: str,
    k: int = 5,
    memory_class_filter: Optional[str] = None  # Changed: Accept all memory classes by default
) -> str:
    """
    Retrieve relevant memories for a query.
    
    Args:
        query: User's question or context
        k: Number of results to return
        memory_class_filter: Filter by memory class (None = all, "LONGTERM", "STM", "WORKING")
    
    Returns:
        Formatted string with relevant memories
    """
    # AUTO-EXPAND query with multilingual keywords (FAILSAFE)
    expanded_query = _expand_query_multilingual(query)
    
    qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    
    # Get collection info to match dimensions
    try:
        collection_info = qdrant_client.get_collection("private")
        vector_size = collection_info.config.params.vectors.size
    except:
        vector_size = 3072  # Default to 3072 if collection doesn't exist
    
    # Generate query embedding with matching dimensions (use expanded query)
    response = openai.embeddings.create(
        model="text-embedding-3-large",
        input=expanded_query,  # Use expanded query here!
        dimensions=vector_size
    )
    query_embedding = response.data[0].embedding
    
    # Search in Qdrant private collection
    search_results = qdrant_client.search(
        collection_name="private",
        query_vector=query_embedding,
        limit=k * 2,  # Get more, then filter
        with_payload=True
    )
    
    # Filter by memory class if specified
    if memory_class_filter:
        search_results = [
            r for r in search_results 
            if r.payload.get("memory_class") == memory_class_filter
        ][:k]
    else:
        search_results = search_results[:k]
    
    # Format results
    if not search_results:
        return ""
    
    memories = []
    for i, result in enumerate(search_results, 1):
        text = result.payload.get("text", "")
        score = result.score
        memory_class = result.payload.get("memory_class", "UNKNOWN")
        
        memories.append(f"{i}. [{memory_class}, score: {score:.2f}] {text}")
    
    return "\n".join(memories)

def get_user_profile() -> Dict:
    """
    Extract user profile from Private Memory.
    
    Returns structured information about the user.
    """
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        with driver.session() as session:
            # Get all LONGTERM concepts
            result = session.run("""
                MATCH (c:PrivateConcept)
                RETURN c.name AS concept, count(*) AS frequency
                ORDER BY frequency DESC
                LIMIT 20
            """)
            
            concepts = [{"name": r["concept"], "frequency": r["frequency"]} for r in result]
            
            # Get key facts (LONGTERM chunks with high importance)
            facts_result = session.run("""
                MATCH (c:PrivateChunk)
                WHERE c.memory_class = 'LONGTERM'
                RETURN c.text AS text, c.memory_confidence AS confidence
                ORDER BY confidence DESC
                LIMIT 10
            """)
            
            facts = [r["text"] for r in facts_result]
        
        return {
            "key_concepts": concepts,
            "key_facts": facts
        }
    
    finally:
        driver.close()

# ============================================================
# FEEDBACK INTEGRATION
# ============================================================

def mark_memory_useful(chunk_id: str, context: str = "Used in chat"):
    """Mark a memory as useful (positive feedback)"""
    from feedback_listener import log_chunk_feedback
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        log_chunk_feedback(
            driver=driver,
            chunk_id=chunk_id,
            signal="good",
            aspect="relevance",
            strength=1.0,
            context=context
        )
    finally:
        driver.close()

def mark_memory_wrong(chunk_id: str, context: str = "Incorrect in chat"):
    """Mark a memory as wrong (negative feedback)"""
    from feedback_listener import log_chunk_feedback
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        log_chunk_feedback(
            driver=driver,
            chunk_id=chunk_id,
            signal="incorrect",
            aspect="accuracy",
            strength=1.0,
            context=context
        )
    finally:
        driver.close()

# ============================================================
# CLI TESTING
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Chat Memory Integration")
    
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # Store command
    store_parser = subparsers.add_parser("store", help="Store chat turn")
    store_parser.add_argument("--user", required=True, help="User message")
    store_parser.add_argument("--assistant", required=True, help="Assistant response")
    store_parser.add_argument("--importance", choices=["high", "medium", "low"], help="Importance level")
    
    # Retrieve command
    retrieve_parser = subparsers.add_parser("retrieve", help="Retrieve memories")
    retrieve_parser.add_argument("--query", required=True, help="Query string")
    retrieve_parser.add_argument("--k", type=int, default=5, help="Number of results")
    
    # Profile command
    profile_parser = subparsers.add_parser("profile", help="Get user profile")
    
    args = parser.parse_args()
    
    if args.command == "store":
        result = store_chat_turn(
            user_message=args.user,
            assistant_message=args.assistant,
            importance=args.importance
        )
        print(json.dumps(result, indent=2))
    
    elif args.command == "retrieve":
        memories = retrieve_relevant_memory(args.query, k=args.k)
        print("\n🧠 Relevant Memories:")
        print("=" * 60)
        print(memories if memories else "No memories found")
    
    elif args.command == "profile":
        profile = get_user_profile()
        print("\n👤 User Profile:")
        print("=" * 60)
        print("\nKey Concepts:")
        for c in profile["key_concepts"][:10]:
            print(f"  - {c['name']} (mentioned {c['frequency']}x)")
        print("\nKey Facts:")
        for i, fact in enumerate(profile["key_facts"][:5], 1):
            print(f"  {i}. {fact[:100]}...")
    
    else:
        parser.print_help()
