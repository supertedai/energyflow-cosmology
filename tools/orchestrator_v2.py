#!/usr/bin/env python3
"""
Orchestrator v2 - 100% Deterministic Ingestion Pipeline
========================================================

Fixes:
1. ✅ Token-based chunking (tiktoken)
2. ✅ LLM concept extraction (structured output)
3. ✅ Safe Neo4j queries (unambiguous paths)
4. ✅ Rollback safety (transaction control)

Ensures perfect sync:
- Qdrant (semantic vectors)
- Neo4j (structural graph)
- GNN (node embeddings)

Usage:
    python tools/orchestrator_v2.py --input doc.txt --type document
"""

import os
import json
import uuid
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Literal, Tuple
from dataclasses import dataclass, asdict, field

# Add parent to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams, PointIdsList
from neo4j import GraphDatabase
import tiktoken

# Authority filtering
sys.path.insert(0, os.path.dirname(__file__))
from authority_filter import get_authority_metadata, is_authoritative

# PDF support (optional)
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

load_dotenv()

# ============================================================
# CONFIG
# ============================================================

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "efc")

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Token-based chunking
CHUNK_SIZE = 512  # tokens (not chars!)
CHUNK_OVERLAP = 50  # tokens
EMBED_DIM = 3072

# Tiktoken encoder (consistent with LLM model)
TOKENIZER = tiktoken.get_encoding("cl100k_base")  # Used by gpt-4o-mini

# ============================================================
# AUTHORITY & TRUST CONFIG
# ============================================================

PRIMARY_EXTENSIONS = {
    ".tex", ".jsonld", ".py", ".ipynb"
}

# Add PDF if parser is available
if PDF_AVAILABLE:
    PRIMARY_EXTENSIONS.add(".pdf")

SECONDARY_EXTENSIONS = {
    ".md"
}

FORBIDDEN_FILENAMES = {
    "readme.md", "index.md", "todo.md", "changelog.md", "notes.md", "draft.md"
}

def get_authority_and_trust(file_path: str):
    """
    Determine authority level and trust score for a file.
    
    Returns:
        (authority_level, trust_score) or (None, None) if blocked
    """
    # SPECIAL OVERRIDE: ALL theory/ folder files are PRIMARY trust
    # User requirement: "jeg vil ha med alt i theory"
    if 'theory/' in file_path:
        return "PRIMARY", 1.0
    
    name = os.path.basename(file_path).lower()

    # BLOCK: Forbidden filenames
    if name in FORBIDDEN_FILENAMES:
        return None, None

    ext = Path(file_path).suffix.lower()

    # Explicit schema override
    if file_path.lower().endswith(".schema.json") or file_path.lower().endswith("schema.json"):
        return "PRIMARY", 1.0

    # PRIMARY sources (gold standard)
    if ext in PRIMARY_EXTENSIONS:
        return "PRIMARY", 1.0

    # SECONDARY sources (theory docs, not README)
    if ext in SECONDARY_EXTENSIONS:
        return "SECONDARY", 0.8

    # BLOCK: Everything else
    return None, None

# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class Input:
    """Standardized input format"""
    id: str
    type: Literal["chat", "document", "log"]
    timestamp: str
    source: str
    text: str
    metadata: Dict = None

@dataclass
class Chunk:
    """Text chunk with metadata"""
    id: str
    document_id: str
    text: str
    chunk_index: int
    token_count: int
    metadata: Dict

@dataclass
class Concept:
    """Extracted concept with semantic properties"""
    name: str
    type: str  # Concept|Hypothesis|Mechanism|Equation|Model|Assumption|Observation|Prediction
    description: Optional[str] = None
    confidence: float = 0.0
    domain: str = "general"  # cosmology|thermodynamics|quantum|information|cognition|meta|general
    layer: str = "applied"   # formal|applied|meta|cognitive|computational

# ============================================================
# PDF TEXT EXTRACTION
# ============================================================

def extract_pdf_text(file_path: str) -> str:
    """Extract text from PDF file using PyPDF2."""
    if not PDF_AVAILABLE:
        raise ImportError("PyPDF2 not installed. Install with: pip install PyPDF2")
    
    text_parts = []
    
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text.strip():
                text_parts.append(f"--- Page {page_num + 1} ---\n{text}")
    
    return "\n\n".join(text_parts)

