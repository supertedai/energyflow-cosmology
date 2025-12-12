#!/usr/bin/env python3
"""
identity_protection.py - Identity Protection for Meta-Supervisor
=================================================================

Protects critical identity facts and blocks test data corruption.

PRINSIPP: Canonical identity enforcement
Identitetsfakta er kritiske og må beskyttes mot:
- Test data corrosion (Morpheus → Morten)
- LLM hallucinations
- Low-trust overrides
- Experimental noise

Dette er top-down vern av kritiske sannheter.

ARKITEKTUR:
1. Critical fact registry: Hvilke fakta er kritiske?
2. Test data detection: Identifiser test/eksperiment data
3. Override blocking: Blokkér low-trust changes
4. Identity validation: Verifiser konsistens

INTEGRASJON:
- CMC: Beskytter canonical facts
- AME: Blokkerer low-trust overrides
- Intent Engine: Aktiverer ved PROTECTION mode
- Self-Healing: Reparerer identity corruption
"""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import sys
from pathlib import Path

# Add tools to path for CLI testing
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.meta_supervisor import IntentSignal, IntentMode


class ProtectionLevel(Enum):
    """Protection level for facts"""
    CRITICAL = "critical"       # Cannot be changed (identity)
    HIGH = "high"              # Requires high trust to change
    MEDIUM = "medium"          # Normal protection
    LOW = "low"                # Can be changed easily


@dataclass
class ProtectionRule:
    """Protection rule for a fact or domain"""
    rule_id: str
    domain: str
    key_pattern: str           # Regex or exact match
    level: ProtectionLevel
    min_trust_to_override: float  # Min trust score to change
    block_patterns: List[str]  # Blocked values (e.g., "Morpheus", "test")
    reason: str
    
    def to_dict(self) -> Dict:
        return {
            "rule_id": self.rule_id,
            "domain": self.domain,
            "key_pattern": self.key_pattern,
            "level": self.level.value,
            "min_trust_to_override": self.min_trust_to_override,
            "block_patterns": self.block_patterns,
            "reason": self.reason
        }


@dataclass
class ValidationResult:
    """Result of identity validation"""
    item_id: str
    passed: bool
    protection_level: ProtectionLevel
    blocked_reason: Optional[str] = None
    required_trust: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            "item_id": self.item_id,
            "passed": self.passed,
            "protection_level": self.protection_level.value,
            "blocked_reason": self.blocked_reason,
            "required_trust": self.required_trust
        }


