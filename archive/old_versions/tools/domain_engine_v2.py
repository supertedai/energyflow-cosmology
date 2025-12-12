#!/usr/bin/env python3
"""
domain_engine_v2.py - Optimized Semantic Field Analysis
=======================================================

CRITICAL IMPROVEMENTS:
1. Proper GNN integration (no duplicate logic)
2. Thread-safe caching with LRU
3. Word-boundary keyword matching
4. Domain-aware GNN calls
5. Entropy threshold for short texts
6. Configurable EFC weights
7. Robust error handling
8. Embedding cache to save API calls

Purpose:
    Analyze text for:
    - Semantic embedding
    - Information entropy
    - Domain/cognitive field classification  
    - EFC relevance
    - GNN structural score (if available)
    - Full JSONL logging

Usage:
    from domain_engine_v2 import analyze_semantic_field

    result = analyze_semantic_field(
        text="The entropy gradient drives cosmic evolution",
        source="chat",
        session_id="session-123"
    )
"""

import os
import sys
import json
import math
import hashlib
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from functools import lru_cache

import numpy as np
from dotenv import load_dotenv
import openai

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

DOMAIN_ENGINE_LOG = Path("symbiose_gnn_output/domain_engine_log.jsonl")

# Configurable weights
EFC_SEMANTIC_WEIGHT = float(os.getenv("EFC_SEMANTIC_WEIGHT", "0.7"))
EFC_GNN_WEIGHT = float(os.getenv("EFC_GNN_WEIGHT", "0.3"))
MIN_TOKENS_FOR_ENTROPY = int(os.getenv("MIN_TOKENS_FOR_ENTROPY", "10"))

# ============================================================
# DOMAIN DEFINITIONS
# ============================================================

DOMAINS: List[Dict[str, Any]] = [
    {
        "id": "cosmology",
        "label": "Cosmology & EFC",
        "weight": 1.3,
        "keywords": [
            "entropy", "entropi", "energy-flow", "energy flow",
            "efc", "grid-higgs", "halo", "cmb", "cosmology",
            "kosmologi", "hubble", "redshift", "entropic field",
            "spacetime", "space-time", "cosmic microwave background"
        ],
        "examples": [
            "Energy-Flow Cosmology",
            "Grid-Higgs Framework",
            "entropy gradient in cosmology",
            "cosmic evolution driven by entropy"
        ]
    },
    {
        "id": "thermo_energy",
        "label": "Thermodynamics & Energisystemer",
        "weight": 1.1,
        "keywords": [
            "varmeveksler", "røykgass", "biodiesel",
            "mw", "kjelen", "kjel", "delta t", "temperatur",
            "effekt", "energisystem", "varmetap", "heat exchanger"
        ],
        "examples": [
            "beregne effekt fra røykgass",
            "MW-estimat fra varmeveksler",
            "termisk energi og entropi i rør"
        ]
    },
    {
        "id": "ai_symbiosis",
        "label": "AI, Symbiose & Arkitektur",
        "weight": 1.2,
        "keywords": [
            "symbiose", "neo4j", "qdrant", "rag",
            "gnn", "intention layer", "memory class",
            "feedback", "steering layer", "orchestrator",
            "mcp", "agent", "multi-agent",
            "embedding", "vectorstore", "llm"
        ],
        "examples": [
            "intention layer for AGI",
            "multi agent symbiose",
            "gnn for structural stability",
            "feedback-driven memory reclassification"
        ]
    },
    {
        "id": "security_net",
        "label": "Sikkerhet & Nettverksherding",
        "weight": 1.1,
        "keywords": [
            "pfsense", "wazuh", "suricata", "snort",
            "firewall", "vpn", "wireguard",
            "dns tunneling", "doh", "quic", "ids",
            "ips", "honeypot", "apparmor",
            "rate limiting", "pfblocker", "exfil"
        ],
        "examples": [
            "dns exfiltration detection",
            "pfsense vlan segmentering",
            "suricata på nordlynx interface"
        ]
    },
    {
        "id": "networking_protocols",
        "label": "Networking & Protokoller",
        "weight": 1.0,
        "keywords": [
            "dns", "tls", "tcp", "udp", "quic",
            "latency", "bandwidth", "dpi", "mtu"
        ],
        "examples": [
            "analyse av dns-resolver",
            "tls fingerprint og klientprofil"
        ]
    },
    {
        "id": "economy_risk",
        "label": "Økonomi & Risiko",
        "weight": 0.9,
        "keywords": [
            "risiko", "risk", "roi", "kostnad",
            "avkastning", "sannsynlighet", "scenario",
            "økonomi", "cash flow", "investering"
        ],
        "examples": [
            "kostnytte for privat vs cloud",
            "risikomatrise for datasystem"
        ]
    },
    {
        "id": "psychology_cog",
        "label": "Psykologi & Kognisjon",
        "weight": 1.0,
        "keywords": [
            "ace", "traume", "kognitiv", "regulering",
            "resonans", "overveldelse", "meta-refleksjon",
            "ego", "tilstand", "trykk", "kapasitet"
        ],
        "examples": [
            "entropi-tilstand i nervesystem",
            "meta-refleksjon uten ego"
        ]
    },
    {
        "id": "system_design",
        "label": "Systemdesign & Infrastruktur",
        "weight": 0.9,
        "keywords": [
            "docker", "compose", "hetzner",
            "gpu", "threadripper", "nvme", "raid",
            "kubernetes", "cluster", "monitoring", "grafana"
        ],
        "examples": [
            "threadripper + multi gpu setup",
            "docker stack for neo4j og qdrant"
        ]
    },
    {
        "id": "language_logic",
        "label": "Språk, Logikk & Semantikk",
        "weight": 0.8,
        "keywords": [
            "semantikk", "logikk", "begrep", "konsept",
            "ontologi", "schema", "json-ld", "graph"
        ],
        "examples": [
            "modellere begrepsfelt i graph",
            "ontologi for efc data"
        ]
    },
    {
        "id": "geopolitics",
        "label": "Geopolitikk & Systemdynamikk",
        "weight": 0.8,
        "keywords": [
            "stat", "nasjon", "regjering", "etterretning",
            "militær", "kritisk infrastruktur", "energi",
            "maktdynamikk"
        ],
        "examples": [
            "agi og statlige sikkerhetssystemer",
            "kritiske infrastrukturer og risiko"
        ]
    },
    {
        "id": "personal",
        "label": "Personlig / Biografisk",
        "weight": 1.0,
        "keywords": [
            "jeg heter", "my name is", "gift med",
            "ektefelle", "bor i", "live in",
            "jobber med", "work at", "familie",
            "barn", "hjemme", "helse"
        ],
        "examples": [
            "jeg heter morten",
            "jeg er gift med elisabet"
        ]
    },
    {
        "id": "meta",
        "label": "Meta & Feltlogikk",
        "weight": 1.2,
        "keywords": [
            "meta", "felt", "resonans", "entropi i tanke",
            "singularitet", "speil", "metaspeil",
            "feltlogikk", "intensjon", "konvergens"
        ],
        "examples": [
            "feltbasert kognitiv resonans",
            "meta-lag som stabiliserer symbiose"
        ]
    },
]

