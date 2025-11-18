"""Contract templates management.

This module provides pre-built contract templates (NDA, MSA, SOW, etc.)
and template management functionality.
"""

from typing import Dict, List, Optional
from uuid import UUID, uuid4

import structlog

from .contract_types import (
    Clause,
    ContractType,
    RiskLevel,
    Template,
)

logger = structlog.get_logger(__name__)


class TemplateLibrary:
    """Library of pre-built contract templates."""

    @staticmethod
    def get_nda_template() -> Template:
        """Get NDA (Non-Disclosure Agreement) template.

        Returns:
            NDA template with standard clauses
        """
        clauses = [
            Clause(
                title="Definition of Confidential Information",
                content="""For purposes of this Agreement, "Confidential Information" means any data or information that is proprietary to the Disclosing Party and not generally known to the public, whether in tangible or intangible form, whenever and however disclosed, including, but not limited to: (i) any marketing strategies, plans, financial information, or projections, operations, sales estimates, business plans and performance results relating to the past, present or future business activities of such party, its affiliates, subsidiaries and affiliates; (ii) plans for products or services, and customer or supplier lists; (iii) any scientific or technical information, invention, design, process, procedure, formula, improvement, technology or method; (iv) any concepts, reports, data, know-how, works-in-progress, designs, development tools, specifications, computer software, source code, object code, flow charts, databases, inventions, information and trade secrets; and (v) any other information that should reasonably be recognized as confidential information of the Disclosing Party.""",
                category="definitions",
                is_standard=True,
                is_mandatory=True,
                risk_level=RiskLevel.LOW,
                position=1,
            ),
            Clause(
                title="Obligations of Receiving Party",
                content="""The Receiving Party agrees to: (a) protect the Confidential Information using the same degree of care that it uses to protect its own confidential information, but in no event less than reasonable care; (b) not use any Confidential Information for any purpose except as necessary to fulfill the Purpose; (c) not disclose, or permit to be disclosed, any Confidential Information to any third party except as permitted under this Agreement; and (d) limit access to Confidential Information to those of its employees, contractors and agents who need such access for purposes consistent with this Agreement and who have signed confidentiality agreements containing protections no less stringent than those herein.""",
                category="obligations",
                is_standard=True,
                is_mandatory=True,
                risk_level=RiskLevel.MEDIUM,
                position=2,
            ),
            Clause(
                title="Non-Compete",
                content="""During the term of this Agreement and for a period of {{non_compete_period}} years thereafter, the Receiving Party agrees not to engage in any business activity that directly competes with the Disclosing Party's business related to the Confidential Information disclosed hereunder.""",
                category="restrictions",
                is_standard=False,
                is_mandatory=False,
                risk_level=RiskLevel.HIGH,
                position=3,
                variables={"non_compete_period": "2"},
            ),
            Clause(
                title="Term and Termination",
                content="""This Agreement shall commence on the Effective Date and continue for a period of {{term_years}} years, unless earlier terminated by either party upon {{notice_days}} days written notice to the other party. The obligations under this Agreement shall survive termination for a period of {{survival_years}} years.""",
                category="term",
                is_standard=True,
                is_mandatory=True,
                risk_level=RiskLevel.LOW,
                position=4,
                variables={"term_years": "3", "notice_days": "30", "survival_years": "5"},
            ),
            Clause(
                title="Return of Materials",
                content="""Upon termination or expiration of this Agreement, or upon request by the Disclosing Party, the Receiving Party shall promptly return to the Disclosing Party all documents and other tangible materials representing the Confidential Information and all copies thereof.""",
                category="termination",
                is_standard=True,
                is_mandatory=True,
                risk_level=RiskLevel.MEDIUM,
                position=5,
            ),
        ]

        return Template(
            name="Non-Disclosure Agreement",
            description="Standard NDA for protecting confidential information",
            contract_type=ContractType.NDA,
            clauses=clauses,
            variables={
                "non_compete_period": "2",
                "term_years": "3",
                "notice_days": "30",
                "survival_years": "5",
            },
            category="Legal",
            jurisdiction="United States",
        )

    @staticmethod
    def get_msa_template() -> Template:
        """Get MSA (Master Service Agreement) template.

        Returns:
            MSA template with standard clauses
        """
        clauses = [
            Clause(
                title="Services",
                content="""The Vendor agrees to provide the services as described in each Statement of Work ("SOW") executed under this Master Service Agreement. Each SOW shall specify the scope of services, deliverables, timeline, and compensation.""",
                category="services",
                is_standard=True,
                is_mandatory=True,
                risk_level=RiskLevel.LOW,
                position=1,
            ),
            Clause(
                title="Payment Terms",
                content="""Client shall pay Vendor the fees specified in each SOW. Unless otherwise stated in the SOW, payment shall be due within {{payment_days}} days of invoice date. Late payments shall accrue interest at {{interest_rate}}% per month.""",
                category="payment",
                is_standard=True,
                is_mandatory=True,
                risk_level=RiskLevel.MEDIUM,
                position=2,
                variables={"payment_days": "30", "interest_rate": "1.5"},
            ),
            Clause(
                title="Intellectual Property",
                content="""All work product, deliverables, and intellectual property created by Vendor in the course of providing Services shall be the exclusive property of Client upon full payment. Vendor hereby assigns all rights, title, and interest in such work product to Client.""",
                category="intellectual_property",
                is_standard=True,
                is_mandatory=True,
                risk_level=RiskLevel.HIGH,
                position=3,
            ),
            Clause(
                title="Warranties",
                content="""Vendor warrants that: (a) it has the necessary expertise and resources to perform the Services; (b) Services will be performed in a professional and workmanlike manner; (c) Services will conform to the specifications in the applicable SOW; and (d) it has the right to enter into this Agreement.""",
                category="warranties",
                is_standard=True,
                is_mandatory=True,
                risk_level=RiskLevel.MEDIUM,
                position=4,
            ),
            Clause(
                title="Limitation of Liability",
                content="""Except for breaches of confidentiality or intellectual property rights, neither party's aggregate liability arising out of this Agreement shall exceed the total fees paid or payable under the applicable SOW in the twelve (12) months preceding the claim. Neither party shall be liable for indirect, incidental, consequential, or punitive damages.""",
                category="liability",
                is_standard=True,
                is_mandatory=True,
                risk_level=RiskLevel.HIGH,
                position=5,
            ),
        ]

        return Template(
            name="Master Service Agreement",
            description="Standard MSA for ongoing service relationships",
            contract_type=ContractType.MSA,
            clauses=clauses,
            variables={"payment_days": "30", "interest_rate": "1.5"},
            category="Services",
            jurisdiction="United States",
        )

    @staticmethod
    def get_sow_template() -> Template:
        """Get SOW (Statement of Work) template.

        Returns:
            SOW template with standard clauses
        """
        clauses = [
            Clause(
                title="Scope of Work",
                content="""This Statement of Work ("SOW") describes the specific services, deliverables, timeline, and fees for the engagement described herein. This SOW is governed by the Master Service Agreement dated {{msa_date}} between the parties.\n\nScope: {{scope_description}}""",
                category="scope",
                is_standard=True,
                is_mandatory=True,
                risk_level=RiskLevel.LOW,
                position=1,
                variables={"msa_date": "", "scope_description": ""},
            ),
            Clause(
                title="Deliverables",
                content="""Vendor shall deliver the following:\n{{deliverables_list}}\n\nAll deliverables shall meet the acceptance criteria specified in this SOW.""",
                category="deliverables",
                is_standard=True,
                is_mandatory=True,
                risk_level=RiskLevel.MEDIUM,
                position=2,
                variables={"deliverables_list": ""},
            ),
            Clause(
                title="Timeline and Milestones",
                content="""The project shall commence on {{start_date}} and be completed by {{end_date}}. Key milestones:\n{{milestones_list}}""",
                category="timeline",
                is_standard=True,
                is_mandatory=True,
                risk_level=RiskLevel.MEDIUM,
                position=3,
                variables={"start_date": "", "end_date": "", "milestones_list": ""},
            ),
            Clause(
                title="Fees and Payment Schedule",
                content="""Total project fee: {{total_fee}} {{currency}}\n\nPayment schedule:\n{{payment_schedule}}""",
                category="payment",
                is_standard=True,
                is_mandatory=True,
                risk_level=RiskLevel.HIGH,
                position=4,
                variables={"total_fee": "", "currency": "USD", "payment_schedule": ""},
            ),
        ]

        return Template(
            name="Statement of Work",
            description="Project-specific SOW template",
            contract_type=ContractType.SOW,
            clauses=clauses,
            variables={
                "msa_date": "",
                "scope_description": "",
                "deliverables_list": "",
                "start_date": "",
                "end_date": "",
                "milestones_list": "",
                "total_fee": "",
                "currency": "USD",
                "payment_schedule": "",
            },
            category="Services",
            jurisdiction="United States",
        )

    @staticmethod
    def get_employment_template() -> Template:
        """Get Employment Agreement template."""
        clauses = [
            Clause(
                title="Position and Duties",
                content="""Employee is hired for the position of {{job_title}} and shall perform duties as assigned by {{manager_title}}. Employee shall devote full business time and attention to the performance of duties.""",
                category="employment",
                is_standard=True,
                is_mandatory=True,
                risk_level=RiskLevel.LOW,
                position=1,
                variables={"job_title": "", "manager_title": ""},
            ),
            Clause(
                title="Compensation",
                content="""Employee shall receive an annual salary of {{salary}} {{currency}}, payable in accordance with Company's standard payroll practices. Employee shall be eligible for performance bonuses and benefits as described in the Employee Handbook.""",
                category="compensation",
                is_standard=True,
                is_mandatory=True,
                risk_level=RiskLevel.MEDIUM,
                position=2,
                variables={"salary": "", "currency": "USD"},
            ),
        ]

        return Template(
            name="Employment Agreement",
            description="Standard employment contract",
            contract_type=ContractType.EMPLOYMENT,
            clauses=clauses,
            category="HR",
        )

    @staticmethod
    def get_vendor_template() -> Template:
        """Get Vendor Agreement template."""
        return Template(
            name="Vendor Agreement",
            description="Agreement with vendors and suppliers",
            contract_type=ContractType.VENDOR,
            category="Procurement",
        )

    @staticmethod
    def get_sales_template() -> Template:
        """Get Sales Agreement template."""
        return Template(
            name="Sales Agreement",
            description="Standard sales contract",
            contract_type=ContractType.SALES,
            category="Sales",
        )

    @staticmethod
    def get_all_templates() -> Dict[ContractType, Template]:
        """Get all available templates.

        Returns:
            Dictionary mapping contract type to template
        """
        return {
            ContractType.NDA: TemplateLibrary.get_nda_template(),
            ContractType.MSA: TemplateLibrary.get_msa_template(),
            ContractType.SOW: TemplateLibrary.get_sow_template(),
            ContractType.EMPLOYMENT: TemplateLibrary.get_employment_template(),
            ContractType.VENDOR: TemplateLibrary.get_vendor_template(),
            ContractType.SALES: TemplateLibrary.get_sales_template(),
        }


