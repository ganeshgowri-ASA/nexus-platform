"""Clause library and management.

This module provides a standard clause library, custom clause builder,
and clause recommendation system.
"""

from typing import Dict, List, Optional
from uuid import UUID

import structlog

from .contract_types import Clause, ContractType, RiskLevel

logger = structlog.get_logger(__name__)


class ClauseLibrary:
    """Standard clauses library."""

    PAYMENT_CLAUSES = {
        "payment_terms_30": Clause(
            title="Payment Terms - Net 30",
            content="Payment is due within thirty (30) days of invoice date. Late payments will incur interest at 1.5% per month.",
            category="payment",
            is_standard=True,
            risk_level=RiskLevel.LOW,
        ),
        "payment_terms_60": Clause(
            title="Payment Terms - Net 60",
            content="Payment is due within sixty (60) days of invoice date. Late payments will incur interest at 1.5% per month.",
            category="payment",
            is_standard=True,
            risk_level=RiskLevel.MEDIUM,
        ),
        "milestone_payment": Clause(
            title="Milestone-Based Payment",
            content="Payment shall be made upon completion and acceptance of milestones as defined in the project schedule.",
            category="payment",
            is_standard=True,
            risk_level=RiskLevel.MEDIUM,
        ),
    }

    CONFIDENTIALITY_CLAUSES = {
        "mutual_nda": Clause(
            title="Mutual Confidentiality",
            content="Both parties agree to maintain confidentiality of proprietary information disclosed during the term of this agreement.",
            category="confidentiality",
            is_standard=True,
            risk_level=RiskLevel.HIGH,
        ),
        "one_way_nda": Clause(
            title="One-Way Confidentiality",
            content="Receiving Party agrees to maintain confidentiality of Disclosing Party's proprietary information.",
            category="confidentiality",
            is_standard=True,
            risk_level=RiskLevel.MEDIUM,
        ),
    }

    LIABILITY_CLAUSES = {
        "limited_liability": Clause(
            title="Limited Liability",
            content="Neither party's liability shall exceed the total amount paid under this agreement in the 12 months preceding the claim.",
            category="liability",
            is_standard=True,
            risk_level=RiskLevel.HIGH,
        ),
        "no_consequential": Clause(
            title="No Consequential Damages",
            content="Neither party shall be liable for indirect, incidental, consequential, or punitive damages.",
            category="liability",
            is_standard=True,
            risk_level=RiskLevel.HIGH,
        ),
    }

    TERMINATION_CLAUSES = {
        "termination_convenience": Clause(
            title="Termination for Convenience",
            content="Either party may terminate this agreement upon thirty (30) days written notice.",
            category="termination",
            is_standard=True,
            risk_level=RiskLevel.MEDIUM,
        ),
        "termination_cause": Clause(
            title="Termination for Cause",
            content="Either party may terminate immediately upon material breach by the other party, with written notice.",
            category="termination",
            is_standard=True,
            risk_level=RiskLevel.LOW,
        ),
    }

    IP_CLAUSES = {
        "work_for_hire": Clause(
            title="Work for Hire",
            content="All work product shall be considered work for hire and owned by Client upon payment.",
            category="intellectual_property",
            is_standard=True,
            risk_level=RiskLevel.HIGH,
        ),
        "ip_assignment": Clause(
            title="IP Assignment",
            content="Contractor assigns all rights, title, and interest in work product to Client.",
            category="intellectual_property",
            is_standard=True,
            risk_level=RiskLevel.HIGH,
        ),
    }

    @classmethod
    def get_all_clauses(cls) -> Dict[str, Clause]:
        """Get all standard clauses.

        Returns:
            Dictionary of all standard clauses
        """
        all_clauses = {}
        all_clauses.update(cls.PAYMENT_CLAUSES)
        all_clauses.update(cls.CONFIDENTIALITY_CLAUSES)
        all_clauses.update(cls.LIABILITY_CLAUSES)
        all_clauses.update(cls.TERMINATION_CLAUSES)
        all_clauses.update(cls.IP_CLAUSES)
        return all_clauses

    @classmethod
    def get_by_category(cls, category: str) -> List[Clause]:
        """Get clauses by category.

        Args:
            category: Clause category

        Returns:
            List of clauses in category
        """
        all_clauses = cls.get_all_clauses()
        return [c for c in all_clauses.values() if c.category == category]


