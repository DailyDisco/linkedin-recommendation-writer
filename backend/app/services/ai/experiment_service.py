"""A/B Testing Infrastructure for prompt and generation experiments.

This module provides infrastructure for:
- Tracking prompt variation effectiveness
- Measuring quality scores across different approaches
- Logging experiment results for analysis
- Supporting gradual rollout of improvements
"""

import hashlib
import json
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ExperimentVariant(Enum):
    """Available experiment variants for recommendation generation."""

    BASELINE = "baseline"
    FEW_SHOT_HEAVY = "few_shot_heavy"  # More few-shot examples
    STORY_FIRST = "story_first"  # Lead with narrative structure
    EVIDENCE_HEAVY = "evidence_heavy"  # More data points emphasized
    EMOTIONAL_FOCUS = "emotional_focus"  # Focus on relationship/emotions
    CONCISE = "concise"  # Shorter, punchier recommendations


@dataclass
class ExperimentConfig:
    """Configuration for an experiment variant."""

    variant: ExperimentVariant
    description: str
    temperature_modifier: float = 0.0
    prompt_additions: List[str] = field(default_factory=list)
    weight: float = 1.0  # Relative weight for random assignment
    enabled: bool = True


@dataclass
class ExperimentResult:
    """Result of a single experiment run."""

    experiment_id: str
    variant: str
    timestamp: str
    github_username: str
    quality_score: float
    validation_results: Dict[str, Any]
    user_selected: Optional[bool] = None  # True if user chose this option
    generation_time_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExperimentService:
    """Service for managing A/B testing experiments on recommendation generation.

    This service allows tracking which prompt variations produce the highest
    quality recommendations, enabling data-driven improvements over time.

    Usage:
        experiment_service = ExperimentService()

        # Get a variant for this generation
        variant = experiment_service.get_variant(username="octocat")

        # Apply variant modifications to generation
        config = experiment_service.get_variant_config(variant)

        # After generation, log the result
        experiment_service.log_result(
            variant=variant,
            username="octocat",
            quality_score=75.5,
            validation_results={...},
            user_selected=True,
        )

        # Get aggregate stats
        stats = experiment_service.get_variant_stats()
    """

    # Experiment configurations for each variant
    VARIANT_CONFIGS: Dict[ExperimentVariant, ExperimentConfig] = {
        ExperimentVariant.BASELINE: ExperimentConfig(
            variant=ExperimentVariant.BASELINE,
            description="Standard generation with default prompts",
            temperature_modifier=0.0,
            weight=2.0,  # Baseline gets more weight
        ),
        ExperimentVariant.FEW_SHOT_HEAVY: ExperimentConfig(
            variant=ExperimentVariant.FEW_SHOT_HEAVY,
            description="Include multiple few-shot examples in prompt",
            temperature_modifier=-0.05,
            prompt_additions=[
                "Study the excellent examples provided very carefully.",
                "Your output should match the quality and specificity of the examples.",
            ],
            weight=1.0,
        ),
        ExperimentVariant.STORY_FIRST: ExperimentConfig(
            variant=ExperimentVariant.STORY_FIRST,
            description="Lead with narrative structure and specific incidents",
            temperature_modifier=0.05,
            prompt_additions=[
                "Start with a specific incident or story that showcases their abilities.",
                "Lead with action and context, not with generic praise.",
                "The first sentence should hook the reader with a concrete example.",
            ],
            weight=1.0,
        ),
        ExperimentVariant.EVIDENCE_HEAVY: ExperimentConfig(
            variant=ExperimentVariant.EVIDENCE_HEAVY,
            description="Emphasize concrete data points and technical details",
            temperature_modifier=-0.1,
            prompt_additions=[
                "Include specific technical details from their GitHub profile.",
                "Mention at least 2-3 specific technologies or skills.",
                "Reference their actual contribution patterns and metrics.",
            ],
            weight=1.0,
        ),
        ExperimentVariant.EMOTIONAL_FOCUS: ExperimentConfig(
            variant=ExperimentVariant.EMOTIONAL_FOCUS,
            description="Focus on relationship and personal appreciation",
            temperature_modifier=0.1,
            prompt_additions=[
                "Express genuine appreciation and personal observations.",
                "Focus on how working with them felt, not just what they did.",
                "Include emotional language that shows authentic connection.",
            ],
            weight=1.0,
        ),
        ExperimentVariant.CONCISE: ExperimentConfig(
            variant=ExperimentVariant.CONCISE,
            description="Shorter, more impactful recommendations",
            temperature_modifier=0.0,
            prompt_additions=[
                "Be concise and impactful - every word should count.",
                "Remove any filler or generic phrases.",
                "Aim for maximum impact with minimum words.",
            ],
            weight=0.5,  # Less common variant
        ),
    }

    def __init__(self, enabled: bool = True, storage_backend: Optional[str] = None):
        """Initialize the experiment service.

        Args:
            enabled: Whether A/B testing is enabled
            storage_backend: Optional storage backend for results (future: 'redis', 'postgres')
        """
        self.enabled = enabled
        self.storage_backend = storage_backend
        self._results: List[ExperimentResult] = []  # In-memory storage (replace with persistent)
        self._variant_stats: Dict[str, Dict[str, Any]] = {}

        logger.info(f"🧪 ExperimentService initialized (enabled={enabled})")

    def get_variant(
        self,
        username: str,
        force_variant: Optional[ExperimentVariant] = None,
    ) -> ExperimentVariant:
        """Get an experiment variant for this generation.

        Uses consistent hashing so the same user gets the same variant
        across multiple requests (unless force_variant is specified).

        Args:
            username: GitHub username (used for consistent assignment)
            force_variant: Optional variant to force (for testing)

        Returns:
            The assigned experiment variant
        """
        if not self.enabled:
            return ExperimentVariant.BASELINE

        if force_variant is not None:
            logger.debug(f"🧪 Forced variant: {force_variant.value}")
            return force_variant

        # Get enabled variants with their weights
        enabled_variants = [(variant, config) for variant, config in self.VARIANT_CONFIGS.items() if config.enabled]

        if not enabled_variants:
            return ExperimentVariant.BASELINE

        # Use consistent hashing for stable assignment
        hash_input = f"{username}:{datetime.now().strftime('%Y-%m-%d')}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)

        # Calculate total weight
        total_weight = sum(config.weight for _, config in enabled_variants)

        # Select variant based on hash
        threshold = (hash_value % 1000) / 1000.0 * total_weight
        cumulative = 0.0

        for variant, config in enabled_variants:
            cumulative += config.weight
            if threshold <= cumulative:
                logger.debug(f"🧪 Assigned variant: {variant.value} for {username}")
                return variant

        return ExperimentVariant.BASELINE

    def get_variant_config(self, variant: ExperimentVariant) -> ExperimentConfig:
        """Get configuration for a specific variant.

        Args:
            variant: The experiment variant

        Returns:
            Configuration for the variant
        """
        return self.VARIANT_CONFIGS.get(
            variant,
            self.VARIANT_CONFIGS[ExperimentVariant.BASELINE],
        )

    def apply_variant_to_prompt(
        self,
        base_prompt: str,
        variant: ExperimentVariant,
    ) -> str:
        """Apply variant-specific modifications to a prompt.

        Args:
            base_prompt: The base prompt
            variant: The experiment variant

        Returns:
            Modified prompt with variant additions
        """
        config = self.get_variant_config(variant)

        if not config.prompt_additions:
            return base_prompt

        additions = "\n".join(
            [
                "",
                "=" * 40,
                f"EXPERIMENT: {config.description}",
                "=" * 40,
                *config.prompt_additions,
                "",
            ]
        )

        return base_prompt + additions

    def get_temperature_modifier(self, variant: ExperimentVariant) -> float:
        """Get temperature modifier for a variant.

        Args:
            variant: The experiment variant

        Returns:
            Temperature modifier to apply
        """
        config = self.get_variant_config(variant)
        return config.temperature_modifier

    def log_result(
        self,
        variant: ExperimentVariant,
        username: str,
        quality_score: float,
        validation_results: Dict[str, Any],
        user_selected: Optional[bool] = None,
        generation_time_ms: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Log an experiment result.

        Args:
            variant: The variant used
            username: GitHub username
            quality_score: Overall quality score (0-100)
            validation_results: Detailed validation results
            user_selected: Whether user selected this option
            generation_time_ms: Time taken for generation
            metadata: Additional metadata

        Returns:
            Experiment ID for tracking
        """
        experiment_id = hashlib.md5(f"{variant.value}:{username}:{datetime.now().isoformat()}".encode()).hexdigest()[:12]

        result = ExperimentResult(
            experiment_id=experiment_id,
            variant=variant.value,
            timestamp=datetime.now().isoformat(),
            github_username=username,
            quality_score=quality_score,
            validation_results=validation_results,
            user_selected=user_selected,
            generation_time_ms=generation_time_ms,
            metadata=metadata or {},
        )

        self._results.append(result)
        self._update_variant_stats(result)

        logger.info(f"🧪 Experiment logged: {experiment_id} | " f"variant={variant.value} | score={quality_score:.1f}")

        return experiment_id

    def _update_variant_stats(self, result: ExperimentResult) -> None:
        """Update running statistics for a variant."""
        variant = result.variant

        if variant not in self._variant_stats:
            self._variant_stats[variant] = {
                "count": 0,
                "total_score": 0.0,
                "scores": [],
                "selected_count": 0,
                "total_time_ms": 0,
            }

        stats = self._variant_stats[variant]
        stats["count"] += 1
        stats["total_score"] += result.quality_score
        stats["scores"].append(result.quality_score)
        stats["total_time_ms"] += result.generation_time_ms

        if result.user_selected:
            stats["selected_count"] += 1

    def get_variant_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get aggregate statistics for all variants.

        Returns:
            Dict mapping variant name to statistics
        """
        stats = {}

        for variant, data in self._variant_stats.items():
            count = data["count"]
            if count == 0:
                continue

            scores = data["scores"]
            avg_score = data["total_score"] / count
            avg_time = data["total_time_ms"] / count

            # Calculate standard deviation
            variance = sum((s - avg_score) ** 2 for s in scores) / count
            std_dev = variance**0.5

            stats[variant] = {
                "sample_count": count,
                "avg_quality_score": round(avg_score, 2),
                "std_dev": round(std_dev, 2),
                "min_score": min(scores),
                "max_score": max(scores),
                "selection_rate": (round(data["selected_count"] / count * 100, 1) if count > 0 else 0),
                "avg_generation_time_ms": round(avg_time, 1),
            }

        return stats

    def get_best_variant(self, min_samples: int = 10) -> Optional[ExperimentVariant]:
        """Get the best performing variant based on quality scores.

        Args:
            min_samples: Minimum samples required for consideration

        Returns:
            Best performing variant, or None if insufficient data
        """
        stats = self.get_variant_stats()

        eligible = [(variant, data) for variant, data in stats.items() if data["sample_count"] >= min_samples]

        if not eligible:
            return None

        best = max(eligible, key=lambda x: x[1]["avg_quality_score"])
        return ExperimentVariant(best[0])

    def export_results(self, format: str = "json") -> str:
        """Export experiment results for analysis.

        Args:
            format: Export format ('json' or 'csv')

        Returns:
            Exported data as string
        """
        if format == "json":
            return json.dumps(
                [
                    {
                        "experiment_id": r.experiment_id,
                        "variant": r.variant,
                        "timestamp": r.timestamp,
                        "github_username": r.github_username,
                        "quality_score": r.quality_score,
                        "user_selected": r.user_selected,
                        "generation_time_ms": r.generation_time_ms,
                    }
                    for r in self._results
                ],
                indent=2,
            )
        elif format == "csv":
            lines = ["experiment_id,variant,timestamp,github_username,quality_score,user_selected,generation_time_ms"]
            for r in self._results:
                lines.append(f"{r.experiment_id},{r.variant},{r.timestamp}," f"{r.github_username},{r.quality_score},{r.user_selected},{r.generation_time_ms}")
            return "\n".join(lines)
        else:
            raise ValueError(f"Unknown format: {format}")

    def clear_results(self) -> int:
        """Clear all stored results (for testing).

        Returns:
            Number of results cleared
        """
        count = len(self._results)
        self._results = []
        self._variant_stats = {}
        logger.info(f"🧪 Cleared {count} experiment results")
        return count


# Global experiment service instance
experiment_service = ExperimentService(enabled=True)


def get_experiment_service() -> ExperimentService:
    """Get the global experiment service instance."""
    return experiment_service