# ============================================================
# ENTROPY ANALYSIS
# ============================================================

def _shannon_entropy(text: str) -> float:
    """Character-level Shannon entropy"""
    if not text:
        return 0.0
    freq = {}
    for ch in text:
        freq[ch] = freq.get(ch, 0) + 1
    total = len(text)
    entropy = 0.0
    for count in freq.values():
        p = count / total
        entropy -= p * math.log2(p)
    return entropy


def _token_entropy(text: str) -> float:
    """Token-level entropy (only meaningful for longer texts)"""
    tokens = text.split()
    if len(tokens) < MIN_TOKENS_FOR_ENTROPY:
        return 0.0  # Not meaningful for short text
    
    freq = {}
    for t in tokens:
        t_norm = t.strip().lower()
        freq[t_norm] = freq.get(t_norm, 0) + 1
    
    entropy = 0.0
    for count in freq.values():
        p = count / len(tokens)
        entropy -= p * math.log2(p)
    return entropy


def _entropy_features(text: str) -> Dict[str, float]:
    """Extract entropy features from text"""
    char_ent = _shannon_entropy(text)
    tok_ent = _token_entropy(text)
    length = len(text)
    token_count = len(text.split()) if text else 0
    density = token_count / max(1, length)

    return {
        "char_entropy": round(char_ent, 4),
        "token_entropy": round(tok_ent, 4),
        "length": length,
        "token_count": token_count,
        "token_density": round(density, 4),
    }

# ============================================================
# EMBEDDINGS (with caching)
# ============================================================

# Cache for text embeddings
_EMBEDDING_CACHE: Dict[str, np.ndarray] = {}

