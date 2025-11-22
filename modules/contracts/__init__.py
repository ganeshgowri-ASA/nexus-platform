"""Contracts Management Module for NEXUS Platform.

This module provides comprehensive contract lifecycle management including:
- Contract creation, negotiation, and execution
- Template and clause management
- Approval workflows and e-signatures
- Obligation and milestone tracking
- Compliance and risk assessment
- AI-powered contract analysis
- Integration with CRM, accounting, and project management
- Analytics and reporting
"""

__version__ = "1.0.0"
__author__ = "NEXUS Platform Team"

from .contract_types import (
    Contract,
    ContractStatus,
    ContractType,
    Party,
    Clause,
    Template,
    Obligation,
    Milestone,
    Amendment,
    Signature,
)

__all__ = [
    "Contract",
    "ContractStatus",
    "ContractType",
    "Party",
    "Clause",
    "Template",
    "Obligation",
    "Milestone",
    "Amendment",
    "Signature",
]
