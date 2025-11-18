"""Tests for clause management."""

import pytest
from modules.contracts.clauses import ClauseLibrary, ClauseBuilder, ClauseRecommender
from modules.contracts.contract_types import ContractType, RiskLevel


class TestClauseLibrary:
    """Tests for ClauseLibrary."""

    def test_get_all_clauses(self):
        """Test getting all clauses."""
        clauses = ClauseLibrary.get_all_clauses()

        assert len(clauses) > 0
        assert "payment_terms_30" in clauses
        assert "mutual_nda" in clauses

    def test_get_by_category(self):
        """Test getting clauses by category."""
        payment_clauses = ClauseLibrary.get_by_category("payment")

        assert len(payment_clauses) > 0
        assert all(c.category == "payment" for c in payment_clauses)


class TestClauseBuilder:
    """Tests for ClauseBuilder."""

    def test_build_clause(self):
        """Test building a custom clause."""
        builder = ClauseBuilder()

        clause = builder.build_clause(
            title="Custom Payment Terms",
            content="Payment due within 45 days",
            category="payment",
            is_mandatory=True,
            risk_level=RiskLevel.MEDIUM,
        )

        assert clause.title == "Custom Payment Terms"
        assert clause.category == "payment"
        assert clause.is_standard is False
        assert clause.is_mandatory is True

    def test_substitute_variables(self):
        """Test variable substitution."""
        builder = ClauseBuilder()

        clause = builder.build_clause(
            title="Payment",
            content="Payment due in {{days}} days at {{rate}}% interest",
            category="payment",
            variables={"days": "30", "rate": "1.5"},
        )

        substituted = builder.substitute_variables(
            clause,
            {"days": "45", "rate": "2.0"},
        )

        assert "45" in substituted.content
        assert "2.0" in substituted.content
        assert "{{" not in substituted.content


class TestClauseRecommender:
    """Tests for ClauseRecommender."""

    def test_recommend_for_nda(self):
        """Test recommendations for NDA."""
        recommender = ClauseRecommender()
        recommendations = recommender.recommend(ContractType.NDA)

        assert len(recommendations) > 0

    def test_recommend_for_msa(self):
        """Test recommendations for MSA."""
        recommender = ClauseRecommender()
        recommendations = recommender.recommend(ContractType.MSA)

        assert len(recommendations) > 0

    def test_identify_missing_mandatory(self):
        """Test identifying missing mandatory clauses."""
        recommender = ClauseRecommender()
        # Empty clauses list
        missing = recommender.identify_missing_mandatory(ContractType.MSA, [])

        # Should have some missing categories
        assert isinstance(missing, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
