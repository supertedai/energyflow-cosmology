#!/usr/bin/env python3
"""
Quality Control: Clean Qdrant + Prepare for Production

Gjør:
1. Fjerner test-dokumenter fra Qdrant
2. Verifiserer metadata-struktur
3. Rapporterer hva som må re-ingestas med node_id
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Load .env from repo root
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "efc")


def log(msg: str):
    print(f"[quality] {msg}", flush=True)


def get_client():
    if not QDRANT_URL or not QDRANT_API_KEY:
        raise RuntimeError("QDRANT_URL/API_KEY mangler")
    return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)


def remove_test_documents(client: QdrantClient):
    """Fjern test-dokumenter fra Qdrant."""
    log("🧹 Fjerner test-dokumenter...")
    
    # Get all points with source starting with "test/"
    test_sources = ["test/", "Test/", "TEST/"]
    removed_count = 0
    
    for test_prefix in test_sources:
        try:
            # Scroll to find test documents
            points, _ = client.scroll(
                collection_name=QDRANT_COLLECTION,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="source",
                            match=MatchValue(value=test_prefix)
                        )
                    ]
                ),
                limit=1000,
                with_payload=True,
                with_vectors=False
            )
            
            if points:
                # Delete by IDs
                ids_to_delete = [str(p.id) for p in points]
                client.delete(
                    collection_name=QDRANT_COLLECTION,
                    points_selector=ids_to_delete
                )
                removed_count += len(ids_to_delete)
                log(f"  ❌ Fjernet {len(ids_to_delete)} punkter med prefix '{test_prefix}'")
        
        except Exception as e:
            log(f"  ⚠️  Feil ved sletting av '{test_prefix}': {e}")
    
    if removed_count == 0:
        log("  ✅ Ingen test-dokumenter funnet")
    else:
        log(f"  ✅ Totalt fjernet: {removed_count} test-punkter")
    
    return removed_count


def analyze_metadata_quality(client: QdrantClient):
    """Analyser metadata-kvalitet i eksisterende data."""
    log("\n📊 Analyserer metadata-kvalitet...")
    
    # Sample 100 points
    points, _ = client.scroll(
        collection_name=QDRANT_COLLECTION,
        limit=100,
        with_payload=True,
        with_vectors=False
    )
    
    stats = {
        "total": len(points),
        "with_node_id": 0,
        "with_layer": 0,
        "with_doi": 0,
        "with_title": 0,
        "sources": set(),
        "layers": set()
    }
    
    for p in points:
        payload = p.payload or {}
        
        if payload.get("node_id"):
            stats["with_node_id"] += 1
        if payload.get("layer"):
            stats["with_layer"] += 1
            stats["layers"].add(payload["layer"])
        if payload.get("doi"):
            stats["with_doi"] += 1
        if payload.get("title"):
            stats["with_title"] += 1
        
        source = payload.get("source", "")
        if source:
            # Get top-level directory
            parts = source.split("/")
            if parts:
                stats["sources"].add(parts[0])
    
    log(f"\n  Totalt punkter (sample): {stats['total']}")
    log(f"  Med node_id:    {stats['with_node_id']} ({stats['with_node_id']/stats['total']*100:.1f}%)")
    log(f"  Med layer:      {stats['with_layer']} ({stats['with_layer']/stats['total']*100:.1f}%)")
    log(f"  Med doi:        {stats['with_doi']} ({stats['with_doi']/stats['total']*100:.1f}%)")
    log(f"  Med title:      {stats['with_title']} ({stats['with_title']/stats['total']*100:.1f}%)")
    
    log(f"\n  Kilder (topp-nivå): {sorted(stats['sources'])}")
    log(f"  Layers funnet: {sorted(stats['layers']) if stats['layers'] else 'ingen'}")
    
    # Recommendation
    if stats["with_node_id"] == 0:
        log("\n  ⚠️  ANBEFALING: Ingen punkter har node_id")
        log("     → Kjør re-ingest med Neo4j bridge for full hybrid scoring")
    elif stats["with_node_id"] < stats["total"] * 0.5:
        log(f"\n  ⚠️  ANBEFALING: Kun {stats['with_node_id']}/{stats['total']} har node_id")
        log("     → Vurder re-ingest for konsistens")
    else:
        log(f"\n  ✅ God node_id-dekning: {stats['with_node_id']}/{stats['total']}")
    
    return stats


def get_collection_stats(client: QdrantClient):
    """Hent collection-statistikk."""
    log("\n📈 Collection-statistikk:")
    
    try:
        info = client.get_collection(collection_name=QDRANT_COLLECTION)
        log(f"  Totalt vektorer: {info.points_count}")
        log(f"  Vektor-dimensjon: {info.config.params.vectors.size}")
        log(f"  Distance metric: {info.config.params.vectors.distance}")
    except Exception as e:
        log(f"  ⚠️  Kunne ikke hente stats: {e}")


def main():
    log("="*60)
    log("🧹 QUALITY CONTROL: Qdrant Cleanup & Analysis")
    log("="*60 + "\n")
    
    client = get_client()
    
    # 1. Remove test documents
    removed = remove_test_documents(client)
    
    # 2. Analyze metadata quality
    stats = analyze_metadata_quality(client)
    
    # 3. Collection stats
    get_collection_stats(client)
    
    log("\n" + "="*60)
    log("✅ Quality check complete")
    log("="*60 + "\n")
    
    # Final recommendations
    log("📋 NEXT STEPS:\n")
    
    if stats["with_node_id"] == 0:
        log("  1. 🔗 Re-ingest med Neo4j bridge:")
        log("     NEO4J_URI=... python tools/rag_ingest_repo.py")
        log("")
    
    log("  2. ✅ Test hybrid search:")
    log("     curl 'http://localhost:8000/graph-rag/search?query=energy+flow&use_gnn=true&alpha=0.7'")
    log("")
    
    log("  3. 📊 Verifiser strukturell scoring:")
    log("     python tools/test_gnn_bridge.py")


if __name__ == "__main__":
    main()
