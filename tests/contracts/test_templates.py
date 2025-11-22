"""Tests for contract templates."""

import pytest
from modules.contracts.templates import TemplateLibrary, TemplateManager
from modules.contracts.contract_types import ContractType


class TestTemplateLibrary:
    """Tests for TemplateLibrary."""

    def test_get_nda_template(self):
        """Test getting NDA template."""
        template = TemplateLibrary.get_nda_template()

        assert template.name == "Non-Disclosure Agreement"
        assert template.contract_type == ContractType.NDA
        assert len(template.clauses) > 0
        assert any("Confidential Information" in c.title for c in template.clauses)

    def test_get_msa_template(self):
        """Test getting MSA template."""
        template = TemplateLibrary.get_msa_template()

        assert template.name == "Master Service Agreement"
        assert template.contract_type == ContractType.MSA
        assert len(template.clauses) > 0

    def test_get_sow_template(self):
        """Test getting SOW template."""
        template = TemplateLibrary.get_sow_template()

        assert template.name == "Statement of Work"
        assert template.contract_type == ContractType.SOW
        assert len(template.clauses) > 0

    def test_get_all_templates(self):
        """Test getting all templates."""
        templates = TemplateLibrary.get_all_templates()

        assert ContractType.NDA in templates
        assert ContractType.MSA in templates
        assert ContractType.SOW in templates
        assert len(templates) > 0


class TestTemplateManager:
    """Tests for TemplateManager."""

    def test_get_template(self):
        """Test getting template by type."""
        manager = TemplateManager()
        template = manager.get_template(ContractType.NDA)

        assert template is not None
        assert template.contract_type == ContractType.NDA

    def test_create_from_template(self):
        """Test creating contract from template."""
        manager = TemplateManager()
        template = manager.get_template(ContractType.NDA)

        variables = {
            "non_compete_period": "3",
            "term_years": "5",
        }

        contract_data = manager.create_from_template(
            template=template,
            variables=variables,
            title="Test NDA",
        )

        assert contract_data["contract_type"] == ContractType.NDA
        assert contract_data["title"] == "Test NDA"
        assert len(contract_data["clauses"]) > 0

        # Check variable substitution
        for clause in contract_data["clauses"]:
            assert "{{" not in clause.content  # No unsubstituted variables

    def test_list_templates(self):
        """Test listing templates."""
        manager = TemplateManager()
        templates = manager.list_templates()

        assert len(templates) > 0

    def test_list_templates_with_filter(self):
        """Test listing templates with filter."""
        manager = TemplateManager()
        nda_templates = manager.list_templates(contract_type=ContractType.NDA)

        assert all(t.contract_type == ContractType.NDA for t in nda_templates)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