def _get_embedding(text: str) -> np.ndarray:
    """Get OpenAI embedding with caching"""
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")
    
    # Check cache first
    text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if text_hash in _EMBEDDING_CACHE:
        return _EMBEDDING_CACHE[text_hash]
    
    # Call API
    resp = openai.embeddings.create(
        model="text-embedding-3-large",
        input=text[:8000]
    )
    emb = np.array(resp.data[0].embedding, dtype=np.float32)
    
    # Cache result
    _EMBEDDING_CACHE[text_hash] = emb
    return emb


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity"""
    if a is None or b is None:
        return 0.0
    an = np.linalg.norm(a)
    bn = np.linalg.norm(b)
    if an == 0 or bn == 0:
        return 0.0
    return float(np.dot(a, b) / (an * bn))

# ============================================================
# DOMAIN EMBEDDINGS (thread-safe caching)
# ============================================================

@lru_cache(maxsize=20)
def _get_domain_embedding(examples_tuple: Tuple[str, ...]) -> np.ndarray:
    """Get domain prototype embedding (cached)"""
    text = "; ".join(examples_tuple)
    return _get_embedding(text)


def _get_domain_embedding_for_id(domain_id: str) -> Optional[np.ndarray]:
    """Get cached embedding for domain by ID"""
    dom = next((d for d in DOMAINS if d["id"] == domain_id), None)
    if not dom:
        return None
    
    examples = dom.get("examples", [])
    if not examples:
        return None
    
    # Convert to tuple for hashable caching
    return _get_domain_embedding(tuple(examples))

# ============================================================
# GNN INTEGRATION (proper domain-aware)
# ============================================================

def _gnn_structural_signal(text: str, domain_id: str) -> Dict[str, Any]:
    """
    Get GNN structural score with domain awareness.
    
    FIXED: Now passes domain_id to gnn_scoring so it can skip appropriately.
    """
    try:
        from tools.gnn_scoring import get_gnn_similarity_score
    except Exception:
        return {
            "available": False,
            "gnn_similarity": 0.0,
            "gnn_confidence": 0.0,
            "top_matches": [],
            "reason": "gnn_scoring not available"
        }

    try:
        # FIXED: Pass domain to GNN for proper skip logic
        res = get_gnn_similarity_score(
            private_chunk_text=text,
            top_k=5,
            chunk_domain=domain_id  # ✅ Domain-aware!
        )
        return {
            "available": res.get("available", False),
            "gnn_similarity": res.get("gnn_similarity", 0.0),
            "gnn_confidence": res.get("confidence", 0.0),
            "top_matches": res.get("top_matches", []),
            "reason": res.get("reason", None)
        }
    except Exception as e:
        return {
            "available": False,
            "gnn_similarity": 0.0,
            "gnn_confidence": 0.0,
            "top_matches": [],
            "reason": f"gnn error: {e}"
        }

# ============================================================
# KEYWORD MATCHING (word-boundary aware)
# ============================================================

def _keyword_boost(text_lower: str, keywords: List[str]) -> float:
    """
    FIXED: Use word-boundary regex to avoid false matches.
    
    Examples:
        "cosmology" matches "cosmology" but not "cosmo" in "because"
        "meta" matches "meta" but not in "metadata"
    """
    score = 0.0
    for kw in keywords:
        # Word boundary check
        pattern = r'\b' + re.escape(kw) + r'\b'
        if re.search(pattern, text_lower):
            score += 0.05
    return min(score, 0.3)  # Cap boost

# ============================================================
# DOMAIN SCORING
# ============================================================

def _compute_domain_scores(text: str, text_emb: np.ndarray) -> Dict[str, Dict[str, Any]]:
    """Compute scores for all domains"""
    t_lower = text.lower()
    scores: Dict[str, Dict[str, Any]] = {}

    for dom in DOMAINS:
        dom_id = dom["id"]
        dom_emb = _get_domain_embedding_for_id(dom_id)
        
        if dom_emb is None:
            sim = 0.0
        else:
            sim = _cosine(text_emb, dom_emb)

        kw_boost = _keyword_boost(t_lower, dom.get("keywords", []))
        raw = sim + kw_boost
        weighted = raw * dom.get("weight", 1.0)

        scores[dom_id] = {
            "id": dom_id,
            "label": dom["label"],
            "similarity": round(sim, 4),
            "keyword_boost": round(kw_boost, 4),
            "weighted_score": round(weighted, 4),
        }

    return scores


def _select_primary_domain(domain_scores: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Select primary domain with confidence"""
    if not domain_scores:
        return {
            "primary_domain": None,
            "primary_score": 0.0,
            "confidence": 0.0
        }

    sorted_scores = sorted(
        domain_scores.values(),
        key=lambda x: x["weighted_score"],
        reverse=True
    )
    best = sorted_scores[0]
    second = sorted_scores[1] if len(sorted_scores) > 1 else {"weighted_score": 0.0}

    diff = best["weighted_score"] - second["weighted_score"]
    confidence = max(0.0, min(1.0, best["weighted_score"] + diff))

    return {
        "primary_domain": best["id"],
        "primary_label": best["label"],
        "primary_score": best["weighted_score"],
        "confidence": round(confidence, 4)
    }