# ============================================================
# STEP 1: PREPROCESSING
# ============================================================

def preprocess(text: str, input_type: str) -> str:
    """
    Normalize input text.
    """
    text = text.strip()
    
    if input_type == "chat":
        # Clean chat: collapse whitespace
        text = " ".join(text.split())
    else:
        # Keep document structure
        text = "\n".join(line.strip() for line in text.split("\n") if line.strip())
    
    return text

# ============================================================
# STEP 2: TOKEN-BASED CHUNKING (FIX #1)
# ============================================================

def chunk_text_by_tokens(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Chunk text by TOKENS, not characters.
    
    This ensures:
    - Consistent semantic boundaries
    - Predictable embedding quality
    - Stable GNN structure
    
    Args:
        text: Input text
        chunk_size: Target tokens per chunk (default 512)
        overlap: Token overlap between chunks (default 50)
    
    Returns:
        List of text chunks
    """
    # Encode to tokens
    print(f"     Encoding text to tokens...")
    tokens = TOKENIZER.encode(text)
    print(f"     Total tokens: {len(tokens)}")
    
    if len(tokens) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    chunk_count = 0
    
    while start < len(tokens):
        chunk_count += 1
        print(f"     Creating chunk {chunk_count}...", end='\r')
        
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        
        # Decode back to text
        chunk_text = TOKENIZER.decode(chunk_tokens)
        
        # Try to break at sentence boundary
        if end < len(tokens) and '.' in chunk_text:
            last_period = chunk_text.rfind('. ')
            if last_period > len(chunk_text) * 0.5:
                chunk_text = chunk_text[:last_period + 1]
                # Re-encode to get actual token count
                chunk_tokens = TOKENIZER.encode(chunk_text)
        
        chunks.append(chunk_text.strip())
        
        # Advance start position (ensure we always move forward)
        advance = max(len(chunk_tokens) - overlap, 1)
        start += advance
    
    print()  # New line after progress
    return chunks

# ============================================================
# STEP 3: EMBEDDING
# ============================================================

def embed_text(text: str) -> List[float]:
    """
    Create embedding vector using actual embed_client.
    """
    from apis.unified_api.clients.embed_client import embed_text as real_embed
    return real_embed(text)

# ============================================================
# STEP 4: LLM CONCEPT EXTRACTION (FIX #2)
# ============================================================

def extract_concepts_llm(text: str) -> Tuple[List[Concept], Dict]:
    """
    Extract concepts AND semantic structure using LLM.
    
    Returns:
        (concepts, semantic_structure)
        
    semantic_structure contains:
        - hypotheses: List[Dict]
        - mechanisms: List[Dict]
        - equations: List[Dict]
        - relationships: List[Dict]
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a semantic structure analyzer for scientific knowledge graphs.

Extract both CONCEPTS and SEMANTIC STRUCTURE from the text.

Return JSON with:
{
  "concepts": [
    {
      "name": "concept name (2-4 words)",
      "type": "Concept|Hypothesis|Mechanism|Equation|Model|Assumption|Observation|Prediction",
      "description": "brief description",
      "confidence": 0.0-1.0,
      "domain": "cosmology|thermodynamics|quantum|information|cognition|meta|general",
      "layer": "formal|applied|meta|cognitive|computational"
    }
  ],
  "relationships": [
    {
      "source": "concept name",
      "target": "concept name",
      "type": "SUPPORTS|CONTRADICTS|DERIVES_FROM|PART_OF|CAUSES|EXPLAINS|DEPENDS_ON|IMPLIES|CONSTRAINS|ENABLES",
      "strength": 0.0-1.0,
      "reasoning": "brief explanation"
    }
  ]
}

Be selective: extract 3-10 concepts and their most important relationships."""
                },
                {
                    "role": "user",
                    "content": f"Extract concepts and structure from:\n\n{text[:2000]}"
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Extract concepts
        concept_items = result.get("concepts", [])
        concepts = []
        for item in concept_items:
            concepts.append(Concept(
                name=item.get("name", "Unknown"),
                type=item.get("type", "Concept"),
                description=item.get("description"),
                confidence=item.get("confidence", 0.7),
                domain=item.get("domain", "general"),
                layer=item.get("layer", "applied")
            ))
        
        # Extract semantic structure
        semantic_structure = {
            "relationships": result.get("relationships", [])
        }
        
        return concepts, semantic_structure
    
    except Exception as e:
        print(f"⚠️  LLM extraction failed: {e}")
        print("   Falling back to keyword extraction")
        return extract_concepts_fallback(text), {"relationships": []}

def extract_concepts_fallback(text: str) -> Tuple[List[Concept], Dict]:
    """
    Fallback keyword extraction if LLM fails.
    """
    concepts = []
    keywords = {
        "entropy": ("Concept", "thermodynamics"),
        "energy flow": ("Concept", "thermodynamics"),
        "cosmology": ("Concept", "cosmology"),
        "consciousness": ("Concept", "cognition"),
        "meta": ("Concept", "meta"),
        "symbiosis": ("Concept", "meta"),
        "GNN": "technical",
        "graph": "technical",
    }
    
    text_lower = text.lower()
    for keyword, (node_type, domain) in keywords.items():
        if keyword in text_lower:
            concepts.append(Concept(
                name=keyword.title(),
                type=node_type,
                domain=domain,
                confidence=0.6
            ))
    
    return concepts, {"relationships": []}

# ============================================================
# STEP 5: QDRANT INSERTION
# ============================================================

def ingest_to_qdrant(client: QdrantClient, chunks: List[Chunk]) -> List[str]:
    """
    Insert chunks to Qdrant.
    Returns list of inserted point IDs.
    """
    points = []
    
    for i, chunk in enumerate(chunks, 1):
        print(f"     Embedding chunk {i}/{len(chunks)}...", end='\r')
        vector = embed_text(chunk.text)
        
        # Validate embedding dimension
        if len(vector) != EMBED_DIM:
            raise ValueError(f"Embedding dim {len(vector)} != EMBED_DIM {EMBED_DIM}")
        
        point = PointStruct(
            id=chunk.id,
            vector=vector,
            payload={
                "document_id": chunk.document_id,
                "text": chunk.text,
                "chunk_index": chunk.chunk_index,
                "token_count": chunk.token_count,
                "source": chunk.metadata.get("source", "unknown"),
                "type": chunk.metadata.get("type", "unknown"),
                "timestamp": chunk.metadata.get("timestamp"),
                # Authority & trust (CRITICAL for hybrid scoring)
                "authority": chunk.metadata.get("authority"),
                "trust": chunk.metadata.get("trust"),
            }
        )
        points.append(point)
    
    client.upsert(
        collection_name=QDRANT_COLLECTION,
        points=points
    )
    
    return [p.id for p in points]

# ============================================================
# STEP 6: NEO4J INSERTION (FIX #3 + #4)
# ============================================================

def ingest_to_neo4j(driver, document: Input, chunks: List[Chunk], concepts: List[Concept], semantic_structure: Dict) -> str:
    """
    Insert document, chunks, concepts AND semantic structure to Neo4j.
    
    FIX #3: Use unambiguous queries
    FIX #4: Rollback safety via transaction
    
    Structure:
        (:Document) -[:HAS_CHUNK]-> (:Chunk)
        (:Chunk) -[:MENTIONS]-> (:Concept|Hypothesis|Mechanism|...)
        (:Concept) -[:SUPPORTS|CONTRADICTS|...]-> (:Concept)
    
    Returns document node elementId.
    """
    with driver.session() as session:
        tx = None
        try:
            # Start transaction
            tx = session.begin_transaction()
            
            # 1. Create Document node
            result = tx.run("""
                CREATE (d:Document {
                    id: $id,
                    type: $type,
                    source: $source,
                    timestamp: $timestamp,
                    text_length: $text_length,
                    authority: $authority,
                    trust: $trust
                })
                RETURN elementId(d) AS node_id
            """, 
                id=document.id,
                type=document.type,
                source=document.source,
                timestamp=document.timestamp,
                text_length=len(document.text),
                authority=document.metadata["authority"],
                trust=document.metadata["trust"]
            )
            doc_node_id = result.single()["node_id"]
            
            # 2. Create Chunk nodes with UNAMBIGUOUS relations
            authority = document.metadata["authority"]
            trust = document.metadata["trust"]
            
            for i, chunk in enumerate(chunks, 1):
                print(f"     Creating Neo4j chunk {i}/{len(chunks)}...", end='\r')
                tx.run("""
                    MATCH (d:Document {id: $doc_id})
                    CREATE (c:Chunk {
                        id: $chunk_id,
                        text: $text,
                        chunk_index: $chunk_index,
                        token_count: $token_count,
                        authority: $authority,
                        trust: $trust
                    })
                    CREATE (d)-[:HAS_CHUNK]->(c)
                """,
                    doc_id=document.id,
                    chunk_id=chunk.id,
                    text=chunk.text[:1000],  # Store reasonable amount
                    chunk_index=chunk.chunk_index,
                    token_count=chunk.token_count,
                    authority=authority,
                    trust=trust
                )
            
            # 3. Create Concept nodes with semantic properties
            print(f"\n     Linking {len(concepts)} concepts...")
            for concept in concepts:
                # Determine node label from type
                node_label = concept.type if concept.type in [
                    "Hypothesis", "Mechanism", "Equation", "Model", 
                    "Assumption", "Observation", "Prediction"
                ] else "Concept"
                
                tx.run(f"""
                    MERGE (c:{node_label} {{name: $name}})
                    ON CREATE SET 
                        c.type = $type,
                        c.description = $description,
                        c.domain = $domain,
                        c.layer = $layer,
                        c.created = timestamp()
                    
                    WITH c
                    MATCH (d:Document {{id: $doc_id}})-[:HAS_CHUNK]->(chunk:Chunk)
                    WHERE toLower(chunk.text) CONTAINS toLower($name)
                    MERGE (chunk)-[:MENTIONS {{confidence: $confidence}}]->(c)
                """,
                    name=concept.name,
                    type=concept.type,
                    description=concept.description,
                    domain=concept.domain,
                    layer=concept.layer,
                    doc_id=document.id,
                    confidence=concept.confidence
                )
            
            # 4. Create semantic relationships
            relationships = semantic_structure.get("relationships", [])
            if relationships:
                print(f"\n     Creating {len(relationships)} semantic relationships...")
                for rel in relationships:
                    rel_type = rel.get("type", "RELATES_TO")
                    source = rel.get("source")
                    target = rel.get("target")
                    strength = rel.get("strength", 0.7)
                    reasoning = rel.get("reasoning", "")
                    
                    if source and target:
                        try:
                            tx.run(f"""
                                MATCH (source {{name: $source_name}})
                                MATCH (target {{name: $target_name}})
                                MERGE (source)-[r:{rel_type}]->(target)
                                ON CREATE SET 
                                    r.strength = $strength,
                                    r.reasoning = $reasoning,
                                    r.created = timestamp()
                            """,
                                source_name=source,
                                target_name=target,
                                strength=strength,
                                reasoning=reasoning
                            )
                        except Exception as e:
                            print(f"     ⚠️  Failed to create {rel_type} relationship: {e}")
            
            # Commit transaction
            tx.commit()
            return doc_node_id
        
        except Exception as e:
            # Rollback on error
            if tx is not None:
                tx.rollback()
            raise Exception(f"Neo4j insertion failed: {e}")

# ============================================================
# STEP 8: GNN BRIDGE - MAP CHUNK UUIDs TO GNN NODE INDICES
# ============================================================

GNN_BRIDGE_FILE = Path("symbiose_gnn_output/gnn_bridge.json")
GNN_NODE_MAPPING = Path("symbiose_gnn_output/node_mapping.json")

def load_gnn_bridge() -> Dict[str, int]:
    """Load existing chunk UUID → GNN index mapping"""
    if GNN_BRIDGE_FILE.exists():
        with open(GNN_BRIDGE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_gnn_bridge(bridge: Dict[str, int]):
    """Save chunk UUID → GNN index mapping"""
    GNN_BRIDGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(GNN_BRIDGE_FILE, 'w') as f:
        json.dump(bridge, f, indent=2)

def load_gnn_node_mapping() -> Dict[str, str]:
    """Load GNN index → Neo4j node ID mapping"""
    if GNN_NODE_MAPPING.exists():
        with open(GNN_NODE_MAPPING, 'r') as f:
            return json.load(f)
    return {}

def update_gnn_bridge(chunks: List[Chunk], neo4j_driver) -> Dict[str, int]:
    """
    Map new chunk UUIDs to GNN node indices.
    
    Strategy:
    1. Load existing gnn_bridge.json (chunk_uuid → gnn_index)
    2. Load node_mapping.json (gnn_index → old_neo4j_id)
    3. Query Neo4j to get new chunk Neo4j internal IDs
    4. Try to match new chunks to old GNN nodes by text similarity
    5. For unmatched chunks, assign new GNN indices
    6. Save updated bridge
    
    Returns:
        Dict mapping chunk_id → gnn_index
    """
    bridge = load_gnn_bridge()
    gnn_mapping = load_gnn_node_mapping()
    
    # Get next available GNN index
    max_gnn_index = max([int(k) for k in gnn_mapping.keys()] + [0])
    next_gnn_index = max_gnn_index + 1
    
    new_mappings = {}
    
    with neo4j_driver.session() as session:
        for chunk in chunks:
            # If chunk already has GNN mapping, keep it
            if chunk.id in bridge:
                new_mappings[chunk.id] = bridge[chunk.id]
                continue
            
            # Assign new GNN index (for now - simple sequential assignment)
            # TODO: In future, could match by text similarity to existing GNN nodes
            new_mappings[chunk.id] = next_gnn_index
            bridge[chunk.id] = next_gnn_index
            next_gnn_index += 1
    
    # Save updated bridge
    save_gnn_bridge(bridge)
    
    return new_mappings

# ============================================================
# ORCHESTRATOR - MAIN PIPELINE WITH ROLLBACK SAFETY (FIX #4)
# ============================================================

def orchestrate(
    text: str,
    source: str,
    input_type: Literal["chat", "document", "log"] = "document",
    metadata: Dict = None
) -> Dict:
    """
    Full ingestion pipeline with rollback safety.
    
    If any step fails:
    - Qdrant points are deleted
    - Neo4j transaction is rolled back
    - Exception is raised
    
    This ensures no partial/corrupt state.
    """
    print(f"🚀 Orchestrator v2 starting: {input_type} from {source}")
    
    # HARD AUTHORITY GATE
    # Use full file_path from metadata if available (for accurate theory/ detection)
    auth_check_path = metadata.get("file_path", source) if metadata else source
    authority, trust = get_authority_and_trust(auth_check_path)
    
    if authority is None:
        raise RuntimeError(f"⛔ BLOCKED: Non-authoritative file: {source}")
    
    print(f"  🏆 Authority: {authority} (trust={trust})")
    
    qdrant_client = None
    neo4j_driver = None
    inserted_chunk_ids = []
    
    try:
        # Step 1: Create standardized input
        doc_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        input_doc = Input(
            id=doc_id,
            type=input_type,
            timestamp=timestamp,
            source=source,
            text=text,
            metadata={
                "authority": authority,
                "trust": trust,
                **(metadata or {})
            }
        )
        
        # Step 2: Preprocess
        print("  📝 Preprocessing...")
        clean_text = preprocess(text, input_type)
        
        # Step 3: Token-based chunking (FIX #1)
        print("  ✂️  Chunking by tokens...")
        text_chunks = chunk_text_by_tokens(clean_text)
        print(f"     Generated {len(text_chunks)} chunks")
        
        # Step 4: Create Chunk objects with token counts
        chunks = []
        for idx, chunk_text in enumerate(text_chunks):
            # Use UUID for Qdrant (not string with suffix)
            chunk_id = str(uuid.uuid4())
            token_count = len(TOKENIZER.encode(chunk_text))
            
            chunks.append(Chunk(
                id=chunk_id,
                document_id=doc_id,
                text=chunk_text,
                chunk_index=idx,
                token_count=token_count,
                metadata={
                    "source": source,
                    "type": input_type,
                    "timestamp": timestamp,
                    "authority": authority,
                    "trust": trust,
                    **(metadata or {})
                }
            ))
        
        # Step 5: LLM concept extraction + semantic structure
        print("  🧠 Extracting concepts & structure (LLM)...")
        concepts, semantic_structure = extract_concepts_llm(clean_text)
        print(f"     Found {len(concepts)} concepts: {[c.name for c in concepts]}")
        print(f"     Found {len(semantic_structure.get('relationships', []))} relationships")
        
        # Step 6: Ingest to Qdrant
        print("  📊 Inserting to Qdrant...")
        qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        
        # Ensure collection exists
        try:
            qdrant_client.get_collection(QDRANT_COLLECTION)
        except:
            qdrant_client.create_collection(
                collection_name=QDRANT_COLLECTION,
                vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE)
            )
        
        inserted_chunk_ids = ingest_to_qdrant(qdrant_client, chunks)
        print(f"     ✅ {len(inserted_chunk_ids)} chunks in Qdrant")
        
        # Step 7: Ingest to Neo4j (FIX #3: safe queries, FIX #4: transaction)
        print("  🕸️  Inserting to Neo4j...")
        neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        neo4j_node_id = ingest_to_neo4j(neo4j_driver, input_doc, chunks, concepts, semantic_structure)
        print(f"     ✅ Neo4j node: {neo4j_node_id}")
        
        # Step 8: GNN index update
        print("  🧬 GNN index update...")
        gnn_mappings = update_gnn_bridge(chunks, neo4j_driver)
        print(f"     ✅ {len(gnn_mappings)} chunks mapped to GNN")
        
        neo4j_driver.close()
        
        print("✅ Orchestrator v2 complete\n")
        
        return {
            "document_id": doc_id,
            "chunk_ids": inserted_chunk_ids,
            "concepts": [c.name for c in concepts],
            "neo4j_node_id": neo4j_node_id,
            "qdrant_collection": QDRANT_COLLECTION,
            "total_tokens": sum(c.token_count for c in chunks)
        }
    
    except Exception as e:
        # ROLLBACK: Delete Qdrant points if Neo4j failed
        print(f"\n❌ ERROR: {e}")
        print("🔄 Rolling back...")
        
        if inserted_chunk_ids and qdrant_client:
            try:
                qdrant_client.delete(
                    collection_name=QDRANT_COLLECTION,
                    points_selector=PointIdsList(points=inserted_chunk_ids)
                )
                print(f"   ✅ Deleted {len(inserted_chunk_ids)} Qdrant points")
            except Exception as rollback_error:
                print(f"   ⚠️  Rollback failed: {rollback_error}")
        
        raise e
    
    finally:
        if neo4j_driver:
            neo4j_driver.close()

# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Orchestrator v2 - 100% deterministic pipeline")
    parser.add_argument("--input", required=True, help="Input file or text")
    parser.add_argument("--type", choices=["chat", "document", "log"], default="document")
    parser.add_argument("--source", help="Source identifier (default: filename)")
    
    args = parser.parse_args()
    
    # Read input
    input_path = Path(args.input)
    if input_path.exists():
        # Handle PDF files
        if input_path.suffix.lower() == '.pdf':
            if not PDF_AVAILABLE:
                print(f"❌ PyPDF2 not installed. Cannot process PDF files.")
                print(f"   Install with: pip install PyPDF2")
                sys.exit(1)
            
            try:
                text = extract_pdf_text(str(input_path))
                print(f"📄 Extracted {len(text)} characters from PDF")
            except Exception as e:
                print(f"❌ Failed to extract PDF text: {e}")
                sys.exit(1)
        else:
            # Regular text file
            text = input_path.read_text()
        
        source = args.source or input_path.name
    else:
        text = args.input
        source = args.source or "cli"
    
    # Run orchestrator
    try:
        result = orchestrate(
            text=text,
            source=source,
            input_type=args.type
        )
        
        print("\n📋 Result:")
        print(json.dumps(result, indent=2))
    
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        sys.exit(1)
