#!/usr/bin/env python3
"""
self_optimizing_layer.py - Self-Optimizing Symbiosis Layer
===========================================================

System som observerer sin egen ytelse og justerer parametere autonomt.

EVNER, IKKE REGLER - systemet lærer fra erfaring.

ARKITEKTUR (4-layer):
1. OBSERVATION LAYER - Tracker system performance
   - override_rate, conflict_rate, accuracy
   - domain_quality, memory_hit_rate
   - Registreres som system_meta observations

2. META-EVALUATION LAYER (MLC) - Analyser patterns
   - "Hva funker? Hva funker ikke?"
   - Detect degradation, drift, improvement
   - Propose parameter adjustments

3. ADJUSTMENT LAYER - Change parameters
   - promotion_threshold (CMC)
   - temporal_decay_days (Self-Healing)
   - AME override aggressiveness
   - SMM decay_rate
   - DDE domain_weights

4. ANCHORING LAYER - Keep what works
   - Before/after comparison
   - Baseline logic
   - Revert if performance degrades
   - Store successful configs in canonical memory

WORKFLOW:
system operates → metrics collected → patterns analyzed → 
parameters adjusted → effectiveness measured → anchor or revert

INTEGRATION:
- CMC: Stores system_meta observations + parameter configs
- Self-Healing: Applies parameter changes
- Router: Emits performance metrics
- MLC: Provides meta-evaluation logic
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import statistics


class MetricType(Enum):
    """Types of performance metrics"""
    OVERRIDE_RATE = "override_rate"           # How often AME overrides user
    CONFLICT_RATE = "conflict_rate"           # Self-healing conflicts per hour
    ACCURACY = "accuracy"                     # Truth accuracy (when verifiable)
    DOMAIN_QUALITY = "domain_quality"         # Domain detection quality
    MEMORY_HIT_RATE = "memory_hit_rate"       # How often memory is useful
    PROMOTION_SUCCESS = "promotion_success"   # Facts promoted correctly
    TEMPORAL_DECAY_QUALITY = "temporal_decay_quality"  # Decay timing quality


class ParameterType(Enum):
    """System parameters that can be adjusted"""
    PROMOTION_THRESHOLD = "promotion_threshold"           # CMC
    TEMPORAL_DECAY_DAYS = "temporal_decay_days"           # Self-Healing
    AME_OVERRIDE_STRENGTH = "ame_override_strength"       # AME
    SMM_DECAY_RATE = "smm_decay_rate"                     # SMM
    DDE_DOMAIN_WEIGHT = "dde_domain_weight"               # DDE


class AdjustmentResult(Enum):
    """Result of parameter adjustment"""
    IMPROVED = "improved"
    DEGRADED = "degraded"
    NEUTRAL = "neutral"
    PENDING = "pending"


@dataclass
class PerformanceMetric:
    """Single performance observation"""
    metric_id: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "metric_id": self.metric_id,
            "metric_type": self.metric_type.value,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context
        }


@dataclass
class ParameterConfig:
    """Parameter configuration snapshot"""
    config_id: str
    parameter: ParameterType
    value: Any
    timestamp: datetime
    reason: str
    baseline_metrics: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict:
        return {
            "config_id": self.config_id,
            "parameter": self.parameter.value,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "reason": self.reason,
            "baseline_metrics": self.baseline_metrics
        }


@dataclass
class Adjustment:
    """Parameter adjustment record"""
    adjustment_id: str
    parameter: ParameterType
    old_value: Any
    new_value: Any
    reason: str
    timestamp: datetime
    baseline_metrics: Dict[str, float]
    result: AdjustmentResult = AdjustmentResult.PENDING
    result_metrics: Optional[Dict[str, float]] = None
    evaluation_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "adjustment_id": self.adjustment_id,
            "parameter": self.parameter.value,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
            "baseline_metrics": self.baseline_metrics,
            "result": self.result.value,
            "result_metrics": self.result_metrics,
            "evaluation_time": self.evaluation_time.isoformat() if self.evaluation_time else None
        }


class SystemObserver:
    """
    OBSERVATION LAYER
    
    Tracks system performance metrics in real-time.
    Emits observations to canonical memory (system_meta domain).
    """
    
    def __init__(self):
        self.metrics: Dict[str, PerformanceMetric] = {}
        self.metric_history: Dict[MetricType, List[PerformanceMetric]] = {}
        
    def record_metric(
        self,
        metric_type: MetricType,
        value: float,
        context: Optional[Dict] = None
    ) -> PerformanceMetric:
        """
        Record a performance metric.
        
        Args:
            metric_type: Type of metric
            value: Metric value (0.0-1.0 for rates, arbitrary for others)
            context: Optional context (domain, session_id, etc.)
        
        Returns:
            Created PerformanceMetric
        """
        metric_id = f"metric_{metric_type.value}_{datetime.now().timestamp()}"
        
        metric = PerformanceMetric(
            metric_id=metric_id,
            metric_type=metric_type,
            value=value,
            timestamp=datetime.now(),
            context=context or {}
        )
        
        self.metrics[metric_id] = metric
        
        # Update history
        if metric_type not in self.metric_history:
            self.metric_history[metric_type] = []
        self.metric_history[metric_type].append(metric)
        
        return metric
    
    def get_recent_metrics(
        self,
        metric_type: MetricType,
        hours: int = 24
    ) -> List[PerformanceMetric]:
        """Get recent metrics of specific type"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        if metric_type not in self.metric_history:
            return []
        
        return [
            m for m in self.metric_history[metric_type]
            if m.timestamp >= cutoff
        ]
    
    def get_metric_stats(
        self,
        metric_type: MetricType,
        hours: int = 24
    ) -> Dict[str, float]:
        """Get statistical summary of metric"""
        recent = self.get_recent_metrics(metric_type, hours)
        
        if not recent:
            return {}
        
        values = [m.value for m in recent]
        
        return {
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
            "min": min(values),
            "max": max(values),
            "count": len(values)
        }