class ClauseBuilder:
    """Custom clause builder."""

    def __init__(self):
        """Initialize clause builder."""
        self.library = ClauseLibrary()

    def build_clause(
        self,
        title: str,
        content: str,
        category: str,
        is_mandatory: bool = False,
        risk_level: RiskLevel = RiskLevel.LOW,
        variables: Optional[Dict[str, str]] = None,
    ) -> Clause:
        """Build a custom clause.

        Args:
            title: Clause title
            content: Clause content
            category: Clause category
            is_mandatory: Whether clause is mandatory
            risk_level: Risk level
            variables: Template variables

        Returns:
            New Clause instance
        """
        logger.info("Building custom clause", title=title, category=category)

        return Clause(
            title=title,
            content=content,
            category=category,
            is_standard=False,
            is_mandatory=is_mandatory,
            risk_level=risk_level,
            variables=variables or {},
        )

    def substitute_variables(
        self,
        clause: Clause,
        variables: Dict[str, str],
    ) -> Clause:
        """Substitute variables in clause content.

        Args:
            clause: Clause with template variables
            variables: Variable values

        Returns:
            Clause with substituted content
        """
        content = clause.content
        for var_name, var_value in variables.items():
            placeholder = f"{{{{{var_name}}}}}"
            content = content.replace(placeholder, var_value)

        updated_clause = clause.copy()
        updated_clause.content = content
        return updated_clause


class ClauseRecommender:
    """Recommends clauses based on contract type and context."""

    RECOMMENDATIONS = {
        ContractType.NDA: [
            "mutual_nda",
            "termination_convenience",
        ],
        ContractType.MSA: [
            "payment_terms_30",
            "limited_liability",
            "no_consequential",
            "termination_cause",
            "mutual_nda",
        ],
        ContractType.SOW: [
            "milestone_payment",
            "work_for_hire",
            "termination_cause",
        ],
        ContractType.EMPLOYMENT: [
            "one_way_nda",
            "ip_assignment",
        ],
        ContractType.VENDOR: [
            "payment_terms_60",
            "limited_liability",
            "termination_cause",
        ],
    }

    def recommend(
        self,
        contract_type: ContractType,
        existing_clauses: Optional[List[Clause]] = None,
    ) -> List[Clause]:
        """Recommend clauses for contract type.

        Args:
            contract_type: Type of contract
            existing_clauses: Clauses already in contract

        Returns:
            List of recommended clauses
        """
        logger.info("Recommending clauses", contract_type=contract_type)

        clause_keys = self.RECOMMENDATIONS.get(contract_type, [])
        all_clauses = ClauseLibrary.get_all_clauses()

        recommended = []
        existing_categories = set()

        if existing_clauses:
            existing_categories = {c.category for c in existing_clauses}

        for key in clause_keys:
            if key in all_clauses:
                clause = all_clauses[key]
                # Don't recommend if category already covered
                if clause.category not in existing_categories:
                    recommended.append(clause)

        return recommended

    def identify_missing_mandatory(
        self,
        contract_type: ContractType,
        clauses: List[Clause],
    ) -> List[str]:
        """Identify missing mandatory clauses.

        Args:
            contract_type: Type of contract
            clauses: Current clauses

        Returns:
            List of missing mandatory clause categories
        """
        recommended = self.recommend(contract_type, clauses)
        mandatory_categories = {
            c.category for c in recommended if c.is_mandatory
        }

        existing_categories = {c.category for c in clauses}
        missing = mandatory_categories - existing_categories

        return list(missing)