class IdentityProtection:
    """
    IDENTITY PROTECTION
    
    Beskytter kritiske identitetsfakta mot corruption.
    
    Håndterer:
    - Test data isolation (Morpheus ≠ Morten)
    - Critical fact protection (user name, system identity)
    - Low-trust override blocking
    - Identity consistency validation
    
    Dette er sikkerhetslaget for kjerneidentitet.
    """
    
    def __init__(self):
        self.protection_rules: List[ProtectionRule] = []
        self.blocked_values: Set[str] = set()
        
        # Initialize default rules
        self._init_default_rules()
        
        self.validation_stats = {
            "total_validations": 0,
            "passed": 0,
            "blocked": 0,
            "critical_blocks": 0
        }
    
    def _init_default_rules(self):
        """Initialize default protection rules"""
        
        # Rule 1: User identity (CRITICAL)
        self.protection_rules.append(ProtectionRule(
            rule_id="identity_user_name",
            domain="identity",
            key_pattern="user.name",
            level=ProtectionLevel.CRITICAL,
            min_trust_to_override=0.95,
            block_patterns=["morpheus", "test", "cli_test", "unknown"],
            reason="User name is critical identity fact"
        ))
        
        # Rule 2: System identity (CRITICAL)
        self.protection_rules.append(ProtectionRule(
            rule_id="identity_system_name",
            domain="identity",
            key_pattern="system.name",
            level=ProtectionLevel.CRITICAL,
            min_trust_to_override=0.95,
            block_patterns=["test", "unknown"],
            reason="System name is critical identity fact"
        ))
        
        # Rule 3: Identity domain general (HIGH)
        self.protection_rules.append(ProtectionRule(
            rule_id="identity_general",
            domain="identity",
            key_pattern="*",
            level=ProtectionLevel.HIGH,
            min_trust_to_override=0.8,
            block_patterns=["morpheus", "test"],
            reason="Identity domain requires high trust"
        ))
        
        # Rule 4: System config (MEDIUM)
        self.protection_rules.append(ProtectionRule(
            rule_id="system_config",
            domain="system_config",
            key_pattern="*",
            level=ProtectionLevel.MEDIUM,
            min_trust_to_override=0.7,
            block_patterns=["test"],
            reason="System config requires medium trust"
        ))
        
        # Add blocked values to set
        for rule in self.protection_rules:
            self.blocked_values.update([v.lower() for v in rule.block_patterns])
    
    def validate_fact(
        self,
        key: str,
        value: str,
        domain: str,
        trust_score: float,
        intent_signal: Optional[IntentSignal] = None
    ) -> ValidationResult:
        """
        Validate a fact against protection rules.
        
        Args:
            key: Fact key
            value: Fact value
            domain: Fact domain
            trust_score: Trust score of source
            intent_signal: Current intent (optional)
        
        Returns:
            ValidationResult with pass/block decision
        """
        self.validation_stats["total_validations"] += 1
        
        # Find matching protection rule
        matching_rule = self._find_matching_rule(key, domain)
        
        if not matching_rule:
            # No rule → default to LOW protection
            self.validation_stats["passed"] += 1
            return ValidationResult(
                item_id=f"{domain}.{key}",
                passed=True,
                protection_level=ProtectionLevel.LOW
            )
        
        # Check blocked patterns
        value_lower = value.lower()
        for pattern in matching_rule.block_patterns:
            if pattern.lower() in value_lower:
                self.validation_stats["blocked"] += 1
                if matching_rule.level == ProtectionLevel.CRITICAL:
                    self.validation_stats["critical_blocks"] += 1
                
                return ValidationResult(
                    item_id=f"{domain}.{key}",
                    passed=False,
                    protection_level=matching_rule.level,
                    blocked_reason=f"Contains blocked pattern: {pattern}",
                    required_trust=matching_rule.min_trust_to_override
                )
        
        # Check trust score
        if trust_score < matching_rule.min_trust_to_override:
            self.validation_stats["blocked"] += 1
            return ValidationResult(
                item_id=f"{domain}.{key}",
                passed=False,
                protection_level=matching_rule.level,
                blocked_reason=f"Trust score {trust_score:.2f} < required {matching_rule.min_trust_to_override:.2f}",
                required_trust=matching_rule.min_trust_to_override
            )
        
        # Passed all checks
        self.validation_stats["passed"] += 1
        return ValidationResult(
            item_id=f"{domain}.{key}",
            passed=True,
            protection_level=matching_rule.level,
            required_trust=matching_rule.min_trust_to_override
        )
    
    def validate_override(
        self,
        existing_fact: Dict[str, Any],
        new_value: str,
        new_trust_score: float,
        intent_signal: Optional[IntentSignal] = None
    ) -> ValidationResult:
        """
        Validate an override attempt.
        
        Args:
            existing_fact: Current fact
            new_value: Proposed new value
            new_trust_score: Trust score of new source
            intent_signal: Current intent
        
        Returns:
            ValidationResult with pass/block decision
        """
        key = existing_fact.get("key", "")
        domain = existing_fact.get("domain", "general")
        existing_value = existing_fact.get("value", "")
        
        # Validate new value
        result = self.validate_fact(
            key=key,
            value=new_value,
            domain=domain,
            trust_score=new_trust_score,
            intent_signal=intent_signal
        )
        
        # Additional check: Don't allow downgrades from canonical
        if existing_fact.get("trust_score", 0) >= 0.95 and new_trust_score < 0.95:
            return ValidationResult(
                item_id=f"{domain}.{key}",
                passed=False,
                protection_level=ProtectionLevel.CRITICAL,
                blocked_reason="Cannot downgrade canonical fact with low-trust source",
                required_trust=0.95
            )
        
        return result
    
    def detect_test_data(self, text: str) -> bool:
        """
        Detect if text contains test data patterns.
        
        Returns True if test data detected.
        """
        text_lower = text.lower()
        
        # Test data indicators
        test_patterns = [
            "morpheus",
            "cli_test",
            "test_",
            "experiment",
            "placeholder",
            "[test]",
            "(test)",
            "debug_"
        ]
        
        return any(pattern in text_lower for pattern in test_patterns)
    
    def isolate_test_data(
        self,
        facts: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Separate test data from production data.
        
        Returns:
            {
                "production": [...],
                "test": [...]
            }
        """
        production = []
        test = []
        
        for fact in facts:
            value = fact.get("value", "")
            key = fact.get("key", "")
            
            # Check if test data
            if self.detect_test_data(value) or self.detect_test_data(key):
                test.append(fact)
            else:
                production.append(fact)
        
        return {
            "production": production,
            "test": test
        }
    
    def _find_matching_rule(
        self,
        key: str,
        domain: str
    ) -> Optional[ProtectionRule]:
        """Find matching protection rule for key/domain"""
        
        # First: exact match
        for rule in self.protection_rules:
            if rule.domain == domain and rule.key_pattern == key:
                return rule
        
        # Second: wildcard match in domain
        for rule in self.protection_rules:
            if rule.domain == domain and rule.key_pattern == "*":
                return rule
        
        # Third: global wildcard
        for rule in self.protection_rules:
            if rule.domain == "*" and rule.key_pattern == "*":
                return rule
        
        return None
    
    def add_protection_rule(self, rule: ProtectionRule):
        """Add a custom protection rule"""
        self.protection_rules.append(rule)
        self.blocked_values.update([v.lower() for v in rule.block_patterns])
    
    def get_stats(self) -> Dict:
        """Get identity protection statistics"""
        return {
            **self.validation_stats,
            "block_rate": (
                self.validation_stats["blocked"] / self.validation_stats["total_validations"]
                if self.validation_stats["total_validations"] > 0 else 0.0
            ),
            "total_rules": len(self.protection_rules),
            "blocked_values": len(self.blocked_values)
        }
    
    def reset_stats(self):
        """Reset validation statistics"""
        self.validation_stats = {
            "total_validations": 0,
            "passed": 0,
            "blocked": 0,
            "critical_blocks": 0
        }


# ============================================================
# CLI for testing
# ============================================================

if __name__ == "__main__":
    print("🧪 Testing Identity Protection")
    print("=" * 60)
    
    # Create identity protection
    protection = IdentityProtection()
    
    print("\n1️⃣ Test: Validate production fact (HIGH trust)")
    result = protection.validate_fact(
        key="user.name",
        value="Morten",
        domain="identity",
        trust_score=0.95
    )
    print(f"  Result: {'✅ PASS' if result.passed else '❌ BLOCK'}")
    print(f"  Protection level: {result.protection_level.value}")
    if result.blocked_reason:
        print(f"  Reason: {result.blocked_reason}")
    
    print("\n2️⃣ Test: Block test data (Morpheus)")
    result = protection.validate_fact(
        key="user.name",
        value="Morpheus",
        domain="identity",
        trust_score=0.95
    )
    print(f"  Result: {'✅ PASS' if result.passed else '❌ BLOCK'}")
    print(f"  Protection level: {result.protection_level.value}")
    if result.blocked_reason:
        print(f"  Reason: {result.blocked_reason}")
    
    print("\n3️⃣ Test: Block low-trust override")
    result = protection.validate_fact(
        key="user.name",
        value="NewName",
        domain="identity",
        trust_score=0.5
    )
    print(f"  Result: {'✅ PASS' if result.passed else '❌ BLOCK'}")
    print(f"  Protection level: {result.protection_level.value}")
    if result.blocked_reason:
        print(f"  Reason: {result.blocked_reason}")
    
    print("\n4️⃣ Test: Test data detection")
    test_cases = [
        "Morpheus is the user",
        "Morten er brukerens navn",
        "This is a cli_test value",
        "Normal production value"
    ]
    for text in test_cases:
        is_test = protection.detect_test_data(text)
        print(f"  {'🧪 TEST' if is_test else '✅ PROD'}: {text}")
    
    print("\n5️⃣ Test: Isolate test data")
    facts = [
        {"key": "user.name", "value": "Morten", "domain": "identity"},
        {"key": "user.name", "value": "Morpheus", "domain": "identity"},
        {"key": "test.value", "value": "cli_test", "domain": "system"},
        {"key": "real.value", "value": "production", "domain": "system"}
    ]
    isolated = protection.isolate_test_data(facts)
    print(f"  Production: {len(isolated['production'])} facts")
    print(f"  Test: {len(isolated['test'])} facts")
    
    print("\n6️⃣ Stats:")
    stats = protection.get_stats()
    print(f"  Total validations: {stats['total_validations']}")
    print(f"  Passed: {stats['passed']}")
    print(f"  Blocked: {stats['blocked']}")
    print(f"  Critical blocks: {stats['critical_blocks']}")
    print(f"  Block rate: {stats['block_rate']:.1%}")
    print(f"  Total rules: {stats['total_rules']}")
    
    print("\n✅ Identity Protection test complete")