class MetaEvaluator:
    """
    META-EVALUATION LAYER (MLC enhancement)
    
    Analyzes performance patterns and proposes parameter adjustments.
    
    Logic:
    - High override_rate → reduce AME aggressiveness
    - High conflict_rate → adjust promotion_threshold
    - Low accuracy → increase temporal_decay
    - Poor domain quality → adjust DDE weights
    """
    
    def __init__(self, observer: SystemObserver):
        self.observer = observer
        
        # Thresholds for triggering adjustments (global defaults)
        self.thresholds = {
            MetricType.OVERRIDE_RATE: 0.3,        # >30% overrides = too aggressive
            MetricType.CONFLICT_RATE: 5.0,         # >5 conflicts/hour = too much
            MetricType.ACCURACY: 0.7,              # <70% accuracy = problem
            MetricType.DOMAIN_QUALITY: 0.8,        # <80% quality = poor detection
            MetricType.MEMORY_HIT_RATE: 0.5        # <50% hits = underutilized
        }
        
        # Domain-spesifikke terskler - EFC har lavere toleranse for feil
        self.domain_thresholds = {
            "efc_theory": {
                MetricType.OVERRIDE_RATE: 0.20,    # >20% = for mye tull om EFC
                MetricType.ACCURACY: 0.85,          # <85% = EFC må være presis
                MetricType.CONFLICT_RATE: 2.0       # >2/hour = for mange EFC-konflikter
            },
            "identity": {
                MetricType.OVERRIDE_RATE: 0.15,    # >15% = identitet må beskyttes
                MetricType.ACCURACY: 0.95           # <95% = identitet må være korrekt
            },
            "canonical_memory": {
                MetricType.OVERRIDE_RATE: 0.25,    # >25% = canonical bør vinne
                MetricType.ACCURACY: 0.90
            }
        }
    
    def get_threshold_for_domain(self, metric_type: MetricType, domain: str = "general") -> float:
        """Get threshold adjusted for domain - EFC/identity har strengere krav."""
        if domain in self.domain_thresholds:
            domain_thresh = self.domain_thresholds[domain].get(metric_type)
            if domain_thresh is not None:
                return domain_thresh
        return self.thresholds.get(metric_type, 0.5)
    
    def evaluate_performance(self, hours: int = 24) -> Dict[str, Any]:
        """
        Evaluate system performance over time window.
        
        Returns:
            {
                "metrics": {metric_type: stats},
                "issues": [detected problems],
                "proposed_adjustments": [parameter changes]
            }
        """
        metrics_summary = {}
        issues = []
        proposed = []
        
        # Evaluate each metric type
        for metric_type in MetricType:
            stats = self.observer.get_metric_stats(metric_type, hours)
            
            if not stats:
                continue
            
            metrics_summary[metric_type.value] = stats
            
            # Check thresholds
            threshold = self.thresholds.get(metric_type)
            if threshold is None:
                continue
            
            mean_value = stats["mean"]
            
            # High override rate
            if metric_type == MetricType.OVERRIDE_RATE and mean_value > threshold:
                issues.append({
                    "metric": metric_type.value,
                    "value": mean_value,
                    "threshold": threshold,
                    "description": f"AME override rate too high ({mean_value:.1%})"
                })
                proposed.append({
                    "parameter": ParameterType.AME_OVERRIDE_STRENGTH.value,
                    "action": "decrease",
                    "current": None,  # Will be filled by ParameterAdapter
                    "suggested": None,
                    "reason": f"Reduce aggressiveness due to {mean_value:.1%} override rate"
                })
            
            # High conflict rate
            if metric_type == MetricType.CONFLICT_RATE and mean_value > threshold:
                issues.append({
                    "metric": metric_type.value,
                    "value": mean_value,
                    "threshold": threshold,
                    "description": f"Conflict rate too high ({mean_value:.1f}/hour)"
                })
                proposed.append({
                    "parameter": ParameterType.PROMOTION_THRESHOLD.value,
                    "action": "increase",
                    "current": None,
                    "suggested": None,
                    "reason": f"Increase threshold to reduce conflicts ({mean_value:.1f}/hour)"
                })
            
            # Low accuracy
            if metric_type == MetricType.ACCURACY and mean_value < threshold:
                issues.append({
                    "metric": metric_type.value,
                    "value": mean_value,
                    "threshold": threshold,
                    "description": f"Accuracy too low ({mean_value:.1%})"
                })
                proposed.append({
                    "parameter": ParameterType.TEMPORAL_DECAY_DAYS.value,
                    "action": "decrease",
                    "current": None,
                    "suggested": None,
                    "reason": f"Faster decay to remove stale facts (accuracy: {mean_value:.1%})"
                })
            
            # Poor domain quality
            if metric_type == MetricType.DOMAIN_QUALITY and mean_value < threshold:
                issues.append({
                    "metric": metric_type.value,
                    "value": mean_value,
                    "threshold": threshold,
                    "description": f"Domain detection quality low ({mean_value:.1%})"
                })
                proposed.append({
                    "parameter": ParameterType.DDE_DOMAIN_WEIGHT.value,
                    "action": "adjust",
                    "current": None,
                    "suggested": None,
                    "reason": f"Adjust domain weights (quality: {mean_value:.1%})"
                })
        
        return {
            "metrics": metrics_summary,
            "issues": issues,
            "proposed_adjustments": proposed
        }
    
    def detect_drift(self, metric_type: MetricType, hours: int = 168) -> Optional[Dict]:
        """
        Detect performance drift over time.
        
        Compares recent performance (24h) vs historical baseline (7 days).
        """
        recent = self.observer.get_metric_stats(metric_type, hours=24)
        baseline = self.observer.get_metric_stats(metric_type, hours=hours)
        
        if not recent or not baseline:
            return None
        
        # Calculate drift
        recent_mean = recent["mean"]
        baseline_mean = baseline["mean"]
        
        if baseline_mean == 0:
            return None
        
        drift_percent = ((recent_mean - baseline_mean) / baseline_mean) * 100
        
        # Significant drift?
        if abs(drift_percent) > 20:  # >20% change
            return {
                "metric_type": metric_type.value,
                "recent_mean": recent_mean,
                "baseline_mean": baseline_mean,
                "drift_percent": drift_percent,
                "direction": "degradation" if drift_percent < 0 else "improvement"
            }
        
        return None


