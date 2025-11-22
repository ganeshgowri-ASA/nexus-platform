"""Compliance and risk assessment.

This module handles regulatory compliance checks, legal requirement validation,
and risk assessment for contracts.
"""

from typing import Dict, List, Optional
from uuid import UUID

import structlog

from .contract_types import Contract, Clause, RiskLevel

logger = structlog.get_logger(__name__)


class ComplianceRule:
    """Represents a compliance rule."""

    def __init__(
        self,
        name: str,
        description: str,
        jurisdiction: str,
        regulation: str,
        severity: str = "warning",
    ):
        """Initialize compliance rule.

        Args:
            name: Rule name
            description: Rule description
            jurisdiction: Applicable jurisdiction
            regulation: Regulation reference
            severity: Severity level (warning, error, critical)
        """
        self.name = name
        self.description = description
        self.jurisdiction = jurisdiction
        self.regulation = regulation
        self.severity = severity

    def check(self, contract: Contract) -> Optional[Dict]:
        """Check if contract complies with rule.

        Args:
            contract: Contract to check

        Returns:
            Compliance issue dict or None if compliant
        """
        raise NotImplementedError


class GDPRComplianceRule(ComplianceRule):
    """GDPR compliance rule."""

    def __init__(self):
        """Initialize GDPR rule."""
        super().__init__(
            name="GDPR Data Protection",
            description="Contract must include GDPR-compliant data protection clauses",
            jurisdiction="EU",
            regulation="GDPR",
            severity="error",
        )

    def check(self, contract: Contract) -> Optional[Dict]:
        """Check GDPR compliance."""
        # Check for data protection clauses
        data_protection_clauses = [
            c for c in contract.clauses
            if "data protection" in c.title.lower() or "privacy" in c.title.lower()
        ]

        if not data_protection_clauses:
            return {
                "rule": self.name,
                "issue": "Missing data protection clauses",
                "severity": self.severity,
                "recommendation": "Add GDPR-compliant data protection and privacy clauses",
            }

        return None


class MandatoryClauseRule(ComplianceRule):
    """Rule for mandatory clause presence."""

    def __init__(self, required_categories: List[str]):
        """Initialize mandatory clause rule.

        Args:
            required_categories: List of required clause categories
        """
        super().__init__(
            name="Mandatory Clauses",
            description="Contract must contain all mandatory clause categories",
            jurisdiction="General",
            regulation="Internal Policy",
            severity="error",
        )
        self.required_categories = required_categories

    def check(self, contract: Contract) -> Optional[Dict]:
        """Check mandatory clauses."""
        existing_categories = {c.category for c in contract.clauses}
        missing = set(self.required_categories) - existing_categories

        if missing:
            return {
                "rule": self.name,
                "issue": f"Missing mandatory clauses: {', '.join(missing)}",
                "severity": self.severity,
                "recommendation": f"Add clauses for: {', '.join(missing)}",
            }

        return None


class ComplianceEngine:
    """Compliance checking engine."""

    def __init__(self):
        """Initialize compliance engine."""
        self.rules: List[ComplianceRule] = []
        self._register_default_rules()

    def _register_default_rules(self):
        """Register default compliance rules."""
        # GDPR rule
        self.rules.append(GDPRComplianceRule())

        # Mandatory clauses for different contract types
        self.rules.append(
            MandatoryClauseRule(["payment", "termination", "liability"])
        )

    def register_rule(self, rule: ComplianceRule):
        """Register a custom compliance rule.

        Args:
            rule: Compliance rule to register
        """
        logger.info("Registering compliance rule", rule=rule.name)
        self.rules.append(rule)

    def check_compliance(
        self,
        contract: Contract,
        jurisdiction: Optional[str] = None,
    ) -> List[Dict]:
        """Check contract compliance.

        Args:
            contract: Contract to check
            jurisdiction: Optional jurisdiction filter

        Returns:
            List of compliance issues
        """
        logger.info("Checking contract compliance", contract_id=contract.id)

        issues = []
        applicable_rules = self.rules

        if jurisdiction:
            applicable_rules = [
                r for r in self.rules
                if r.jurisdiction == jurisdiction or r.jurisdiction == "General"
            ]

        for rule in applicable_rules:
            issue = rule.check(contract)
            if issue:
                issues.append(issue)

        logger.info("Compliance check completed", contract_id=contract.id, issues=len(issues))
        return issues

    def assess_risk(self, contract: Contract) -> Dict:
        """Assess contract risk.

        Args:
            contract: Contract to assess

        Returns:
            Risk assessment report
        """
        logger.info("Assessing contract risk", contract_id=contract.id)

        risk_factors = []
        risk_score = 0

        # Check high-risk clauses
        high_risk_clauses = [c for c in contract.clauses if c.risk_level == RiskLevel.HIGH]
        if high_risk_clauses:
            risk_score += len(high_risk_clauses) * 20
            risk_factors.append(f"{len(high_risk_clauses)} high-risk clauses")

        # Check contract value
        if contract.total_value and contract.total_value > 1000000:
            risk_score += 30
            risk_factors.append("High contract value")

        # Check jurisdiction
        high_risk_jurisdictions = ["XX", "YY"]  # Example
        if contract.jurisdiction in high_risk_jurisdictions:
            risk_score += 25
            risk_factors.append("High-risk jurisdiction")

        # Check compliance issues
        compliance_issues = self.check_compliance(contract)
        if compliance_issues:
            risk_score += len(compliance_issues) * 10
            risk_factors.append(f"{len(compliance_issues)} compliance issues")

        # Determine risk level
        if risk_score >= 75:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 50:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 25:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "compliance_issues": compliance_issues,
            "recommendations": self._get_recommendations(risk_level, risk_factors),
        }

    def _get_recommendations(
        self,
        risk_level: RiskLevel,
        risk_factors: List[str],
    ) -> List[str]:
        """Get risk mitigation recommendations.

        Args:
            risk_level: Assessed risk level
            risk_factors: List of risk factors

        Returns:
            List of recommendations
        """
        recommendations = []

        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.append("Require legal review before approval")
            recommendations.append("Obtain additional management approval")

        if "high-risk clauses" in str(risk_factors):
            recommendations.append("Review and modify high-risk clauses")

        if "compliance issues" in str(risk_factors):
            recommendations.append("Address all compliance issues before execution")

        return recommendations
