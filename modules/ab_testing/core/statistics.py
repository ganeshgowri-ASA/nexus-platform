"""Statistical analysis engine for A/B testing."""

import math
from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy import stats
from loguru import logger


@dataclass
class VariantData:
    """Data container for a single variant."""

    name: str
    conversions: int
    total: int
    revenue: Optional[float] = None

    @property
    def conversion_rate(self) -> float:
        """Calculate conversion rate."""
        return self.conversions / self.total if self.total > 0 else 0.0

    @property
    def average_revenue(self) -> float:
        """Calculate average revenue per participant."""
        if self.revenue is None or self.total == 0:
            return 0.0
        return self.revenue / self.total


@dataclass
class TestResult:
    """Result of a statistical test."""

    variant_a: str
    variant_b: str
    p_value: float
    is_significant: bool
    confidence_level: float
    effect_size: float
    confidence_interval: tuple[float, float]
    winner: Optional[str] = None
    relative_improvement: Optional[float] = None


@dataclass
class SampleSizeResult:
    """Result of sample size calculation."""

    required_sample_size: int
    baseline_conversion_rate: float
    minimum_detectable_effect: float
    power: float
    significance_level: float


class StatisticalAnalyzer:
    """
    Statistical analysis engine for A/B testing.

    Provides methods for:
    - Statistical significance testing (Z-test, T-test, Chi-square)
    - Confidence interval calculation
    - Sample size calculation
    - Effect size measurement
    - Winner detection
    """

    @staticmethod
    def calculate_sample_size(
        baseline_conversion_rate: float,
        minimum_detectable_effect: float,
        power: float = 0.8,
        significance_level: float = 0.05,
    ) -> SampleSizeResult:
        """
        Calculate required sample size for an A/B test.

        Uses the formula for comparing two proportions.

        Args:
            baseline_conversion_rate: Expected conversion rate of control (0.0-1.0)
            minimum_detectable_effect: Minimum effect size to detect (e.g., 0.1 for 10%)
            power: Statistical power (1 - beta), typically 0.8
            significance_level: Significance level (alpha), typically 0.05

        Returns:
            SampleSizeResult: Required sample size and parameters

        Example:
            >>> analyzer = StatisticalAnalyzer()
            >>> result = analyzer.calculate_sample_size(
            ...     baseline_conversion_rate=0.1,
            ...     minimum_detectable_effect=0.2,
            ...     power=0.8,
            ...     significance_level=0.05
            ... )
            >>> print(f"Required sample size: {result.required_sample_size}")
        """
        logger.info(
            f"Calculating sample size for baseline={baseline_conversion_rate}, "
            f"MDE={minimum_detectable_effect}"
        )

        # Calculate effect size (relative difference)
        p1 = baseline_conversion_rate
        p2 = baseline_conversion_rate * (1 + minimum_detectable_effect)

        # Pooled proportion
        p_pooled = (p1 + p2) / 2

        # Z-scores for power and significance
        z_alpha = stats.norm.ppf(1 - significance_level / 2)
        z_beta = stats.norm.ppf(power)

        # Sample size formula for two proportions
        numerator = (z_alpha + z_beta) ** 2 * (p1 * (1 - p1) + p2 * (1 - p2))
        denominator = (p2 - p1) ** 2

        sample_size_per_variant = int(math.ceil(numerator / denominator))

        result = SampleSizeResult(
            required_sample_size=sample_size_per_variant,
            baseline_conversion_rate=baseline_conversion_rate,
            minimum_detectable_effect=minimum_detectable_effect,
            power=power,
            significance_level=significance_level,
        )

        logger.info(f"Required sample size: {sample_size_per_variant} per variant")
        return result

    @staticmethod
    def z_test(
        variant_a: VariantData,
        variant_b: VariantData,
        confidence_level: float = 0.95,
    ) -> TestResult:
        """
        Perform Z-test for comparing two proportions (conversion rates).

        Args:
            variant_a: Data for variant A (typically control)
            variant_b: Data for variant B (typically treatment)
            confidence_level: Confidence level for the test (e.g., 0.95)

        Returns:
            TestResult: Statistical test results

        Example:
            >>> control = VariantData(name="Control", conversions=100, total=1000)
            >>> treatment = VariantData(name="Treatment", conversions=120, total=1000)
            >>> result = StatisticalAnalyzer.z_test(control, treatment)
            >>> print(f"P-value: {result.p_value}")
            >>> print(f"Significant: {result.is_significant}")
        """
        logger.info(f"Running Z-test: {variant_a.name} vs {variant_b.name}")

        p1 = variant_a.conversion_rate
        p2 = variant_b.conversion_rate
        n1 = variant_a.total
        n2 = variant_b.total

        # Pooled proportion
        p_pooled = (variant_a.conversions + variant_b.conversions) / (n1 + n2)

        # Standard error
        se = math.sqrt(p_pooled * (1 - p_pooled) * (1 / n1 + 1 / n2))

        # Z-score
        if se == 0:
            z_score = 0.0
        else:
            z_score = (p2 - p1) / se

        # P-value (two-tailed test)
        p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))

        # Significance
        significance_level = 1 - confidence_level
        is_significant = p_value < significance_level

        # Effect size (Cohen's h)
        effect_size = 2 * (math.asin(math.sqrt(p2)) - math.asin(math.sqrt(p1)))

        # Confidence interval for difference in proportions
        se_diff = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
        z_critical = stats.norm.ppf(1 - significance_level / 2)
        margin = z_critical * se_diff
        ci_lower = (p2 - p1) - margin
        ci_upper = (p2 - p1) + margin

        # Determine winner
        winner = None
        relative_improvement = None
        if is_significant:
            if p2 > p1:
                winner = variant_b.name
                relative_improvement = (p2 - p1) / p1 if p1 > 0 else None
            elif p1 > p2:
                winner = variant_a.name
                relative_improvement = (p1 - p2) / p2 if p2 > 0 else None

        result = TestResult(
            variant_a=variant_a.name,
            variant_b=variant_b.name,
            p_value=p_value,
            is_significant=is_significant,
            confidence_level=confidence_level,
            effect_size=effect_size,
            confidence_interval=(ci_lower, ci_upper),
            winner=winner,
            relative_improvement=relative_improvement,
        )

        logger.info(
            f"Z-test result: p-value={p_value:.4f}, "
            f"significant={is_significant}, winner={winner}"
        )

        return result

    @staticmethod
    def t_test(
        values_a: list[float],
        values_b: list[float],
        confidence_level: float = 0.95,
    ) -> TestResult:
        """
        Perform independent two-sample t-test (e.g., for revenue comparison).

        Args:
            values_a: Values for variant A
            values_b: Values for variant B
            confidence_level: Confidence level for the test

        Returns:
            TestResult: Statistical test results

        Example:
            >>> revenue_control = [10.5, 20.3, 15.7, ...]
            >>> revenue_treatment = [12.1, 22.5, 18.9, ...]
            >>> result = StatisticalAnalyzer.t_test(revenue_control, revenue_treatment)
        """
        logger.info("Running independent t-test")

        # Convert to numpy arrays
        a = np.array(values_a)
        b = np.array(values_b)

        # Perform t-test
        t_stat, p_value = stats.ttest_ind(a, b, equal_var=False)

        # Significance
        significance_level = 1 - confidence_level
        is_significant = p_value < significance_level

        # Effect size (Cohen's d)
        pooled_std = math.sqrt(
            ((len(a) - 1) * np.var(a, ddof=1) + (len(b) - 1) * np.var(b, ddof=1))
            / (len(a) + len(b) - 2)
        )
        effect_size = (np.mean(b) - np.mean(a)) / pooled_std if pooled_std > 0 else 0.0

        # Confidence interval
        se_diff = math.sqrt(np.var(a, ddof=1) / len(a) + np.var(b, ddof=1) / len(b))
        df = len(a) + len(b) - 2
        t_critical = stats.t.ppf(1 - significance_level / 2, df)
        margin = t_critical * se_diff
        mean_diff = np.mean(b) - np.mean(a)
        ci_lower = mean_diff - margin
        ci_upper = mean_diff + margin

        # Determine winner
        winner = None
        relative_improvement = None
        if is_significant:
            mean_a = np.mean(a)
            mean_b = np.mean(b)
            if mean_b > mean_a:
                winner = "B"
                relative_improvement = (mean_b - mean_a) / mean_a if mean_a > 0 else None
            elif mean_a > mean_b:
                winner = "A"
                relative_improvement = (mean_a - mean_b) / mean_b if mean_b > 0 else None

        result = TestResult(
            variant_a="A",
            variant_b="B",
            p_value=p_value,
            is_significant=is_significant,
            confidence_level=confidence_level,
            effect_size=effect_size,
            confidence_interval=(ci_lower, ci_upper),
            winner=winner,
            relative_improvement=relative_improvement,
        )

        logger.info(
            f"T-test result: p-value={p_value:.4f}, "
            f"significant={is_significant}, winner={winner}"
        )

        return result

    @staticmethod
    def bayesian_probability_to_win(
        variant_a: VariantData,
        variant_b: VariantData,
        n_simulations: int = 100000,
    ) -> dict[str, float]:
        """
        Calculate Bayesian probability that each variant is the winner.

        Uses Beta distribution for conversion rates.

        Args:
            variant_a: Data for variant A
            variant_b: Data for variant B
            n_simulations: Number of Monte Carlo simulations

        Returns:
            dict: Probability to win for each variant

        Example:
            >>> control = VariantData(name="Control", conversions=100, total=1000)
            >>> treatment = VariantData(name="Treatment", conversions=120, total=1000)
            >>> probs = StatisticalAnalyzer.bayesian_probability_to_win(
            ...     control, treatment
            ... )
            >>> print(f"Control P(win): {probs['A']:.2%}")
            >>> print(f"Treatment P(win): {probs['B']:.2%}")
        """
        logger.info("Calculating Bayesian probability to win")

        # Beta distribution parameters (using non-informative prior)
        alpha_a = variant_a.conversions + 1
        beta_a = variant_a.total - variant_a.conversions + 1
        alpha_b = variant_b.conversions + 1
        beta_b = variant_b.total - variant_b.conversions + 1

        # Sample from Beta distributions
        samples_a = np.random.beta(alpha_a, beta_a, n_simulations)
        samples_b = np.random.beta(alpha_b, beta_b, n_simulations)

        # Calculate probability that B > A
        prob_b_wins = np.mean(samples_b > samples_a)
        prob_a_wins = 1 - prob_b_wins

        result = {
            "A": prob_a_wins,
            "B": prob_b_wins,
        }

        logger.info(f"Bayesian results: P(A wins)={prob_a_wins:.2%}, P(B wins)={prob_b_wins:.2%}")

        return result

    @staticmethod
    def sequential_testing(
        variant_a: VariantData,
        variant_b: VariantData,
        alpha: float = 0.05,
        beta: float = 0.2,
    ) -> dict[str, any]:
        """
        Perform sequential probability ratio test (SPRT).

        Allows for early stopping when sufficient evidence is gathered.

        Args:
            variant_a: Data for variant A
            variant_b: Data for variant B
            alpha: Type I error rate (false positive)
            beta: Type II error rate (false negative)

        Returns:
            dict: Decision and log likelihood ratio
        """
        logger.info("Running sequential probability ratio test")

        p1 = variant_a.conversion_rate
        p2 = variant_b.conversion_rate

        n1 = variant_a.total
        n2 = variant_b.total
        x1 = variant_a.conversions
        x2 = variant_b.conversions

        # Log likelihood ratio
        if p1 > 0 and p2 > 0 and p1 < 1 and p2 < 1:
            llr = (
                x2 * math.log(p2 / p1)
                + (n2 - x2) * math.log((1 - p2) / (1 - p1))
                + x1 * math.log(p1 / p2)
                + (n1 - x1) * math.log((1 - p1) / (1 - p2))
            )
        else:
            llr = 0.0

        # Decision boundaries
        lower_bound = math.log(beta / (1 - alpha))
        upper_bound = math.log((1 - beta) / alpha)

        # Make decision
        if llr >= upper_bound:
            decision = "B_wins"
        elif llr <= lower_bound:
            decision = "A_wins"
        else:
            decision = "continue"

        result = {
            "decision": decision,
            "log_likelihood_ratio": llr,
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
        }

        logger.info(f"SPRT result: decision={decision}, LLR={llr:.4f}")

        return result