class ParameterAdapter:
    """
    ADJUSTMENT LAYER
    
    Applies parameter changes to system components.
    
    Integrates with:
    - CMC (promotion_threshold)
    - Self-Healing (temporal_decay_days)
    - AME (override_strength)
    - SMM (decay_rate)
    - DDE (domain_weights)
    """
    
    def __init__(self):
        self.adjustments: Dict[str, Adjustment] = {}
        self.current_config: Dict[ParameterType, Any] = {}
        
        # Default values
        self.defaults = {
            ParameterType.PROMOTION_THRESHOLD: 3,
            ParameterType.TEMPORAL_DECAY_DAYS: 90,
            ParameterType.AME_OVERRIDE_STRENGTH: 0.5,
            ParameterType.SMM_DECAY_RATE: 0.01,
            ParameterType.DDE_DOMAIN_WEIGHT: 1.0
        }
        
        # Initialize with defaults
        self.current_config = self.defaults.copy()
    
    def adjust_parameter(
        self,
        parameter: ParameterType,
        new_value: Any,
        reason: str,
        baseline_metrics: Dict[str, float]
    ) -> Adjustment:
        """
        Adjust a system parameter.
        
        Args:
            parameter: Parameter to adjust
            new_value: New value
            reason: Why this adjustment is being made
            baseline_metrics: Current performance metrics (for comparison)
        
        Returns:
            Created Adjustment record
        """
        adjustment_id = f"adj_{parameter.value}_{datetime.now().timestamp()}"
        
        old_value = self.current_config.get(parameter)
        
        adjustment = Adjustment(
            adjustment_id=adjustment_id,
            parameter=parameter,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            timestamp=datetime.now(),
            baseline_metrics=baseline_metrics
        )
        
        self.adjustments[adjustment_id] = adjustment
        self.current_config[parameter] = new_value
        
        return adjustment
    
    def get_parameter(self, parameter: ParameterType) -> Any:
        """Get current parameter value"""
        return self.current_config.get(parameter, self.defaults.get(parameter))
    
    def revert_adjustment(self, adjustment_id: str):
        """Revert a parameter adjustment"""
        adjustment = self.adjustments.get(adjustment_id)
        if not adjustment:
            return
        
        # Restore old value
        self.current_config[adjustment.parameter] = adjustment.old_value
        adjustment.result = AdjustmentResult.DEGRADED


