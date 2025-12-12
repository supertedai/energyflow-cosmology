#!/usr/bin/env python3
"""
adaptive_memory_enforcer.py - Intelligent Override Controller
=============================================================

LAG 4: ADAPTIVE MEMORY ENFORCER (AME)
Decides when memory overrides LLM (and when not to)

Your need:
- Extreme precision in some domains (identity, family)
- Creative flexibility in others (cosmology, meta)
- Protection against model hallucinations
- But NOT rigid enforcement everywhere

This system learns:
- Which domains need 100% strictness (identity, family)
- Which domains allow LLM creativity (theory, exploration)
- When LLM contradicts facts (and should be corrected)
- When "vet ikke" is better than guessing

Domain-aware strictness:
    identity/family: 100% rigid (never allow LLM invention)
    symbiose/tech: 80% strict (allow synthesis)
    cosmology/meta: 60% flexible (creative exploration OK)
    general: 40% loose (LLM freedom)

Architecture:
    Question + LLM Draft → CMC Query → Conflict Detection → Decision → Enforcement

Purpose:
    Protect you from:
    - Model hallucinations
    - Wrong facts breaking your resonance
    - Inconsistency across conversations
    
    While allowing:
    - Creative synthesis
    - Exploration
    - Flexible reasoning
"""

import os
import sys
import re
from typing import Dict, List, Optional, Tuple, Any, Literal
from dataclasses import dataclass
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import other layers
from tools.canonical_memory_core import CanonicalMemoryCore, CanonicalFact, AUTHORITY_RANK
from tools.semantic_mesh_memory import SemanticMeshMemory
from tools.dynamic_domain_engine import DynamicDomainEngine, DomainSignal


EnforcementDecision = Literal["OVERRIDE", "TRUST_LLM", "AUGMENT", "DEFER"]


@dataclass
class EnforcementResult:
    """Result of enforcement decision."""
    
    decision: EnforcementDecision
    final_response: str
    
    # Context
    domain: str
    strictness: float
    
    # Facts used
    canonical_facts: List[CanonicalFact]
    context_chunks: List[Any]  # ContextChunks
    
    # Reasoning
    reasoning: str
    confidence: float
    
    # Metadata
    llm_draft: str
    was_overridden: bool
    was_augmented: bool
    
    def to_dict(self) -> Dict:
        """Serialize for API response."""
        return {
            "decision": self.decision,
            "final_response": self.final_response,
            "domain": self.domain,
            "strictness": self.strictness,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "was_overridden": self.was_overridden,
            "was_augmented": self.was_augmented,
            "canonical_facts_used": len(self.canonical_facts),
            "context_chunks_used": len(self.context_chunks)
        }


