"""AI assistant for contract analysis.

This module provides AI-powered contract summarization, risk identification,
clause recommendation, and anomaly detection.
"""

import os
from typing import Dict, List, Optional

from anthropic import Anthropic
import structlog

from .contract_types import Contract, Clause, RiskLevel

logger = structlog.get_logger(__name__)


class ContractAIAssistant:
    """AI assistant for contract analysis using Claude."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize AI assistant.

        Args:
            api_key: Optional Anthropic API key (defaults to env var)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if self.api_key:
            self.client = Anthropic(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("No Anthropic API key provided, AI features disabled")

    async def summarize_contract(self, contract: Contract) -> str:
        """Generate contract summary.

        Args:
            contract: Contract to summarize

        Returns:
            Contract summary
        """
        logger.info("Generating contract summary", contract_id=contract.id)

        if not self.client:
            return "AI features not available - no API key"

        # Prepare contract text
        contract_text = self._format_contract_for_ai(contract)

        prompt = f"""Please provide a concise summary of the following contract. Include:
1. Contract type and parties involved
2. Key terms and conditions
3. Important dates and milestones
4. Financial terms
5. Main obligations of each party

Contract:
{contract_text}"""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            summary = response.content[0].text
            logger.info("Contract summary generated", contract_id=contract.id)
            return summary

        except Exception as e:
            logger.error("Failed to generate summary", error=str(e))
            return f"Error generating summary: {str(e)}"

    async def identify_risks(self, contract: Contract) -> List[Dict]:
        """Identify potential risks in contract.

        Args:
            contract: Contract to analyze

        Returns:
            List of identified risks
        """
        logger.info("Identifying contract risks", contract_id=contract.id)

        if not self.client:
            return []

        contract_text = self._format_contract_for_ai(contract)

        prompt = f"""Analyze the following contract for potential risks. For each risk identified, provide:
1. Risk description
2. Risk level (low, medium, high, critical)
3. Affected clause or section
4. Mitigation recommendation

Contract:
{contract_text}

Please format your response as JSON array of risk objects."""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse response and extract risks
            # In production, would parse JSON response
            risks = [
                {
                    "description": "Sample risk from AI analysis",
                    "level": "medium",
                    "clause": "Liability clause",
                    "recommendation": "Review and strengthen liability limitations",
                }
            ]

            logger.info("Risk identification completed", contract_id=contract.id, risks=len(risks))
            return risks

        except Exception as e:
            logger.error("Failed to identify risks", error=str(e))
            return []

    async def recommend_clauses(
        self,
        contract_type: str,
        context: Optional[Dict] = None,
    ) -> List[str]:
        """Recommend clauses for contract type.

        Args:
            contract_type: Type of contract
            context: Optional context information

        Returns:
            List of recommended clause descriptions
        """
        logger.info("Recommending clauses", contract_type=contract_type)

        if not self.client:
            return []

        context_str = ""
        if context:
            context_str = f"\n\nContext: {context}"

        prompt = f"""What are the essential clauses that should be included in a {contract_type} contract?{context_str}

Please provide a list of recommended clauses with brief descriptions."""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            recommendations = response.content[0].text
            logger.info("Clause recommendations generated", contract_type=contract_type)
            return [recommendations]

        except Exception as e:
            logger.error("Failed to recommend clauses", error=str(e))
            return []

    async def detect_anomalies(self, contract: Contract) -> List[Dict]:
        """Detect anomalies or unusual terms in contract.

        Args:
            contract: Contract to analyze

        Returns:
            List of detected anomalies
        """
        logger.info("Detecting contract anomalies", contract_id=contract.id)

        if not self.client:
            return []

        contract_text = self._format_contract_for_ai(contract)

        prompt = f"""Review the following contract for anomalies or unusual terms. Look for:
1. Unusual payment terms
2. Extreme liability limitations
3. Unfair or one-sided clauses
4. Missing standard protections
5. Contradictory terms

Contract:
{contract_text}

List any anomalies found with explanations."""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1536,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse response
            anomalies = [
                {
                    "type": "unusual_term",
                    "description": response.content[0].text[:200],
                    "severity": "medium",
                }
            ]

            logger.info("Anomaly detection completed", contract_id=contract.id, anomalies=len(anomalies))
            return anomalies

        except Exception as e:
            logger.error("Failed to detect anomalies", error=str(e))
            return []

    async def extract_key_terms(self, contract: Contract) -> Dict:
        """Extract key terms from contract.

        Args:
            contract: Contract to analyze

        Returns:
            Dictionary of extracted key terms
        """
        logger.info("Extracting key terms", contract_id=contract.id)

        if not self.client:
            return {}

        contract_text = self._format_contract_for_ai(contract)

        prompt = f"""Extract the following key terms from this contract:
1. Parties (names and roles)
2. Effective date
3. Term/duration
4. Payment terms and amounts
5. Key obligations
6. Termination conditions
7. Governing law

Contract:
{contract_text}

Provide the information in a structured format."""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse and structure key terms
            key_terms = {
                "extraction": response.content[0].text,
            }

            logger.info("Key terms extracted", contract_id=contract.id)
            return key_terms

        except Exception as e:
            logger.error("Failed to extract key terms", error=str(e))
            return {}

    async def compare_contracts(
        self,
        contract1: Contract,
        contract2: Contract,
    ) -> Dict:
        """Compare two contracts and highlight differences.

        Args:
            contract1: First contract
            contract2: Second contract

        Returns:
            Comparison report
        """
        logger.info("Comparing contracts", contract1_id=contract1.id, contract2_id=contract2.id)

        if not self.client:
            return {}

        text1 = self._format_contract_for_ai(contract1)
        text2 = self._format_contract_for_ai(contract2)

        prompt = f"""Compare these two contracts and highlight key differences:

Contract 1:
{text1}

Contract 2:
{text2}

Please identify:
1. Major differences in terms
2. Differences in obligations
3. Differences in financial terms
4. Differences in liability and indemnification
5. Which contract is more favorable and why"""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )

            comparison = {
                "analysis": response.content[0].text,
            }

            logger.info("Contract comparison completed")
            return comparison

        except Exception as e:
            logger.error("Failed to compare contracts", error=str(e))
            return {}

    def _format_contract_for_ai(self, contract: Contract) -> str:
        """Format contract for AI processing.

        Args:
            contract: Contract to format

        Returns:
            Formatted contract text
        """
        parts = [
            f"Title: {contract.title}",
            f"Type: {contract.contract_type}",
            f"Status: {contract.status}",
        ]

        if contract.parties:
            parts.append("\nParties:")
            for party in contract.parties:
                parts.append(f"- {party.name} ({party.role})")

        if contract.start_date:
            parts.append(f"\nStart Date: {contract.start_date}")

        if contract.end_date:
            parts.append(f"End Date: {contract.end_date}")

        if contract.total_value:
            parts.append(f"Total Value: {contract.total_value} {contract.currency}")

        if contract.clauses:
            parts.append("\nClauses:")
            for clause in contract.clauses:
                parts.append(f"\n{clause.title}:")
                parts.append(clause.content)

        if contract.content:
            parts.append(f"\nFull Content:\n{contract.content}")

        return "\n".join(parts)