class EffectivenessTracker:
    """
    ANCHORING LAYER
    
    Evaluates effectiveness of parameter adjustments.
    Keeps improvements, reverts failures.
    
    Logic:
    - Record baseline metrics before adjustment
    - Wait evaluation_period (e.g., 24 hours)
    - Compare new metrics to baseline
    - If better → anchor (keep)
    - If worse → revert
    """
    
    def __init__(
        self,
        observer: SystemObserver,
        adapter: ParameterAdapter,
        evaluation_period_hours: int = 24
    ):
        self.observer = observer
        self.adapter = adapter
        self.evaluation_period = timedelta(hours=evaluation_period_hours)
        
    def evaluate_adjustment(self, adjustment_id: str) -> AdjustmentResult:
        """
        Evaluate an adjustment after evaluation period.
        
        Returns:
            IMPROVED, DEGRADED, NEUTRAL, or PENDING
        """
        adjustment = self.adapter.adjustments.get(adjustment_id)
        if not adjustment:
            return AdjustmentResult.PENDING
        
        # Check if enough time has passed
        if datetime.now() - adjustment.timestamp < self.evaluation_period:
            return AdjustmentResult.PENDING
        
        # Already evaluated?
        if adjustment.result != AdjustmentResult.PENDING:
            return adjustment.result
        
        # Get new metrics
        result_metrics = {}
        for metric_type in MetricType:
            stats = self.observer.get_metric_stats(metric_type, hours=24)
            if stats:
                result_metrics[metric_type.value] = stats["mean"]
        
        adjustment.result_metrics = result_metrics
        adjustment.evaluation_time = datetime.now()
        
        # Compare to baseline
        baseline = adjustment.baseline_metrics
        
        # Calculate improvement score
        improvement_score = 0
        comparisons = 0
        
        for metric_type_str, baseline_value in baseline.items():
            result_value = result_metrics.get(metric_type_str)
            if result_value is None:
                continue
            
            # For rates (override, conflict): lower is better
            if "rate" in metric_type_str:
                change = baseline_value - result_value  # Positive = improvement
            # For quality metrics (accuracy, domain_quality, hit_rate): higher is better
            else:
                change = result_value - baseline_value  # Positive = improvement
            
            if baseline_value != 0:
                change_percent = (change / baseline_value) * 100
                improvement_score += change_percent
                comparisons += 1
        
        # Determine result
        if comparisons == 0:
            adjustment.result = AdjustmentResult.NEUTRAL
        else:
            avg_improvement = improvement_score / comparisons
            
            if avg_improvement > 5:  # >5% improvement
                adjustment.result = AdjustmentResult.IMPROVED
            elif avg_improvement < -5:  # >5% degradation
                adjustment.result = AdjustmentResult.DEGRADED
                # Revert!
                self.adapter.revert_adjustment(adjustment_id)
            else:
                adjustment.result = AdjustmentResult.NEUTRAL
        
        return adjustment.result
    
    def get_successful_configs(self) -> List[ParameterConfig]:
        """Get all parameter configs that improved performance"""
        successful = []
        
        for adjustment in self.adapter.adjustments.values():
            if adjustment.result == AdjustmentResult.IMPROVED:
                config = ParameterConfig(
                    config_id=f"config_{adjustment.adjustment_id}",
                    parameter=adjustment.parameter,
                    value=adjustment.new_value,
                    timestamp=adjustment.evaluation_time or datetime.now(),
                    reason=adjustment.reason,
                    baseline_metrics=adjustment.result_metrics
                )
                successful.append(config)
        
        return successful