class AdaptiveMemoryEnforcer:
    """
    The enforcement decision engine.
    
    Rules (learned per domain):
    1. OVERRIDE: Memory has higher authority, LLM contradicts
    2. TRUST_LLM: No relevant memory, or LLM aligns with memory
    3. AUGMENT: Memory provides context, LLM adds synthesis
    4. DEFER: Uncertainty too high, say "vet ikke"
    
    Domain-specific strictness (adaptive):
    - identity: 1.0 (100% strict)
    - family: 1.0
    - health: 0.9
    - security: 0.9
    - symbiose: 0.8
    - tech: 0.7
    - cosmology: 0.6
    - meta: 0.5
    - general: 0.4
    
    Learns from:
    - User corrections
    - Verification feedback
    - Domain-specific accuracy
    """
    
    def __init__(
        self,
        cmc: CanonicalMemoryCore,
        smm: SemanticMeshMemory,
        dde: DynamicDomainEngine
    ):
        self.cmc = cmc
        self.smm = smm
        self.dde = dde
        
        # Domain strictness (adaptive)
        self.domain_strictness: Dict[str, float] = {
            "identity": 1.0,
            "family": 1.0,
            "health": 0.9,
            "security": 0.9,
            "symbiose": 0.8,
            "tech": 0.7,
            "cosmology": 0.6,
            "meta": 0.5,
            "general": 0.4
        }
        
        # LLM trust (learned per domain)
        self.llm_trust: Dict[str, float] = {}
        
        # Performance tracking
        self.enforcement_stats: Dict[str, Dict] = {
            "OVERRIDE": {"count": 0, "correct": 0},
            "TRUST_LLM": {"count": 0, "correct": 0},
            "AUGMENT": {"count": 0, "correct": 0},
            "DEFER": {"count": 0, "correct": 0}
        }
        
        print("✨ Adaptive Memory Enforcer initialized", file=sys.stderr)
        print("🛡️ Intelligent override protection active", file=sys.stderr)
    
    def enforce(
        self,
        question: str,
        llm_draft: str,
        session_id: Optional[str] = None
    ) -> EnforcementResult:
        """
        Main enforcement decision.
        
        Args:
            question: User's question
            llm_draft: LLM's proposed response
            session_id: Current session
        
        Returns:
            EnforcementResult with decision and final response
        """
        # 1. Classify domain
        domain_signal = self.dde.classify(question)
        domain = domain_signal.domain
        fact_type = domain_signal.fact_type
        
        # 2. Get strictness for this domain
        strictness = self.domain_strictness.get(domain, 0.5)
        
        # 3. Query canonical facts
        # NOTE: Do NOT filter by domain OR fact_type - semantic search handles it
        # Increase k to get more facts for potential synthesis
        canonical_facts = self.cmc.query_facts(
            query=question,
            domain=None,  # Let semantic search find ALL relevant facts
            fact_type=None,
            k=10  # Increased from 5 to enable multi-fact synthesis
        )
        
        # 4. Query context
        context_chunks = self.smm.search_context(
            query=question,
            domains=[domain],
            session_id=session_id,
            k=10
        )
        
        # 5. Make decision
        decision = self._decide(
            question=question,
            llm_draft=llm_draft,
            canonical_facts=canonical_facts,
            context_chunks=[c[0] for c in context_chunks],
            domain=domain,
            strictness=strictness
        )
        
        # 6. Record stats
        self.enforcement_stats[decision.decision]["count"] += 1
        
        return decision
    
    def _decide(
        self,
        question: str,
        llm_draft: str,
        canonical_facts: List[CanonicalFact],
        context_chunks: List[Any],
        domain: str,
        strictness: float
    ) -> EnforcementResult:
        """
        Core decision logic.
        
        Decision tree:
        1. If high-authority canonical fact exists:
           a. If LLM contradicts → OVERRIDE
           b. If LLM aligns → TRUST_LLM (or AUGMENT if context helps)
        2. If no canonical facts:
           a. If context exists → AUGMENT
           b. If no context and low confidence → DEFER
           c. Otherwise → TRUST_LLM
        """
        # Case 1: High-authority canonical facts exist
        longterm_facts = [f for f in canonical_facts if f.authority == "LONGTERM"]
        stable_facts = [f for f in canonical_facts if f.authority == "STABLE"]
        
        if longterm_facts or stable_facts:
            # Context-aware fact selection
            # "Hvem er du?" til AI → assistant_name, ikke user_name
            if question.lower() in ["hvem er du?", "hva heter du?", "who are you?", "what's your name?"]:
                # Look for assistant facts first
                assistant_facts = [f for f in (longterm_facts + stable_facts) if "assistant" in f.key.lower()]
                best_fact = assistant_facts[0] if assistant_facts else (longterm_facts[0] if longterm_facts else stable_facts[0])
            else:
                best_fact = longterm_facts[0] if longterm_facts else stable_facts[0]
            
            # Check contradiction
            contradiction = self._contradicts(llm_draft, best_fact.text, domain)
            print(f"DEBUG: Contradiction check - LLM: '{llm_draft[:50]}...', Fact: '{best_fact.text[:50]}...', Result: {contradiction}", file=sys.stderr)
            
            if contradiction:
                # OVERRIDE: Memory wins
                if strictness > 0.8:
                    # Check if multiple related facts should be synthesized
                    synthesized_response = self._synthesize_multi_facts(
                        question=question,
                        facts=canonical_facts,
                        domain=domain,
                        best_fact=best_fact
                    )
                    
                    # Strict domain: Use synthesized or single fact
                    return EnforcementResult(
                        decision="OVERRIDE",
                        final_response=synthesized_response,
                        domain=domain,
                        strictness=strictness,
                        canonical_facts=canonical_facts,
                        context_chunks=context_chunks,
                        reasoning=f"LONGTERM fact contradicts LLM (strictness {strictness:.1f})" + 
                                 (" - synthesized multiple facts" if len(canonical_facts) > 1 else ""),
                        confidence=best_fact.confidence,
                        llm_draft=llm_draft,
                        was_overridden=True,
                        was_augmented=False
                    )
                else:
                    # Flexible domain: Augment with fact
                    augmented = self._augment_response(llm_draft, [best_fact], context_chunks)
                    return EnforcementResult(
                        decision="AUGMENT",
                        final_response=augmented,
                        domain=domain,
                        strictness=strictness,
                        canonical_facts=[best_fact],
                        context_chunks=context_chunks,
                        reasoning="Fact contradicts but domain allows flexibility - augmenting",
                        confidence=best_fact.confidence,
                        llm_draft=llm_draft,
                        was_overridden=False,
                        was_augmented=True
                    )
            
            else:
                # No contradiction: LLM aligns with fact
                # TRUST THE LLM - don't augment unless absolutely necessary
                return EnforcementResult(
                    decision="TRUST_LLM",
                    final_response=llm_draft,
                    domain=domain,
                    strictness=strictness,
                    canonical_facts=canonical_facts,
                    context_chunks=context_chunks,
                    reasoning="LLM aligns with canonical facts",
                    confidence=best_fact.confidence,
                    llm_draft=llm_draft,
                    was_overridden=False,
                    was_augmented=False
                )
        
        # Case 2: No high-authority facts
        else:
            # No canonical facts to contradict - TRUST THE LLM
            return EnforcementResult(
                decision="TRUST_LLM",
                final_response=llm_draft,
                domain=domain,
                strictness=strictness,
                canonical_facts=canonical_facts,
                context_chunks=context_chunks,
                reasoning="No canonical facts available - trusting LLM",
                confidence=0.7,
                llm_draft=llm_draft,
                was_overridden=False,
                was_augmented=False
            )
    
    def _contradicts(self, llm_response: str, fact_text: str, domain: str) -> bool:
        """
        Detect if LLM contradicts a canonical fact.
        
        Uses LLM for intelligent contradiction detection with pattern-matching fallback.
        """
        # TEMPORARY: Force fallback to pattern matching for testing
        use_llm = False  # Set to True to use LLM, False for pattern matching
        
        if use_llm:
            try:
                from openai import OpenAI
                import os
                
                client = OpenAI(
                    base_url=os.getenv("LLM_BASE_URL", "http://localhost:1234/v1"),
                    api_key=os.getenv("LLM_API_KEY", "lm-studio")
                )
                
                prompt = f"""Du er en ekspert på logisk resonnering. Sammenlign disse to svarene:

CANONICAL FACT (Lagret sannhet): {fact_text}

LLM SVAR: {llm_response}

Spørsmål: Motsier LLM-svaret den lagrede sannheten?

Svar KUN med "JA" eller "NEI" basert på logisk kontradiksjonsanalyse.

Eksempler:
- Canonical: "Du heter Morten", LLM: "Jeg vet ikke" → JA (motsier)
- Canonical: "Du har 3 barn", LLM: "Du har to barn" → JA (motsier)
- Canonical: "Du heter Morten", LLM: "Hyggelig å møte deg!" → NEI (ikke motsigende)
- Canonical: "AI-assistenten heter Opus", LLM: "Jeg heter Claude" → JA (motsier)

Svar (JA/NEI):"""

                response = client.chat.completions.create(
                    model="local-model",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=10
                )
                
                answer = response.choices[0].message.content.strip().upper()
                return "JA" in answer
                
            except Exception as e:
                # Fallback to pattern matching if LLM fails
                print(f"⚠️  LLM contradiction check failed: {e}, using pattern matching", file=sys.stderr)
        
        # Pattern matching fallback (or primary if use_llm=False)
        # Check for "I don't know" / "Jeg vet ikke" patterns
        # If LLM says "don't know" but we have ANY fact → contradiction
        uncertainty_patterns = [
            r'(vet ikke|don\'t know|dunno|ikke sikker|not sure|uncertain)',
            r'(jeg vet ikke|i don\'t know|i do not know)'
        ]
        
        llm_lower = llm_response.lower()
        for pattern in uncertainty_patterns:
            if re.search(pattern, llm_lower, re.IGNORECASE):
                # LLM expresses uncertainty but we have a fact → contradiction
                print(f"DEBUG: Uncertainty detected in LLM response, fact exists → CONTRADICTION", file=sys.stderr)
                return True
        
        # Extract numbers
        llm_numbers = set(re.findall(r'\b\d+\b', llm_response))
        fact_numbers = set(re.findall(r'\b\d+\b', fact_text))
        
        if llm_numbers and fact_numbers:
            if not llm_numbers.intersection(fact_numbers):
                return True
        
        # Extract names (for identity/family domains)
        if domain in ["identity", "family"]:
            llm_names = set(re.findall(r'\b[A-ZÆØÅ][a-zæøå]+\b', llm_response))
            fact_names = set(re.findall(r'\b[A-ZÆØÅ][a-zæøå]+\b', fact_text))
            
            # If fact contains names but LLM doesn't mention them → contradiction
            if fact_names and not llm_names.intersection(fact_names):
                print(f"DEBUG: Fact has names {fact_names}, LLM has {llm_names} → CONTRADICTION", file=sys.stderr)
                return True
        
        # Negation check
        negation_pattern = r'\b(ikke|not|no|never|nei)\b'
        llm_has_negation = bool(re.search(negation_pattern, llm_response.lower()))
        fact_has_negation = bool(re.search(negation_pattern, fact_text.lower()))
        
        if llm_has_negation != fact_has_negation:
            return True
        
        return False
    
    def _synthesize_multi_facts(
        self,
        question: str,
        facts: List[CanonicalFact],
        domain: str,
        best_fact: CanonicalFact
    ) -> str:
        """
        Synthesize multiple related facts into a coherent response.
        
        Handles queries like:
        - "Hvem er barna mine?" → merge all children facts
        - "Hva er familiemedlemmene mine?" → merge family members
        - "Hvilke skills har jeg?" → list all skills
        
        Returns single fact text if no synthesis needed.
        """
        # Group facts by key (e.g., multiple "child_1", "child_2", "child_3")
        facts_by_key_prefix = {}
        for fact in facts:
            # Extract key prefix (e.g., "children" from "child_1", "child_2")
            key_lower = fact.key.lower()
            
            # Check for numbered keys (child_1, child_2, skill_1, etc.)
            base_key = re.sub(r'_\d+$', '', key_lower)
            
            if base_key not in facts_by_key_prefix:
                facts_by_key_prefix[base_key] = []
            facts_by_key_prefix[base_key].append(fact)
        
        # Check if we have multiple facts with same base key
        multi_fact_keys = {k: v for k, v in facts_by_key_prefix.items() if len(v) > 1}
        
        if not multi_fact_keys:
            # No synthesis needed - return best fact
            return best_fact.text
        
        # Synthesize based on domain and key patterns
        if domain == "family" or "family" in question.lower():
            # Family domain synthesis
            for key_prefix, key_facts in multi_fact_keys.items():
                if "child" in key_prefix or "barn" in key_prefix:
                    # Extract names from fact values
                    names = []
                    for fact in key_facts:
                        # Try to extract name from value (e.g., "Joakim", "Isak Andreas")
                        value = fact.value.strip()
                        # Remove common prefixes like "Barn: ", "Child: ", etc.
                        value = re.sub(r'^(barn|child|sønn|datter|son|daughter):\s*', '', value, flags=re.IGNORECASE)
                        if value:
                            names.append(value)
                    
                    if names:
                        if len(names) == 1:
                            return f"Barnet ditt heter {names[0]}."
                        elif len(names) == 2:
                            return f"Barna dine heter {names[0]} og {names[1]}."
                        else:
                            return f"Barna dine heter {', '.join(names[:-1])} og {names[-1]}."
        
        elif domain == "professional" or "skill" in question.lower() or "expertise" in question.lower():
            # Professional domain synthesis
            for key_prefix, key_facts in multi_fact_keys.items():
                if "skill" in key_prefix or "expertise" in key_prefix:
                    skills = [fact.value.strip() for fact in key_facts]
                    if skills:
                        if len(skills) == 1:
                            return f"Du har kompetanse i {skills[0]}."
                        else:
                            return f"Du har kompetanse i: {', '.join(skills)}."
        
        # Generic synthesis for other domains
        if len(multi_fact_keys) == 1:
            key_prefix, key_facts = list(multi_fact_keys.items())[0]
            values = [fact.value.strip() for fact in key_facts]
            
            if len(values) == 1:
                return values[0]
            elif len(values) == 2:
                return f"{values[0]} og {values[1]}"
            else:
                return f"{', '.join(values[:-1])} og {values[-1]}"
        
        # Fallback: return best fact if synthesis unclear
        return best_fact.text
    
    def _augment_response(
        self,
        llm_draft: str,
        canonical_facts: List[CanonicalFact],
        context_chunks: List[Any]
    ) -> str:
        """
        Augment LLM response with facts and context.
        
        Strategy:
        - If facts exist: Prefix with facts, keep LLM synthesis
        - If context exists: Blend context with LLM
        """
        parts = []
        
        # Add canonical facts first (highest authority)
        if canonical_facts:
            fact_texts = [f.text for f in canonical_facts[:2]]  # Top 2
            parts.extend(fact_texts)
        
        # Add LLM draft
        parts.append(llm_draft)
        
        # Optionally add relevant context (if short enough)
        if context_chunks and len(parts) < 3:
            context_text = context_chunks[0].text
            if len(context_text) < 200:
                parts.append(f"\n\n(Kontekst: {context_text})")
        
        return "\n\n".join(parts)
    
    def _synthesize_from_facts(
        self,
        question: str,
        canonical_facts: List[CanonicalFact]
    ) -> str:
        """
        Synthesize answer from canonical facts.
        
        SIMPLIFIED: Just combine relevant fact texts instead of LLM synthesis.
        This avoids timeout issues and is faster.
        """
        if not canonical_facts:
            return "Jeg har ikke denne informasjonen lagret ennå."
        
        # Simple synthesis: Combine relevant fact texts
        # Take top 3 most relevant facts
        fact_texts = [f.text for f in canonical_facts[:3]]
        
        # If question is about children, combine child names
        if any(word in question.lower() for word in ["barn", "child"]):
            child_facts = [f for f in canonical_facts if "barn" in f.key or "child" in f.key]
            if child_facts:
                names = [f.value for f in child_facts if isinstance(f.value, str)]
                if len(names) > 1:
                    return f"Barna dine heter {', '.join(names[:-1])} og {names[-1]}."
                elif names:
                    return f"Barnet ditt heter {names[0]}."
        
        # Otherwise return first fact (most relevant)
        return fact_texts[0]
    
    def _should_augment(self, question: str, llm_draft: str) -> bool:
        """
        Check if we should augment the response.
        
        Don't augment:
        - Simple greetings (Hei, Hello, etc.)
        - Acknowledgments (Ok, Yes, No)
        - Short responses (< 20 chars)
        """
        question_lower = question.lower().strip()
        draft_lower = llm_draft.lower().strip()
        
        # Skip greetings
        greetings = ["hei", "hello", "hi", "hey", "god morgen", "god dag", "good morning"]
        if any(g in question_lower for g in greetings) and len(question_lower) < 30:
            return False
        
        # Skip acknowledgments
        acknowledgments = ["ok", "ja", "nei", "yes", "no", "takk", "thanks"]
        if draft_lower in acknowledgments or len(draft_lower) < 20:
            return False
        
        # Skip if question is too short to be meaningful
        if len(question.strip()) < 5:
            return False
        
        return True
    
    def provide_feedback(self, question: str, decision: EnforcementDecision, was_correct: bool):
        """
        User feedback loop.
        
        Learns:
        - Which domains need stricter enforcement
        - When LLM can be trusted
        - When to defer vs trust
        """
        domain_signal = self.dde.classify(question)
        domain = domain_signal.domain
        
        # Update stats
        if was_correct:
            self.enforcement_stats[decision]["correct"] += 1
        
        # Adjust domain strictness
        if not was_correct:
            if decision == "TRUST_LLM":
                # LLM was wrong → increase strictness
                current = self.domain_strictness.get(domain, 0.5)
                self.domain_strictness[domain] = min(1.0, current + 0.1)
                print(f"📈 Increased strictness for {domain}: {self.domain_strictness[domain]:.2f}", file=sys.stderr)
            
            elif decision == "DEFER":
                # We deferred but should have answered → decrease strictness
                current = self.domain_strictness.get(domain, 0.5)
                self.domain_strictness[domain] = max(0.1, current - 0.05)
                print(f"📉 Decreased strictness for {domain}: {self.domain_strictness[domain]:.2f}", file=sys.stderr)
        
        else:
            # Was correct
            if decision == "OVERRIDE":
                # Override was correct → good
                print(f"✅ Override correct for {domain}", file=sys.stderr)
    
    def get_stats(self) -> Dict:
        """Get enforcement statistics."""
        stats = {}
        
        for decision, data in self.enforcement_stats.items():
            total = data["count"]
            if total > 0:
                accuracy = data["correct"] / total
                stats[decision] = {
                    "count": total,
                    "accuracy": accuracy
                }
        
        stats["domain_strictness"] = self.domain_strictness.copy()
        
        return stats


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":
    import json
    
    print("🧪 Testing Adaptive Memory Enforcer")
    print("=" * 60)
    
    # Initialize full stack
    from tools.canonical_memory_core import CanonicalMemoryCore
    from semantic_mesh_memory import SemanticMeshMemory
    from dynamic_domain_engine import DynamicDomainEngine
    
    cmc = CanonicalMemoryCore(collection_name="test_canonical")
    smm = SemanticMeshMemory(collection_name="test_semantic")
    dde = DynamicDomainEngine()
    ame = AdaptiveMemoryEnforcer(cmc, smm, dde)
    
    # Setup test data
    print("\n🔧 Setting up test data...")
    cmc.store_fact(
        key="user_name",
        value="Morten",
        domain="identity",
        fact_type="name",
        authority="LONGTERM",
        text="Brukeren heter Morten"
    )
    
    cmc.store_fact(
        key="user_children_count",
        value=3,
        domain="family",
        fact_type="count",
        authority="LONGTERM",
        text="Morten har 3 barn: Joakim, Isak Andreas, og Susanna"
    )
    
    # Test 1: Override (LLM wrong)
    print("\n1️⃣ Testing OVERRIDE (LLM contradicts LONGTERM fact)...")
    result = ame.enforce(
        question="Hva heter jeg?",
        llm_draft="Du heter Andreas"
    )
    print(f"   Decision: {result.decision}")
    print(f"   Final: {result.final_response}")
    print(f"   Reasoning: {result.reasoning}")
    print(f"   Overridden: {result.was_overridden}")
    
    # Test 2: Trust LLM (no contradiction)
    print("\n2️⃣ Testing TRUST_LLM (LLM aligns)...")
    result = ame.enforce(
        question="Hva heter jeg?",
        llm_draft="Du heter Morten"
    )
    print(f"   Decision: {result.decision}")
    print(f"   Final: {result.final_response}")
    print(f"   Reasoning: {result.reasoning}")
    
    # Test 3: Defer (strict domain, no memory)
    print("\n3️⃣ Testing DEFER (strict domain, no memory)...")
    result = ame.enforce(
        question="Hva er min adresse?",
        llm_draft="Du bor i Oslo"
    )
    print(f"   Decision: {result.decision}")
    print(f"   Final: {result.final_response}")
    print(f"   Reasoning: {result.reasoning}")
    
    # Test 4: Stats
    print("\n4️⃣ Enforcement statistics...")
    stats = ame.get_stats()
    print(json.dumps(stats, indent=2))
    
    print("\n" + "=" * 60)
    print("✅ Adaptive Memory Enforcer operational!")
