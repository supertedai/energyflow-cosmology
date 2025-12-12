#!/usr/bin/env python3
"""
export_trainer.py - Export Training Data from Private Knowledge Graph
=====================================================================

Purpose: Export Private knowledge + Feedback + Intention scores to structured formats
for offline analysis, GNN training, bias detection, and steering simulation.

Key principle: Separate SOURCE (user) from LEARNING (model).

Exports:
- PrivateChunk (structure)
- Feedback (human signals)
- Memory classification (STM/LONGTERM/DISCARD)
- Intention gate scores (importance, uncertainty, conflict, risk)
- Concept relationships

Output formats:
- JSONL (streaming, line-delimited JSON)
- Parquet (columnar, efficient for analytics)
- CSV (simple tabular)

Usage:
    # Export all data to JSONL
    python tools/export_trainer.py --format jsonl --output training_data.jsonl
    
    # Export to Parquet for analytics
    python tools/export_trainer.py --format parquet --output training_data.parquet
    
    # Export with intention scores
    python tools/export_trainer.py --format jsonl --output full_data.jsonl --include-intentions
    
    # Export statistics only
    python tools/export_trainer.py --stats-only
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Literal, Optional, List, Dict, Any
from dataclasses import dataclass, asdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

# ============================================================
# CONFIG
# ============================================================

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

DEFAULT_OUTPUT_DIR = Path("symbiose_gnn_output/training_exports")

# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class ChunkRecord:
    """Single chunk with all associated data"""
    chunk_id: str
    doc_id: str
    text: str
    memory_class: str
    created_at: int
    
    # Feedback aggregation
    feedback_count: int
    positive_count: int
    negative_count: int
    uncertain_count: int
    manual_feedback_count: int
    feedback_sources: List[str]
    
    # Intention scores (if available)
    importance: Optional[float] = None
    uncertainty: Optional[float] = None
    confidence: Optional[float] = None
    conflict: Optional[bool] = None
    risk: Optional[str] = None
    suggested_action: Optional[str] = None
    
    # Concepts
    concepts: List[str] = None
    concept_count: int = 0

@dataclass
class FeedbackRecord:
    """Individual feedback signal"""
    feedback_id: str
    chunk_id: str
    signal: str
    strength: float
    aspect: str
    source: str
    timestamp: int
    context: Optional[str] = None
    suggested_class: Optional[str] = None

@dataclass
class ConceptRecord:
    """Concept with relationships"""
    concept_name: str
    concept_type: str
    chunk_count: int
    chunks: List[str]

@dataclass
class ExportStats:
    """Export metadata and statistics"""
    export_timestamp: str
    total_chunks: int
    total_feedback: int
    total_concepts: int
    
    chunks_by_class: Dict[str, int]
    feedback_by_signal: Dict[str, int]
    feedback_by_source: Dict[str, int]
    
    avg_feedback_per_chunk: float
    chunks_with_feedback: int
    chunks_without_feedback: int
    
    promotion_candidates: int
    high_conflict_chunks: int

# ============================================================
# DATA EXTRACTION
# ============================================================

def fetch_all_chunks(driver) -> List[Dict[str, Any]]:
    """Fetch all PrivateChunks with aggregated feedback"""
    with driver.session() as session:
        result = session.run("""
            MATCH (d:PrivateDocument)-[:HAS_CHUNK]->(c:PrivateChunk)
            OPTIONAL MATCH (c)<-[r]-(f:Feedback)
            OPTIONAL MATCH (c)-[:MENTIONS]->(concept:PrivateConcept)
            
            WITH d, c, 
                 collect(DISTINCT {
                     id: f.id,
                     signal: f.signal,
                     strength: f.strength,
                     aspect: properties(r).aspect,
                     source: f.source,
                     timestamp: f.timestamp,
                     context: f.context,
                     suggested_class: properties(r).suggested_class
                 }) as feedback,
                 collect(DISTINCT concept.name) as concepts
            
            RETURN 
                c.id as chunk_id,
                d.id as doc_id,
                c.text as text,
                c.memory_class as memory_class,
                c.created_at as created_at,
                feedback,
                concepts
            ORDER BY c.created_at DESC
        """)
        
        chunks = []
        for record in result:
            # Filter out null feedback
            feedback = [f for f in record["feedback"] if f["signal"] is not None]
            
            # Aggregate feedback stats
            positive = sum(1 for f in feedback if f["signal"] in ["good", "correct"])
            negative = sum(1 for f in feedback if f["signal"] in ["bad", "incorrect"])
            uncertain = sum(1 for f in feedback if f["signal"] in ["unsure", "neutral"])
            manual = sum(1 for f in feedback if f["source"] == "manual")
            sources = list(set(f["source"] for f in feedback))
            
            # Filter out null concepts
            concepts = [c for c in record["concepts"] if c is not None]
            
            chunks.append({
                "chunk_id": record["chunk_id"],
                "doc_id": record["doc_id"],
                "text": record["text"],
                "memory_class": record["memory_class"],
                "created_at": record["created_at"],
                "feedback": feedback,
                "feedback_count": len(feedback),
                "positive_count": positive,
                "negative_count": negative,
                "uncertain_count": uncertain,
                "manual_feedback_count": manual,
                "feedback_sources": sources,
                "concepts": concepts,
                "concept_count": len(concepts)
            })
        
        return chunks

def fetch_all_feedback(driver) -> List[Dict[str, Any]]:
    """Fetch all Feedback as individual records"""
    with driver.session() as session:
        result = session.run("""
            MATCH (f:Feedback)-[r]->(c:PrivateChunk)
            RETURN 
                f.id as feedback_id,
                c.id as chunk_id,
                f.signal as signal,
                f.strength as strength,
                properties(r).aspect as aspect,
                f.source as source,
                f.timestamp as timestamp,
                f.context as context,
                properties(r).suggested_class as suggested_class
            ORDER BY f.timestamp DESC
        """)
        
        return [dict(record) for record in result]

def fetch_all_concepts(driver) -> List[Dict[str, Any]]:
    """Fetch all PrivateConcepts with relationships"""
    with driver.session() as session:
        result = session.run("""
            MATCH (concept:PrivateConcept)
            OPTIONAL MATCH (concept)<-[:MENTIONS]-(c:PrivateChunk)
            
            WITH concept, collect(DISTINCT c.id) as chunks
            
            RETURN 
                concept.name as concept_name,
                concept.type as concept_type,
                size(chunks) as chunk_count,
                chunks
            ORDER BY chunk_count DESC
        """)
        
        return [dict(record) for record in result]

def calculate_stats(chunks: List[Dict], feedback: List[Dict]) -> ExportStats:
    """Calculate export statistics"""
    
    # Chunks by class
    chunks_by_class = {}
    for c in chunks:
        cls = c["memory_class"]
        chunks_by_class[cls] = chunks_by_class.get(cls, 0) + 1
    
    # Feedback by signal
    feedback_by_signal = {}
    for f in feedback:
        signal = f["signal"]
        feedback_by_signal[signal] = feedback_by_signal.get(signal, 0) + 1
    
    # Feedback by source
    feedback_by_source = {}
    for f in feedback:
        source = f["source"]
        feedback_by_source[source] = feedback_by_source.get(source, 0) + 1
    
    # Chunks with/without feedback
    chunks_with_feedback = sum(1 for c in chunks if c["feedback_count"] > 0)
    chunks_without_feedback = len(chunks) - chunks_with_feedback
    
    # Average feedback per chunk
    avg_feedback = sum(c["feedback_count"] for c in chunks) / len(chunks) if chunks else 0
    
    # Promotion candidates (STM with ≥2 positive, ≥1 manual)
    promotion_candidates = sum(1 for c in chunks 
                               if c["memory_class"] == "STM" 
                               and c["positive_count"] >= 2 
                               and c["manual_feedback_count"] >= 1)
    
    # High conflict chunks (both positive and negative)
    high_conflict = sum(1 for c in chunks 
                       if c["positive_count"] > 0 and c["negative_count"] > 0)
    
    return ExportStats(
        export_timestamp=datetime.utcnow().isoformat(),
        total_chunks=len(chunks),
        total_feedback=len(feedback),
        total_concepts=0,  # Will be updated if concepts exported
        chunks_by_class=chunks_by_class,
        feedback_by_signal=feedback_by_signal,
        feedback_by_source=feedback_by_source,
        avg_feedback_per_chunk=round(avg_feedback, 2),
        chunks_with_feedback=chunks_with_feedback,
        chunks_without_feedback=chunks_without_feedback,
        promotion_candidates=promotion_candidates,
        high_conflict_chunks=high_conflict
    )

# ============================================================
# INTENTION INTEGRATION
# ============================================================

def enrich_with_intentions(chunks: List[Dict], driver) -> List[Dict]:
    """
    Run intention_gate logic and add scores to chunks.
    
    NOTE: This imports intention_gate module. Make sure it's in path.
    """
    try:
        # Import intention gate functions
        sys.path.insert(0, str(Path(__file__).parent))
        from intention_gate import calculate_scores, suggest_action
        
        for chunk in chunks:
            # Prepare feedback in expected format
            feedback = [
                {
                    "signal": f["signal"],
                    "strength": f["strength"],
                    "source": f["source"],
                    "timestamp": f["timestamp"]
                }
                for f in chunk["feedback"]
            ]
            
            # Calculate scores
            scores = calculate_scores(feedback, chunk["created_at"])
            
            # Get suggestion
            suggestion = suggest_action(
                chunk["chunk_id"],
                chunk["memory_class"],
                scores,
                chunk["created_at"],
                chunk["manual_feedback_count"]
            )
            
            # Add to chunk
            chunk["importance"] = scores["importance"]
            chunk["uncertainty"] = scores["uncertainty"]
            chunk["confidence"] = scores["confidence"]
            chunk["conflict"] = scores["conflict"]
            chunk["risk"] = scores["risk"]
            chunk["suggested_action"] = suggestion["action"]
        
        return chunks
    
    except ImportError as e:
        print(f"⚠️  Could not import intention_gate: {e}")
        print("   Skipping intention enrichment")
        return chunks

# ============================================================
# EXPORT FUNCTIONS
# ============================================================

def export_jsonl(chunks: List[Dict], feedback: List[Dict], concepts: List[Dict], 
                 output_path: Path, stats: ExportStats):
    """Export to JSONL (one JSON object per line)"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        # Write metadata
        f.write(json.dumps({"_meta": asdict(stats)}) + '\n')
        
        # Write chunks
        for chunk in chunks:
            f.write(json.dumps({"type": "chunk", "data": chunk}) + '\n')
        
        # Write feedback
        for fb in feedback:
            f.write(json.dumps({"type": "feedback", "data": fb}) + '\n')
        
        # Write concepts
        for concept in concepts:
            f.write(json.dumps({"type": "concept", "data": concept}) + '\n')
    
    print(f"✅ Exported to JSONL: {output_path}")
    print(f"   {len(chunks)} chunks, {len(feedback)} feedback, {len(concepts)} concepts")