# ============================================================
# EFC RELEVANCE (configurable weights)
# ============================================================

def _efc_relevance(
    domain_scores: Dict[str, Dict[str, Any]],
    gnn_signal: Dict[str, Any],
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    FIXED: Configurable weights for semantic vs GNN.
    
    Default: 70% semantic, 30% GNN (from environment or hardcoded)
    """
    w = weights or {"semantic": EFC_SEMANTIC_WEIGHT, "gnn": EFC_GNN_WEIGHT}
    
    base = domain_scores.get("cosmology", {}).get("weighted_score", 0.0)
    gnn_sim = gnn_signal.get("gnn_similarity", 0.0) if gnn_signal.get("available") else 0.0

    score = w["semantic"] * base + w["gnn"] * gnn_sim
    return round(max(0.0, min(1.0, score)), 4)

# ============================================================
# LOGGING (robust error handling)
# ============================================================

def _text_hash(text: str) -> str:
    """Generate hash for text"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _log_analysis(record: Dict[str, Any]) -> None:
    """
    FIXED: Robust logging with error handling.
    
    Fails silently if disk full or permission denied.
    """
    try:
        DOMAIN_ENGINE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(DOMAIN_ENGINE_LOG, "a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        # Fail-silent for logging
        print(f"⚠️  Failed to log domain analysis: {e}", file=sys.stderr)

# ============================================================
# MAIN FUNCTION
# ============================================================

def analyze_semantic_field(
    text: str,
    source: str = "chat",
    session_id: Optional[str] = None,
    chunk_id: Optional[str] = None,
    document_id: Optional[str] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
    efc_weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Main entry: analyze text for domain/field.

    Returns:
        {
            "entropy_features": {...},
            "domain_scores": {...},
            "primary_domain": str,
            "primary_domain_confidence": float,
            "efc_relevance": float,
            "gnn": {...}
        }
    
    Logs to domain_engine_log.jsonl.
    """
    if not text:
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "text_hash": None,
            "source": source,
            "session_id": session_id,
            "chunk_id": chunk_id,
            "document_id": document_id,
            "entropy": _entropy_features(text),
            "domain_scores": {},
            "primary_domain": None,
            "primary_domain_confidence": 0.0,
            "efc_relevance": 0.0,
            "gnn": {"available": False, "reason": "empty text"},
            "metadata": extra_metadata or {}
        }
        _log_analysis(result)
        return result

    # Entropy
    ent = _entropy_features(text)

    # Embedding
    emb = _get_embedding(text)

    # Domain scores
    domain_scores = _compute_domain_scores(text, emb)
    dom_sel = _select_primary_domain(domain_scores)
    
    primary_domain = dom_sel.get("primary_domain")

    # GNN signal (domain-aware)
    gnn_sig = _gnn_structural_signal(text, primary_domain or "unknown")

    # EFC relevance
    efc_rel = _efc_relevance(domain_scores, gnn_sig, efc_weights)

    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "source": source,
        "session_id": session_id,
        "chunk_id": chunk_id,
        "document_id": document_id,
        "text_hash": _text_hash(text),
        "entropy": ent,
        "domain_scores": domain_scores,
        "primary_domain": primary_domain,
        "primary_domain_label": dom_sel.get("primary_label"),
        "primary_domain_score": dom_sel.get("primary_score"),
        "primary_domain_confidence": dom_sel.get("confidence"),
        "efc_relevance": efc_rel,
        "gnn": gnn_sig,
        "metadata": extra_metadata or {}
    }

    # Log
    _log_analysis(record)

    return record

# ============================================================
# CLI TESTING
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Domain Engine v2 - Optimized")
    parser.add_argument("--text", help="Text to analyze")
    parser.add_argument("--file", help="File with text")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    if not args.text and not args.file:
        parser.print_help()
        sys.exit(0)

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = args.text

    result = analyze_semantic_field(text=text, source="cli")

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"\n=== Domain Engine v2 Result ===")
        print(f"Primary: {result['primary_domain_label']} ({result['primary_domain']})")
        print(f"Score: {result['primary_domain_score']}, Confidence: {result['primary_domain_confidence']}")
        print(f"EFC relevance: {result['efc_relevance']}")
        print(f"Entropy: char={result['entropy']['char_entropy']}, token={result['entropy']['token_entropy']}")
        
        print("\nTop domains:")
        for dom in sorted(result["domain_scores"].values(),
                          key=lambda x: x["weighted_score"], reverse=True)[:5]:
            print(f"  {dom['label']}: {dom['weighted_score']}")
        
        if result["gnn"]["available"]:
            print(f"\nGNN: {result['gnn']['gnn_similarity']} (conf: {result['gnn']['gnn_confidence']})")
