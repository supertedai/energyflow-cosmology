#!/usr/bin/env python3
"""
efc_theory_engine.py - Energy Flow Cosmology Theory Engine
==========================================================

EFC som informasjonsteoretisk motor.

Denne modulen er et *privat* domene-lag for:
- å tolke spørsmål i EFC-domenet
- å vurdere påstander opp mot EFC-postulater
- å hente strukturell kontekst fra Neo4j
- å gi anbefalinger til AME/DDE om hvordan EFC skal brukes

Viktig:
- Ingen eksterne kall
- Jobber kun mot:
  - CanonicalMemoryCore (CMC)
  - SemanticMeshMemory (SMM)
  - Neo4jGraphLayer (struktur)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Literal

# -------------------------------------------------------------------
# Avhengigheter (lokale, private)
# -------------------------------------------------------------------

try:
    from tools.canonical_memory_core import CanonicalMemoryCore, CanonicalFact
    from tools.semantic_mesh_memory import SemanticMeshMemory, ContextChunk
    from tools.neo4j_graph_layer import Neo4jGraphLayer
except ImportError:
    CanonicalMemoryCore = Any  # type: ignore
    CanonicalFact = Any        # type: ignore
    SemanticMeshMemory = Any   # type: ignore
    ContextChunk = Any         # type: ignore
    Neo4jGraphLayer = Any      # type: ignore

# Adaptive learning import (separate to avoid issues)
try:
    from efc_pattern_learner import EFCPatternLearner
    LEARNER_AVAILABLE = True
except ImportError as e:
    try:
        from tools.efc_pattern_learner import EFCPatternLearner
        LEARNER_AVAILABLE = True
    except ImportError:
        EFCPatternLearner = Any    # type: ignore
        LEARNER_AVAILABLE = False


# -------------------------------------------------------------------
# Datatyper
# -------------------------------------------------------------------

EFCMode = Literal[
    "PURE_EFC",          # bruk kun EFC som sannhetsgrunnlag
    "COMPARE_WITH_LCDM", # forklar forskjell mot standardmodeller
    "EXPLAIN_EFC",       # pedagogisk, ikke hard-konklusiv
    "OUT_OF_SCOPE"       # ikke egentlig et EFC-spørsmål
]


@dataclass
class EFCPrinciple:
    """Ett kjerneprinsipp i EFC."""
    key: str
    title: str
    description: str
    weight: float = 1.0  # hvor sentralt prinsippet er


@dataclass
class EFCClaimCheck:
    """Resultat av å sjekke en påstand mot EFC."""
    is_consistent: bool
    confidence: float
    violated_principles: List[str] = field(default_factory=list)
    supporting_principles: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class EFCInferenceMode:
    """Hvordan systemet bør bruke EFC i et gitt spørsmål."""
    mode: EFCMode
    confidence: float
    reasons: List[str] = field(default_factory=list)


@dataclass
class EFCGraphContext:
    """Strukturell kontekst hentet fra Neo4j."""
    related_nodes: List[Dict[str, Any]] = field(default_factory=list)
    paths: List[List[str]] = field(default_factory=list)
    notes: str = ""


@dataclass
class EFCPatternRelevance:
    """
    Vurdering av om EFC-logikk er relevant for et spørsmål.
    
    Dette er ikke domene-deteksjon - det er pattern-matching.
    EFC kan være relevant i kosmologi, biologi, AI, psykologi, økonomi, etc.
    """
    score: float
    relevance_level: Literal["OUT_OF_SCOPE", "WEAK_SIGNAL", "EFC_ENABLED", "PURE_EFC"]
    language_cues: int
    structural_cues: int
    logical_cues: int
    detected_patterns: List[str] = field(default_factory=list)
    reasoning: str = ""


# -------------------------------------------------------------------
# Selve motoren
# -------------------------------------------------------------------

class EFCTheoryEngine:
    """
    Energy Flow Cosmology som informasjonsteoretisk motor.

    Denne klassen skal:
    - tolke om et spørsmål hører hjemme i EFC
    - gi en anbefalt modus (PURE_EFC / COMPARE / EXPLAIN / OUT_OF_SCOPE)
    - sjekke påstander mot kjerneprinsipper
    - hente grafkontekst for EFC-relaterte begreper
    - **VIKTIGST: Pattern Detection** - oppdage når EFC-logikk gjelder,
      uavhengig av domene (fungerer i kosmologi, AI, biologi, økonomi, etc.)
    """

    # Pattern detection: Language cues
    # Ord som peker mot EFC-relevante konsepter på tvers av domener
    LANGUAGE_CUES = [
        "stabil", "ustabil", "balanse", "metastabil",
        "flow", "flux", "gradient", "felt", "energi",
        "dynamikk", "emergens", "mønster", "struktur",
        "driver", "drivkraft", "stabiliserer", "organiserer",
        "retning", "spenning", "trykk", "ubalanse",
        "entropi", "entropy", "entropic", "entropisk",
        "system", "systemisk", "halo", "field", "potential",
    ]
    
    # Logical cues: phrases indicating EFC-type reasoning
    LOGICAL_PATTERNS = [
        "hvorfor.*stabiliserer",
        "hvordan oppstår",
        "hva driver",
        "hvorfor.*organiserer",
        "hvorfor.*mønster",
        "hvorfor.*struktur",
        "hvorfor.*emergent",
        "hva får.*til å",
        "hvorfor.*finner.*minimum",
        "hvorfor.*retning",
        "why.*stabilize",
        "how.*emerge",
        "what drives",
        "why.*organize",
        "why.*pattern",
    ]

    def __init__(
        self,
        cmc: Optional[CanonicalMemoryCore] = None,
        smm: Optional[SemanticMeshMemory] = None,
        graph: Optional[Neo4jGraphLayer] = None,
        enable_learning: bool = True,
        learning_file: str = "efc_pattern_learning.json"
    ):
        self.cmc = cmc
        self.smm = smm
        self.graph = graph

        # Definerer kjerneprinsipper i EFC
        self.principles: Dict[str, EFCPrinciple] = self._load_core_principles()
        
        # Adaptive learning system
        self.enable_learning = enable_learning
        self.learner = None
        if enable_learning and LEARNER_AVAILABLE:
            try:
                self.learner = EFCPatternLearner(learning_file=learning_file)
            except Exception as e:
                print(f"⚠️  Could not initialize learner: {e}")
                self.learner = None

    # ------------------------------------------------------------------
    # Kjerneprinsipper
    # ------------------------------------------------------------------

    def _load_core_principles(self) -> Dict[str, EFCPrinciple]:
        """
        Lokal definisjon av EFC-prinsipper.
        Dette bør etter hvert også ligge i CMC som canonical facts.
        """
        principles = {
            "NO_DARK_MATTER": EFCPrinciple(
                key="NO_DARK_MATTER",
                title="Ingen egen mørk materie-komponent",
                description=(
                    "Observasjoner som tilskrives mørk materie forklares som "
                    "emergente effekter av energiflyt, entropi og strukturelle haloer."
                ),
                weight=1.0,
            ),
            "NO_DARK_ENERGY": EFCPrinciple(
                key="NO_DARK_ENERGY",
                title="Ingen separat mørk energi",
                description=(
                    "Akselerasjon og ekspansjon forstås som resultat av "
                    "entropigradienter og energifordeling, ikke en kosmologisk konstant."
                ),
                weight=1.0,
            ),
            "GRID_MEDIUM": EFCPrinciple(
                key="GRID_MEDIUM",
                title="Kontinuerlig grid-medium",
                description=(
                    "Universet modelleres som et kontinuerlig energigrid, ikke tomt rom "
                    "med diskrete objekter på toppen."
                ),
                weight=1.0,
            ),
            "ENTROPY_DRIVEN": EFCPrinciple(
                key="ENTROPY_DRIVEN",
                title="Entropidrevne prosesser",
                description=(
                    "Struktur, haloer, rotasjonskurver og storskala-mønstre oppstår fra "
                    "entropigradienter og energiflyt, ikke fra skjulte masser."
                ),
                weight=1.0,
            ),
            "SCALE_CONTINUITY": EFCPrinciple(
                key="SCALE_CONTINUITY",
                title="Skalakontinuitet",
                description=(
                    "Samme grunnlogikk for energiflyt gjelder på tvers av skalaer "
                    "(galakse, halo, klynger, kosmisk web)."
                ),
                weight=0.8,
            ),
            "EMERGENT_GRAVITY": EFCPrinciple(
                key="EMERGENT_GRAVITY",
                title="Gravitasjon som emergent fenomen",
                description=(
                    "Det vi kaller gravitasjon er et emergent resultat av energiflyt og "
                    "entropigradienter, ikke en grunnleggende kraft med egen partikkel."
                ),
                weight=0.9,
            ),
        }
        return principles

    def get_core_principles(self) -> List[EFCPrinciple]:
        """Returner alle kjerneprinsipper."""
        return list(self.principles.values())

    # ------------------------------------------------------------------
    # Domene-deteksjon
    # ------------------------------------------------------------------

    def is_efc_question(self, question: str) -> bool:
        """
        Grov sjekk: er dette sannsynligvis et EFC-spørsmål?

        Brukes av DDE / AME for å avgjøre om EFC skal aktiveres.
        """
        q = question.lower()

        # Nøkkelord som sterkt peker mot EFC
        hard_hits = [
            "energy flow hypothesis",
            "energy-flow cosmology",
            "grid-higgs",
            "grid higgs",
            "halo hypothesis",
            "entropy-light speed",
            "efc",
        ]

        # Mer generelle ord som ofte brukes i din EFC-kontekst
        soft_hits = [
            "entropi", "entropy",
            "halo",
            "grid",
            "emergent gravity",
            "mørk materie", "dark matter",
            "mørk energi", "dark energy",
            "hubble", "cmb",
            "rotation curve", "rotasjonskurve",
        ]

        if any(token in q for token in hard_hits):
            return True

        soft_count = sum(1 for token in soft_hits if token in q)
        return soft_count >= 2

    def infer_mode(
        self,
        question: str,
        active_domains: Optional[List[str]] = None
    ) -> EFCInferenceMode:
        """
        Foreslår hvordan EFC bør brukes for et gitt spørsmål.

        - PURE_EFC: når spørsmålet tydelig handler om din modell
        - COMPARE_WITH_LCDM: når spørsmålet ber om sammenlikning
        - EXPLAIN_EFC: når bruker spør "forklar", "hvordan fungerer"
        - OUT_OF_SCOPE: når EFC kun er bakgrunnsrelevant
        """
        q = question.lower()
        reasons: List[str] = []

        if active_domains and "cosmology" not in active_domains:
            return EFCInferenceMode(
                mode="OUT_OF_SCOPE",
                confidence=0.2,
                reasons=["Aktive domener inneholder ikke cosmology"],
            )

        if not self.is_efc_question(question):
            return EFCInferenceMode(
                mode="OUT_OF_SCOPE",
                confidence=0.3,
                reasons=["Spørsmålet matcher ikke EFC-mønstre"],
            )

        # Sammenlikningsspørsmål
        compare_tokens = ["vs", "versus", "kontra", "sammenlign", "compare"]
        if any(t in q for t in compare_tokens):
            return EFCInferenceMode(
                mode="COMPARE_WITH_LCDM",
                confidence=0.9,
                reasons=["Direkte sammenlikning etterspurt"],
            )

        if "lcdm" in q or "lambda cdm" in q or "standardmodell" in q:
            return EFCInferenceMode(
                mode="COMPARE_WITH_LCDM",
                confidence=0.85,
                reasons=["Standardmodeller nevnt eksplisitt"],
            )

        # Forklaringsmodus
        if any(t in q for t in ["forklar", "explain", "hvordan fungerer", "intuisjon"]):
            return EFCInferenceMode(
                mode="EXPLAIN_EFC",
                confidence=0.9,
                reasons=["Spørsmålet er eksplisitt forklarende"],
            )

        # Standard: ren EFC-bruk
        reasons.append("Spørsmål om kosmologi med EFC-begreper")
        return EFCInferenceMode(
            mode="PURE_EFC",
            confidence=0.8,
            reasons=reasons,
        )

    # ------------------------------------------------------------------
    # Påstands-sjekk mot prinsipper
    # ------------------------------------------------------------------

    def check_claim(self, claim_text: str) -> EFCClaimCheck:
        """
        Grov konsistenssjekk av en tekstlig påstand mot EFC-prinsipper.

        Dette er heuristisk og kvalitativt:
        - leter etter ord/fraser som strider mot eksplisitte postulat
        """
        text = claim_text.lower()
        violated: List[str] = []
        supporting: List[str] = []
        notes: List[str] = []

        # Mørk materie eksplisitt positivt omtalt
        if re.search(r"\bmørk materie\b", text) or "dark matter" in text:
            if any(t in text for t in ["nødvendig", "må", "kreves", "trengs", "er påkrevd"]):
                violated.append("NO_DARK_MATTER")
                notes.append("Påstand uttrykker DM som nødvendig komponent")

        # Mørk energi
        if re.search(r"\bmørk energi\b", text) or "dark energy" in text:
            if any(t in text for t in ["nødvendig", "må", "kreves", "trengs", "er påkrevd"]):
                violated.append("NO_DARK_ENERGY")
                notes.append("Påstand uttrykker DE som nødvendig komponent")

        # Grid / entropi / emergent gravity støttende
        if any(t in text for t in ["grid", "higgs", "energiflyt", "energy flow", "entropi", "entropy"]):
            supporting.append("ENTROPY_DRIVEN")
            supporting.append("GRID_MEDIUM")

        if "emergent gravity" in text or "emergens" in text:
            supporting.append("EMERGENT_GRAVITY")

        # Klassisk gravitasjon som grunnleggende kraft kan være i konflikt
        if "fundamental force" in text and "gravity" in text:
            violated.append("EMERGENT_GRAVITY")
            notes.append("Gravitasjon omtales som fundamental kraft, ikke emergent")

        # Grov vurdering
        if violated and not supporting:
            is_consistent = False
            confidence = 0.8
        elif violated and supporting:
            is_consistent = False
            confidence = 0.6
        elif supporting and not violated:
            is_consistent = True
            confidence = 0.8
        else:
            is_consistent = True
            confidence = 0.5
            notes.append("Ingen klare brudd eller støtte funnet")

        return EFCClaimCheck(
            is_consistent=is_consistent,
            confidence=confidence,
            violated_principles=violated,
            supporting_principles=list(set(supporting)),
            notes="; ".join(notes),
        )

    def suggest_rewrite(self, claim_text: str) -> str:
        """
        Enkel regelbasert omskriving for å gjøre påstand mer EFC-kompatibel.

        Dette er ren tekstlig justering – LLM kan senere gjøre dette rikere.
        """
        text = claim_text

        replacements = [
            # Dark matter
            (
                r"\bmørk materie\b",
                "det som i standardmodeller omtales som mørk materie, "
                "men som i EFC tolkes som emergente halo-effekter fra energiflyt"
            ),
            (
                r"\bdark matter\b",
                "what is called dark matter in standard models, "
                "but in EFC interpreted as emergent halo effects from energy flow"
            ),
            # Dark energy
            (
                r"\bmørk energi\b",
                "det som i standardmodeller omtales som mørk energi, men som i EFC "
                "tolkes som resultat av entropigradienter og energifordeling"
            ),
            (
                r"\bdark energy\b",
                "what is called dark energy in standard models, but in EFC "
                "understood as the result of entropy gradients and energy distribution"
            ),
        ]

        for pattern, repl in replacements:
            text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

        return text

    # ------------------------------------------------------------------
    # Graf-kontekst (Neo4j)
    # ------------------------------------------------------------------

    def graph_context_for(
        self,
        question: str,
        max_depth: int = 3
    ) -> Optional[EFCGraphContext]:
        """
        Hent strukturell EFC-kontekst fra Neo4j for et spørsmål.

        Forenklet versjon:
        - prøver å identifisere ett eller to sentrale begreper
        - finner naboer og eventuelle paths mellom dem
        """
        if not self.graph or not hasattr(self.graph, "driver") or self.graph.driver is None:
            return None

        q = question.lower()

        # Enkle "konsept-ord" å matche mot node.name
        candidate_terms = []
        for term in ["entropy", "entropi", "grid", "halo", "higgs", "energy flow", "EFC", "CMB"]:
            if term.lower() in q:
                candidate_terms.append(term)

        if not candidate_terms:
            return None

        related_nodes: List[Dict[str, Any]] = []
        paths: List[List[str]] = []

        try:
            with self.graph.driver.session() as session:
                # Finn noder som matcher navn
                result = session.run(
                    """
                    MATCH (n)
                    WHERE any(t IN $terms WHERE toLower(n.name) CONTAINS toLower(t))
                    RETURN n, labels(n) as labels
                    LIMIT 20
                    """,
                    terms=candidate_terms,
                )

                node_ids: List[str] = []
                for record in result:
                    node_data = dict(record["n"])
                    labels = record["labels"]
                    related_nodes.append(
                        {
                            "id": node_data.get("id"),
                            "name": node_data.get("name"),
                            "labels": labels,
                        }
                    )
                    if "id" in node_data:
                        node_ids.append(node_data["id"])

                # Ta første to noder og finn paths mellom dem, hvis mulig
                if len(node_ids) >= 2:
                    from_id, to_id = node_ids[0], node_ids[1]
                    neo_paths = self.graph.find_path(from_id=from_id, to_id=to_id, max_depth=max_depth)
                    for p in neo_paths:
                        # p er liste av (node_name, rel_type)
                        paths.append([f"{name} -[{rel}]" if rel else name for (name, rel) in p])

        except Exception as e:
            return EFCGraphContext(
                related_nodes=[],
                paths=[],
                notes=f"Feil ved grafspørring: {e}",
            )

        notes = "Strukturell EFC-kontekst hentet fra Neo4j"
        return EFCGraphContext(
            related_nodes=related_nodes,
            paths=paths,
            notes=notes,
        )

    # ------------------------------------------------------------------
    # PATTERN DETECTION - Tverrdomene EFC-logikk
    # ------------------------------------------------------------------

    def detect_efc_pattern(
        self,
        question: str,
        domain: Optional[str] = None
    ) -> EFCPatternRelevance:
        """
        Oppdager om EFC-logikk er relevant for et spørsmål.
        
        ADAPTIVE: Bruker learned patterns og justerte terskler hvis tilgjengelig.
        
        Dette er IKKE domene-deteksjon - det er pattern-matching.
        EFC kan være relevant i:
        - Kosmologi (selvfølgelig)
        - Biologi (emergente strukturer, metabolisme)
        - AI (stabilitet, emergent behavior)
        - Psykologi (kognitive mønstre, mental energi)
        - Økonomi (markedsbalanse, systemdynamikk)
        - Sosiologi (sosiale systemer, emergente normer)
        
        Returnerer relevance score og reasoning.
        """
        q = question.lower()
        score = 0
        detected_patterns: List[str] = []
        
        # Get base patterns + learned patterns
        base_language_cues = list(self.LANGUAGE_CUES)
        base_logical_patterns = list(self.LOGICAL_PATTERNS)
        
        # Add learned patterns if available
        if self.learner:
            learned_cues = self.learner.get_learned_cues_for_domain(domain) if domain else []
            base_language_cues.extend(learned_cues)
            
            # Get active learned patterns
            active_patterns = self.learner.get_active_patterns()
            base_language_cues.extend(active_patterns.get("language_cues", []))
            base_logical_patterns.extend(active_patterns.get("logical_patterns", []))
        
        # LAG A: Language cues (ord som peker mot EFC-konsepter)
        language_hits = sum(1 for cue in base_language_cues if cue in q)
        score += language_hits
        if language_hits > 0:
            detected_patterns.append(f"Language cues: {language_hits} hits")
        
        # LAG B: Structural cues (Neo4j-baserte konsepter)
        structural_hits = 0
        if self.graph and hasattr(self.graph, "driver") and self.graph.driver:
            try:
                # Sjekk om spørsmål inneholder EFC-konsepter fra grafen
                efc_concepts = ["grid", "halo", "entropy", "flow", "energy", "field"]
                for concept in efc_concepts:
                    if concept in q:
                        structural_hits += 1
                        detected_patterns.append(f"Structural: '{concept}' in graph")
            except Exception:
                pass
        
        score += structural_hits * 3  # Strukturelle treff veier tungt
        
        # LAG C: Logical cues (informasjonsteoretiske mønstre)
        logical_hits = 0
        for pattern in base_logical_patterns:
            if re.search(pattern, q):
                logical_hits += 1
                detected_patterns.append(f"Logical: matches '{pattern}'")
        
        score += logical_hits * 2  # Logiske mønstre veier medium
        
        # ADAPTIVE: Get domain-specific threshold adjustment
        # Negative adjustment = easier to activate (lower threshold)
        # Positive adjustment = harder to activate (higher threshold)
        threshold_adjustment = 0.0
        if self.learner and domain:
            threshold_adjustment = self.learner.get_threshold_adjustment(domain)
            if threshold_adjustment != 0:
                detected_patterns.append(f"Adaptive: {threshold_adjustment:+.1f} threshold adjustment for {domain}")
        
        # Klassifiser relevance level (med adaptive terskler)
        # Apply adjustment: negative = lower threshold (easier), positive = higher threshold (harder)
        base_threshold_weak = 3 + threshold_adjustment
        base_threshold_enabled = 5 + threshold_adjustment
        base_threshold_pure = 7 + threshold_adjustment
        
        if score < base_threshold_weak:
            level = "OUT_OF_SCOPE"
            reasoning = "Ingen sterke EFC-mønstre detektert"
        elif score < base_threshold_enabled:
            level = "WEAK_SIGNAL"
            reasoning = "Svake EFC-mønstre - kan nevnes hvis relevant"
        elif score < base_threshold_pure:
            level = "EFC_ENABLED"
            reasoning = "EFC-logikk kan gi verdifull parallell forklaring"
        else:
            level = "PURE_EFC"
            reasoning = "Sterke EFC-mønstre - EFC bør dominere forklaring"
        
        return EFCPatternRelevance(
            score=score,
            relevance_level=level,
            language_cues=language_hits,
            structural_cues=structural_hits,
            logical_cues=logical_hits,
            detected_patterns=detected_patterns,
            reasoning=reasoning
        )

    def provide_feedback(
        self,
        question: str,
        domain: str,
        efc_score: float,
        detected_patterns: List[str],
        was_helpful: bool
    ) -> None:
        """
        Gir tilbakemelding til adaptive learning system.
        
        Args:
            question: Det opprinnelige spørsmålet
            domain: Domenet som ble detektert
            efc_score: EFC-relevance score som ble beregnet
            detected_patterns: Mønstre som ble oppdaget
            was_helpful: Om EFC-logikk var hjelpsom for dette spørsmålet
        """
        if self.learner:
            # Record observation
            self.learner.observe_pattern_use(
                question=question,
                domain=domain,
                detected_patterns=detected_patterns,
                efc_score=efc_score,
                was_helpful=was_helpful
            )
            
            # Update threshold adjustments for the domain
            if domain in self.learner.domains:
                self.learner.get_threshold_adjustment(domain)
            
            # Try to learn new patterns if helpful but low score
            if was_helpful and efc_score < 5.0:
                new_patterns = self.learner.extract_new_patterns(question, domain)
                if new_patterns and domain in self.learner.domains:
                    self.learner.domains[domain].learned_patterns.extend(new_patterns)
            
            # Persist learning every 5 observations
            if len(self.learner.observations) % 5 == 0:
                self.learner.save_learning()

    def should_augment_with_efc(
        self,
        pattern_relevance: EFCPatternRelevance
    ) -> bool:
        """
        Bestem om EFC bør brukes som AUGMENT (parallell forklaring).
        
        Dette unngår å "presse" EFC inn - den tilbys kun når relevant.
        """
        return pattern_relevance.relevance_level in ["EFC_ENABLED", "PURE_EFC"]

    def should_override_with_efc(
        self,
        pattern_relevance: EFCPatternRelevance
    ) -> bool:
        """
        Bestem om EFC bør brukes som OVERRIDE (primær logikk).
        
        Dette skjer kun ved veldig sterke signaler.
        """
        return pattern_relevance.relevance_level == "PURE_EFC"


# -------------------------------------------------------------------
# Enkel selvtest
# -------------------------------------------------------------------

if __name__ == "__main__":
    print("🧪 Testing EFCTheoryEngine")
    print("=" * 60)

    engine = EFCTheoryEngine()

    # Test 1: Domene-deteksjon
    q1 = "Hvordan forklarer Energy Flow Hypothesis rotasjonskurver uten mørk materie?"
    print("\n1️⃣ Domene-deteksjon")
    print(f"Q: {q1}")
    print(f"   is_efc_question: {engine.is_efc_question(q1)}")
    mode = engine.infer_mode(q1, active_domains=["cosmology"])
    print(f"   mode: {mode.mode}, conf={mode.confidence:.2f}, reasons={mode.reasons}")

    # Test 2: Påstands-sjekk
    claim = "Galakse-rotasjonskurver krever mørk materie som egen komponent."
    print("\n2️⃣ Påstands-sjekk")
    check = engine.check_claim(claim)
    print(f"   is_consistent: {check.is_consistent}, conf={check.confidence:.2f}")
    print(f"   violated: {check.violated_principles}")
    print(f"   supporting: {check.supporting_principles}")
    print(f"   notes: {check.notes}")

    # Test 3: Omskriving
    print("\n3️⃣ Omskriving")
    rewritten = engine.suggest_rewrite(claim)
    print(f"   original:  {claim}")
    print(f"   rewritten: {rewritten}")

    # Test 4: EFC-kompatibel påstand
    claim2 = "Rotasjonskurver forklares via emergent gravity og entropigradienter i grid-medium."
    print("\n4️⃣ EFC-kompatibel påstand")
    check2 = engine.check_claim(claim2)
    print(f"   is_consistent: {check2.is_consistent}, conf={check2.confidence:.2f}")
    print(f"   violated: {check2.violated_principles}")
    print(f"   supporting: {check2.supporting_principles}")
    print(f"   notes: {check2.notes}")

    # Test 5: Kjerneprinsipper
    print("\n5️⃣ EFC Kjerneprinsipper")
    principles = engine.get_core_principles()
    for p in principles:
        print(f"   • {p.key}: {p.title} (weight={p.weight})")

    # Test 6: Pattern Detection (NYTT!)
    print("\n" + "=" * 60)
    print("6️⃣ PATTERN DETECTION - Tverrdomene EFC-logikk")
    print("=" * 60)
    
    test_questions = [
        # Kosmologi (opplagt EFC)
        "Hvorfor stabiliserer galakser seg i spiralform?",
        
        # Biologi (EFC-relevant!)
        "Hvorfor organiserer celler seg i vevstrukturer?",
        
        # AI (EFC-relevant!)
        "Hva driver emergent behavior i AI-systemer?",
        
        # Psykologi (EFC-relevant!)
        "Hvorfor finner hjernen mentale mønstre?",
        
        # Økonomi (EFC-relevant!)
        "Hvorfor stabiliserer markeder seg rundt en pris?",
        
        # Ikke EFC
        "Hva er datoen i dag?",
    ]
    
    for q in test_questions:
        pattern = engine.detect_efc_pattern(q)
        print(f"\n   Q: {q}")
        print(f"   Score: {pattern.score:.1f} | Level: {pattern.relevance_level}")
        print(f"   Cues: lang={pattern.language_cues}, struct={pattern.structural_cues}, logic={pattern.logical_cues}")
        if pattern.detected_patterns:
            print(f"   Patterns: {', '.join(pattern.detected_patterns[:2])}")
        print(f"   → Augment: {engine.should_augment_with_efc(pattern)}, Override: {engine.should_override_with_efc(pattern)}")

    print("\n" + "=" * 60)
    print("✅ EFCTheoryEngine basic tests complete")
    print("💡 Integration: Koble til OptimalMemorySystem som domenemotor")
    print("🌌 Pattern Detection: Oppdager EFC-logikk på tvers av domener!")
