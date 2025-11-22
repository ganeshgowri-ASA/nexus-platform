"""Unit tests for statistical analysis engine."""

import pytest
from modules.ab_testing.core.statistics import StatisticalAnalyzer, VariantData


class TestStatisticalAnalyzer:
    """Test suite for StatisticalAnalyzer."""

    def test_calculate_sample_size(self):
        """Test sample size calculation."""
        analyzer = StatisticalAnalyzer()
        result = analyzer.calculate_sample_size(
            baseline_conversion_rate=0.1,
            minimum_detectable_effect=0.2,
            power=0.8,
            significance_level=0.05,
        )

        assert result.required_sample_size > 0
        assert result.baseline_conversion_rate == 0.1
        assert result.minimum_detectable_effect == 0.2
        assert result.power == 0.8
        assert result.significance_level == 0.05

    def test_z_test_significant_difference(self):
        """Test Z-test with significant difference."""
        analyzer = StatisticalAnalyzer()

        control = VariantData(name="Control", conversions=100, total=1000)
        treatment = VariantData(name="Treatment", conversions=150, total=1000)

        result = analyzer.z_test(control, treatment, confidence_level=0.95)

        assert result.p_value < 0.05
        assert result.is_significant is True
        assert result.winner == "Treatment"
        assert result.relative_improvement is not None
        assert result.relative_improvement > 0

    def test_z_test_no_significant_difference(self):
        """Test Z-test with no significant difference."""
        analyzer = StatisticalAnalyzer()

        control = VariantData(name="Control", conversions=100, total=1000)
        treatment = VariantData(name="Treatment", conversions=105, total=1000)

        result = analyzer.z_test(control, treatment, confidence_level=0.95)

        # Small difference should not be significant
        assert result.is_significant is False
        assert result.winner is None

    def test_t_test(self):
        """Test independent t-test."""
        analyzer = StatisticalAnalyzer()

        values_a = [10.5, 20.3, 15.7, 12.1, 18.9] * 20  # 100 values
        values_b = [12.1, 22.5, 18.9, 14.3, 21.7] * 20  # 100 values

        result = analyzer.t_test(values_a, values_b, confidence_level=0.95)

        assert result.p_value is not None
        assert isinstance(result.is_significant, bool)
        assert result.confidence_interval is not None

    def test_bayesian_probability_to_win(self):
        """Test Bayesian probability calculation."""
        analyzer = StatisticalAnalyzer()

        control = VariantData(name="Control", conversions=100, total=1000)
        treatment = VariantData(name="Treatment", conversions=150, total=1000)

        probs = analyzer.bayesian_probability_to_win(control, treatment, n_simulations=10000)

        assert "A" in probs
        assert "B" in probs
        assert 0 <= probs["A"] <= 1
        assert 0 <= probs["B"] <= 1
        assert abs(probs["A"] + probs["B"] - 1.0) < 0.01  # Should sum to ~1.0

    def test_sequential_testing(self):
        """Test sequential probability ratio test."""
        analyzer = StatisticalAnalyzer()

        control = VariantData(name="Control", conversions=100, total=1000)
        treatment = VariantData(name="Treatment", conversions=150, total=1000)

        result = analyzer.sequential_testing(control, treatment)

        assert "decision" in result
        assert "log_likelihood_ratio" in result
        assert result["decision"] in ["A_wins", "B_wins", "continue"]

    def test_variant_data_conversion_rate(self):
        """Test VariantData conversion rate calculation."""
        variant = VariantData(name="Test", conversions=150, total=1000)

        assert variant.conversion_rate == 0.15

    def test_variant_data_zero_total(self):
        """Test VariantData with zero total."""
        variant = VariantData(name="Test", conversions=0, total=0)

        assert variant.conversion_rate == 0.0

    def test_variant_data_revenue(self):
        """Test VariantData revenue calculation."""
        variant = VariantData(name="Test", conversions=100, total=1000, revenue=5000.0)

        assert variant.average_revenue == 5.0

    def test_sample_size_edge_cases(self):
        """Test sample size calculation edge cases."""
        analyzer = StatisticalAnalyzer()

        # Very small baseline
        result = analyzer.calculate_sample_size(
            baseline_conversion_rate=0.01,
            minimum_detectable_effect=0.5,
            power=0.8,
            significance_level=0.05,
        )
        assert result.required_sample_size > 0

        # Very high baseline
        result = analyzer.calculate_sample_size(
            baseline_conversion_rate=0.5,
            minimum_detectable_effect=0.1,
            power=0.8,
            significance_level=0.05,
        )
        assert result.required_sample_size > 0
