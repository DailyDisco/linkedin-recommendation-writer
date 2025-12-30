"""Tests for the A/B testing experiment service."""

import pytest
from datetime import datetime

# Import test - this will be tested when pytest runs
from app.services.ai.experiment_service import (
    ExperimentService,
    ExperimentVariant,
    ExperimentConfig,
    ExperimentResult,
)


class TestExperimentService:
    """Tests for ExperimentService."""

    def test_initialization(self):
        """Test service initializes correctly."""
        service = ExperimentService(enabled=True)
        assert service.enabled is True
        assert len(service._results) == 0

    def test_disabled_returns_baseline(self):
        """Test disabled service always returns baseline."""
        service = ExperimentService(enabled=False)
        variant = service.get_variant("test_user")
        assert variant == ExperimentVariant.BASELINE

    def test_force_variant(self):
        """Test forcing a specific variant."""
        service = ExperimentService(enabled=True)
        variant = service.get_variant(
            "test_user",
            force_variant=ExperimentVariant.STORY_FIRST,
        )
        assert variant == ExperimentVariant.STORY_FIRST

    def test_consistent_assignment(self):
        """Test same user gets same variant on same day."""
        service = ExperimentService(enabled=True)
        variant1 = service.get_variant("consistent_user")
        variant2 = service.get_variant("consistent_user")
        assert variant1 == variant2

    def test_get_variant_config(self):
        """Test getting variant configuration."""
        service = ExperimentService(enabled=True)
        config = service.get_variant_config(ExperimentVariant.STORY_FIRST)
        assert config.variant == ExperimentVariant.STORY_FIRST
        assert len(config.prompt_additions) > 0

    def test_apply_variant_to_prompt(self):
        """Test applying variant modifications to prompt."""
        service = ExperimentService(enabled=True)
        base_prompt = "Write a recommendation."
        modified = service.apply_variant_to_prompt(
            base_prompt,
            ExperimentVariant.STORY_FIRST,
        )
        assert base_prompt in modified
        assert "EXPERIMENT" in modified
        assert "story" in modified.lower() or "narrative" in modified.lower()

    def test_log_result(self):
        """Test logging experiment results."""
        service = ExperimentService(enabled=True)

        experiment_id = service.log_result(
            variant=ExperimentVariant.BASELINE,
            username="test_user",
            quality_score=75.5,
            validation_results={"test": True},
            user_selected=True,
            generation_time_ms=1500,
        )

        assert experiment_id is not None
        assert len(experiment_id) == 12
        assert len(service._results) == 1

    def test_variant_stats(self):
        """Test aggregate statistics calculation."""
        service = ExperimentService(enabled=True)

        # Log multiple results
        for score in [70, 80, 90]:
            service.log_result(
                variant=ExperimentVariant.BASELINE,
                username=f"user_{score}",
                quality_score=score,
                validation_results={},
            )

        stats = service.get_variant_stats()
        assert "baseline" in stats
        assert stats["baseline"]["sample_count"] == 3
        assert stats["baseline"]["avg_quality_score"] == 80.0

    def test_get_best_variant(self):
        """Test finding best performing variant."""
        service = ExperimentService(enabled=True)

        # Log results for different variants
        for i in range(15):
            service.log_result(
                variant=ExperimentVariant.BASELINE,
                username=f"baseline_user_{i}",
                quality_score=70,
                validation_results={},
            )
            service.log_result(
                variant=ExperimentVariant.STORY_FIRST,
                username=f"story_user_{i}",
                quality_score=85,
                validation_results={},
            )

        best = service.get_best_variant(min_samples=10)
        assert best == ExperimentVariant.STORY_FIRST

    def test_export_results_json(self):
        """Test exporting results to JSON."""
        service = ExperimentService(enabled=True)
        service.log_result(
            variant=ExperimentVariant.BASELINE,
            username="export_test",
            quality_score=75,
            validation_results={},
        )

        json_export = service.export_results(format="json")
        assert "export_test" in json_export
        assert "baseline" in json_export

    def test_export_results_csv(self):
        """Test exporting results to CSV."""
        service = ExperimentService(enabled=True)
        service.log_result(
            variant=ExperimentVariant.BASELINE,
            username="csv_test",
            quality_score=80,
            validation_results={},
        )

        csv_export = service.export_results(format="csv")
        assert "experiment_id" in csv_export
        assert "csv_test" in csv_export

    def test_clear_results(self):
        """Test clearing stored results."""
        service = ExperimentService(enabled=True)
        service.log_result(
            variant=ExperimentVariant.BASELINE,
            username="clear_test",
            quality_score=75,
            validation_results={},
        )

        count = service.clear_results()
        assert count == 1
        assert len(service._results) == 0

    def test_temperature_modifier(self):
        """Test getting temperature modifiers for variants."""
        service = ExperimentService(enabled=True)

        # Baseline should have 0 modifier
        assert service.get_temperature_modifier(ExperimentVariant.BASELINE) == 0.0

        # Story first should have positive modifier
        assert service.get_temperature_modifier(ExperimentVariant.STORY_FIRST) > 0

        # Evidence heavy should have negative modifier
        assert service.get_temperature_modifier(ExperimentVariant.EVIDENCE_HEAVY) < 0