def export_csv(chunks: List[Dict], output_path: Path):
    """Export chunks to CSV (simplified, flattened)"""
    import csv
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        fieldnames = [
            "chunk_id", "doc_id", "text", "memory_class", "created_at",
            "feedback_count", "positive_count", "negative_count", "uncertain_count",
            "manual_feedback_count", "concept_count",
            "importance", "uncertainty", "confidence", "conflict", "risk", "suggested_action"
        ]
        
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for chunk in chunks:
            row = {k: chunk.get(k) for k in fieldnames}
            # Convert lists to string
            if isinstance(row.get("conflict"), bool):
                row["conflict"] = str(row["conflict"])
            writer.writerow(row)
    
    print(f"✅ Exported to CSV: {output_path}")
    print(f"   {len(chunks)} chunks")

def export_parquet(chunks: List[Dict], feedback: List[Dict], output_path: Path):
    """Export to Parquet (requires pyarrow)"""
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        print("❌ pyarrow not installed. Install with: pip install pyarrow")
        return
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert chunks to table
    chunk_records = []
    for c in chunks:
        record = {
            "chunk_id": c["chunk_id"],
            "doc_id": c["doc_id"],
            "text": c["text"],
            "memory_class": c["memory_class"],
            "created_at": c["created_at"],
            "feedback_count": c["feedback_count"],
            "positive_count": c["positive_count"],
            "negative_count": c["negative_count"],
            "uncertain_count": c["uncertain_count"],
            "manual_feedback_count": c["manual_feedback_count"],
            "concept_count": c["concept_count"],
            "importance": c.get("importance"),
            "uncertainty": c.get("uncertainty"),
            "confidence": c.get("confidence"),
            "conflict": c.get("conflict"),
            "risk": c.get("risk"),
            "suggested_action": c.get("suggested_action")
        }
        chunk_records.append(record)
    
    chunk_table = pa.Table.from_pylist(chunk_records)
    
    # Write chunks
    chunk_path = output_path.parent / (output_path.stem + "_chunks.parquet")
    pq.write_table(chunk_table, chunk_path)
    print(f"✅ Exported chunks to Parquet: {chunk_path}")
    
    # Write feedback
    if feedback:
        feedback_table = pa.Table.from_pylist(feedback)
        feedback_path = output_path.parent / (output_path.stem + "_feedback.parquet")
        pq.write_table(feedback_table, feedback_path)
        print(f"✅ Exported feedback to Parquet: {feedback_path}")

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Export training data from Private knowledge graph")
    
    parser.add_argument("--format", choices=["jsonl", "csv", "parquet"], default="jsonl",
                       help="Export format")
    parser.add_argument("--output", type=str,
                       help="Output file path (default: auto-generated in symbiose_gnn_output/)")
    parser.add_argument("--include-intentions", action="store_true",
                       help="Run intention_gate and include scores")
    parser.add_argument("--stats-only", action="store_true",
                       help="Print statistics only, no export")
    
    args = parser.parse_args()
    
    # Generate default output path
    if not args.output:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"training_export_{timestamp}.{args.format}"
        output_path = DEFAULT_OUTPUT_DIR / filename
    else:
        output_path = Path(args.output)
    
    # Connect to Neo4j
    driver = GraphDatabase.driver(
        NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
    )
    
    try:
        print("📊 Fetching data from Neo4j...")
        
        # Fetch all data
        chunks = fetch_all_chunks(driver)
        feedback = fetch_all_feedback(driver)
        concepts = fetch_all_concepts(driver)
        
        print(f"   Found: {len(chunks)} chunks, {len(feedback)} feedback, {len(concepts)} concepts")
        
        # Calculate statistics
        stats = calculate_stats(chunks, feedback)
        stats.total_concepts = len(concepts)
        
        # Enrich with intentions if requested
        if args.include_intentions and chunks:
            print("🎯 Calculating intention scores...")
            chunks = enrich_with_intentions(chunks, driver)
        
        # Print statistics
        print("\n📈 Export Statistics:")
        print("=" * 60)
        print(f"Total chunks: {stats.total_chunks}")
        print(f"Total feedback: {stats.total_feedback}")
        print(f"Total concepts: {stats.total_concepts}")
        print(f"\nChunks by class:")
        for cls, count in stats.chunks_by_class.items():
            print(f"  {cls}: {count}")
        print(f"\nFeedback by signal:")
        for signal, count in stats.feedback_by_signal.items():
            print(f"  {signal}: {count}")
        print(f"\nFeedback by source:")
        for source, count in stats.feedback_by_source.items():
            print(f"  {source}: {count}")
        print(f"\nChunks with feedback: {stats.chunks_with_feedback}")
        print(f"Chunks without feedback: {stats.chunks_without_feedback}")
        print(f"Avg feedback per chunk: {stats.avg_feedback_per_chunk}")
        print(f"\nPromotion candidates: {stats.promotion_candidates}")
        print(f"High conflict chunks: {stats.high_conflict_chunks}")
        
        # Export if not stats-only
        if not args.stats_only:
            print(f"\n💾 Exporting to {args.format.upper()}...")
            
            if args.format == "jsonl":
                export_jsonl(chunks, feedback, concepts, output_path, stats)
            elif args.format == "csv":
                export_csv(chunks, output_path)
            elif args.format == "parquet":
                export_parquet(chunks, feedback, output_path)
            
            print(f"\n✅ Export complete: {output_path}")
        else:
            print("\n✅ Statistics generated (no export)")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        driver.close()