class SelfOptimizingLayer:
    """
    Complete Self-Optimizing Symbiosis Layer.
    
    Coordinates all 4 layers:
    1. SystemObserver - tracks metrics
    2. MetaEvaluator - analyzes patterns
    3. ParameterAdapter - applies changes
    4. EffectivenessTracker - anchors improvements
    
    USAGE:
        sol = SelfOptimizingLayer()
        
        # Record metrics from system operation
        sol.record_metric(MetricType.OVERRIDE_RATE, 0.35)
        
        # Periodic evaluation (e.g., hourly cron)
        sol.evaluate_and_adjust()
        
        # Get current optimal parameters
        params = sol.get_current_parameters()
    """
    
    def __init__(self, evaluation_period_hours: int = 24):
        self.observer = SystemObserver()
        self.evaluator = MetaEvaluator(self.observer)
        self.adapter = ParameterAdapter()
        self.tracker = EffectivenessTracker(
            self.observer,
            self.adapter,
            evaluation_period_hours
        )
        
    def record_metric(
        self,
        metric_type: MetricType,
        value: float,
        context: Optional[Dict] = None
    ) -> PerformanceMetric:
        """Record a performance metric (delegates to observer)"""
        return self.observer.record_metric(metric_type, value, context)
    
    def evaluate_and_adjust(self) -> Dict[str, Any]:
        """
        Main evaluation + adjustment cycle.
        
        Call this periodically (e.g., hourly) to let system self-optimize.
        
        Returns:
            {
                "evaluation": evaluation results,
                "adjustments_made": list of adjustments,
                "evaluations_completed": list of evaluated adjustments
            }
        """
        # 1. Evaluate performance
        evaluation = self.evaluator.evaluate_performance()
        
        # 2. Apply proposed adjustments
        adjustments_made = []
        
        for proposed in evaluation.get("proposed_adjustments", []):
            param_type = ParameterType(proposed["parameter"])
            
            # Calculate new value based on action
            current = self.adapter.get_parameter(param_type)
            
            if proposed["action"] == "increase":
                new_value = current * 1.2  # 20% increase
            elif proposed["action"] == "decrease":
                new_value = current * 0.8  # 20% decrease
            else:  # adjust
                new_value = current * 1.1  # 10% adjustment
            
            # Get baseline metrics
            baseline = {}
            for metric_type in MetricType:
                stats = self.observer.get_metric_stats(metric_type)
                if stats:
                    baseline[metric_type.value] = stats["mean"]
            
            # Apply adjustment
            adjustment = self.adapter.adjust_parameter(
                param_type,
                new_value,
                proposed["reason"],
                baseline
            )
            
            adjustments_made.append(adjustment.to_dict())
        
        # 3. Evaluate pending adjustments
        evaluations_completed = []
        
        for adj_id, adjustment in self.adapter.adjustments.items():
            if adjustment.result == AdjustmentResult.PENDING:
                result = self.tracker.evaluate_adjustment(adj_id)
                
                if result != AdjustmentResult.PENDING:
                    evaluations_completed.append({
                        "adjustment_id": adj_id,
                        "parameter": adjustment.parameter.value,
                        "result": result.value,
                        "old_value": adjustment.old_value,
                        "new_value": adjustment.new_value
                    })
        
        return {
            "evaluation": evaluation,
            "adjustments_made": adjustments_made,
            "evaluations_completed": evaluations_completed
        }
    
    def get_current_parameters(self) -> Dict[str, Any]:
        """Get current optimal parameter values"""
        return {
            param.value: value
            for param, value in self.adapter.current_config.items()
        }
    
    def get_stats(self) -> Dict:
        """Get system statistics"""
        total_adjustments = len(self.adapter.adjustments)
        
        result_counts = {
            "improved": 0,
            "degraded": 0,
            "neutral": 0,
            "pending": 0
        }
        
        for adjustment in self.adapter.adjustments.values():
            result_counts[adjustment.result.value] += 1
        
        return {
            "total_metrics": len(self.observer.metrics),
            "total_adjustments": total_adjustments,
            "adjustment_results": result_counts,
            "successful_adjustments": result_counts["improved"],
            "success_rate": result_counts["improved"] / total_adjustments if total_adjustments > 0 else 0.0
        }