class TemplateManager:
    """Manages contract templates."""

    def __init__(self):
        """Initialize template manager."""
        self.library = TemplateLibrary()

    def get_template(self, contract_type: ContractType) -> Optional[Template]:
        """Get template by contract type.

        Args:
            contract_type: Type of contract

        Returns:
            Template instance or None
        """
        templates = self.library.get_all_templates()
        return templates.get(contract_type)

    def create_from_template(
        self,
        template: Template,
        variables: Dict[str, str],
        **kwargs
    ) -> Dict:
        """Create contract from template with variable substitution.

        Args:
            template: Template to use
            variables: Variable values for substitution
            **kwargs: Additional contract fields

        Returns:
            Contract data dictionary
        """
        logger.info("Creating contract from template", template=template.name)

        # Substitute variables in clauses
        processed_clauses = []
        for clause in template.clauses:
            content = clause.content
            # Replace template variables
            for var_name, var_value in variables.items():
                placeholder = f"{{{{{var_name}}}}}"
                if placeholder in content:
                    content = content.replace(placeholder, var_value)

            processed_clause = clause.copy()
            processed_clause.content = content
            processed_clauses.append(processed_clause)

        contract_data = {
            "contract_type": template.contract_type,
            "template_id": template.id,
            "clauses": processed_clauses,
            "category": template.category,
            "jurisdiction": template.jurisdiction,
            "language": template.language,
            **kwargs
        }

        return contract_data

    def list_templates(
        self,
        contract_type: Optional[ContractType] = None,
        category: Optional[str] = None,
    ) -> List[Template]:
        """List available templates.

        Args:
            contract_type: Filter by contract type
            category: Filter by category

        Returns:
            List of templates
        """
        templates = list(self.library.get_all_templates().values())

        if contract_type:
            templates = [t for t in templates if t.contract_type == contract_type]

        if category:
            templates = [t for t in templates if t.category == category]

        return templates