# ============================================================
# CLI for testing
# ============================================================

if __name__ == "__main__":
    print("🧪 Testing Self-Optimizing Layer")
    print("=" * 60)
    
    sol = SelfOptimizingLayer(evaluation_period_hours=0)  # Instant eval for testing
    
    # Test 1: Record high override rate (trigger adjustment)
    print("\n1️⃣ Record high override rate")
    for i in range(10):
        sol.record_metric(MetricType.OVERRIDE_RATE, 0.4)  # 40% > 30% threshold
    
    # Test 2: Evaluate and adjust
    print("\n2️⃣ Evaluate and adjust")
    result = sol.evaluate_and_adjust()
    
    print(f"Issues detected: {len(result['evaluation']['issues'])}")
    for issue in result["evaluation"]["issues"]:
        print(f"  - {issue['description']}")
    
    print(f"Adjustments made: {len(result['adjustments_made'])}")
    for adj in result["adjustments_made"]:
        print(f"  - {adj['parameter']}: {adj['old_value']} → {adj['new_value']}")
        print(f"    Reason: {adj['reason']}")
    
    # Test 3: Get current parameters
    print("\n3️⃣ Current parameters")
    params = sol.get_current_parameters()
    for param, value in params.items():
        print(f"  {param}: {value}")
    
    # Test 4: Stats
    print("\n4️⃣ System stats")
    stats = sol.get_stats()
    print(json.dumps(stats, indent=2))
    
    print("\n✅ Self-Optimizing Layer test complete")
