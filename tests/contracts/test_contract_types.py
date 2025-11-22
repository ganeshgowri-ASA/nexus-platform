"""Tests for contract types and models."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from modules.contracts.contract_types import (
    Contract,
    ContractStatus,
    ContractType,
    Party,
    PartyRole,
    Clause,
    Obligation,
    ObligationStatus,
    ObligationType,
    Milestone,
    MilestoneStatus,
    Signature,
    SignatureStatus,
    RiskLevel,
    Currency,
)


class TestParty:
    """Tests for Party model."""

    def test_create_party(self):
        """Test creating a party."""
        party = Party(
            name="John Doe",
            role=PartyRole.BUYER,
            organization="Acme Corp",
            email="john@acme.com",
        )

        assert party.name == "John Doe"
        assert party.role == PartyRole.BUYER
        assert party.organization == "Acme Corp"
        assert party.email == "john@acme.com"

    def test_party_created_at(self):
        """Test party has created_at timestamp."""
        party = Party(name="Test", role=PartyRole.SELLER)
        assert isinstance(party.created_at, datetime)


class TestClause:
    """Tests for Clause model."""

    def test_create_clause(self):
        """Test creating a clause."""
        clause = Clause(
            title="Payment Terms",
            content="Payment due within 30 days",
            category="payment",
            is_standard=True,
            risk_level=RiskLevel.LOW,
        )

        assert clause.title == "Payment Terms"
        assert clause.content == "Payment due within 30 days"
        assert clause.category == "payment"
        assert clause.is_standard is True
        assert clause.risk_level == RiskLevel.LOW

    def test_clause_with_variables(self):
        """Test clause with template variables."""
        clause = Clause(
            title="Payment",
            content="Payment due in {{days}} days",
            category="payment",
            variables={"days": "30"},
        )

        assert clause.variables["days"] == "30"


class TestContract:
    """Tests for Contract model."""

    def test_create_contract(self):
        """Test creating a contract."""
        party1 = Party(name="Buyer", role=PartyRole.BUYER)
        party2 = Party(name="Seller", role=PartyRole.SELLER)

        contract = Contract(
            title="Test Contract",
            contract_type=ContractType.SALES,
            parties=[party1, party2],
        )

        assert contract.title == "Test Contract"
        assert contract.contract_type == ContractType.SALES
        assert len(contract.parties) == 2
        assert contract.status == ContractStatus.DRAFT

    def test_contract_requires_two_parties(self):
        """Test contract requires at least 2 parties."""
        party = Party(name="Single Party", role=PartyRole.BUYER)

        with pytest.raises(ValueError, match="at least 2 parties"):
            Contract(
                title="Invalid Contract",
                contract_type=ContractType.SALES,
                parties=[party],
            )

    def test_contract_date_validation(self):
        """Test contract date validation."""
        party1 = Party(name="A", role=PartyRole.BUYER)
        party2 = Party(name="B", role=PartyRole.SELLER)

        start = datetime.now()
        end = start - timedelta(days=1)  # End before start

        with pytest.raises(ValueError, match="after start date"):
            Contract(
                title="Test",
                contract_type=ContractType.SALES,
                parties=[party1, party2],
                start_date=start,
                end_date=end,
            )

    def test_is_expiring(self):
        """Test is_expiring method."""
        party1 = Party(name="A", role=PartyRole.BUYER)
        party2 = Party(name="B", role=PartyRole.SELLER)

        # Contract expiring in 20 days
        end_date = datetime.utcnow() + timedelta(days=20)

        contract = Contract(
            title="Test",
            contract_type=ContractType.SALES,
            parties=[party1, party2],
            end_date=end_date,
        )

        assert contract.is_expiring(days=30) is True
        assert contract.is_expiring(days=10) is False

    def test_is_expired(self):
        """Test is_expired method."""
        party1 = Party(name="A", role=PartyRole.BUYER)
        party2 = Party(name="B", role=PartyRole.SELLER)

        # Contract expired yesterday
        end_date = datetime.utcnow() - timedelta(days=1)

        contract = Contract(
            title="Test",
            contract_type=ContractType.SALES,
            parties=[party1, party2],
            end_date=end_date,
        )

        assert contract.is_expired() is True

    def test_days_until_expiry(self):
        """Test days_until_expiry method."""
        party1 = Party(name="A", role=PartyRole.BUYER)
        party2 = Party(name="B", role=PartyRole.SELLER)

        end_date = datetime.utcnow() + timedelta(days=15)

        contract = Contract(
            title="Test",
            contract_type=ContractType.SALES,
            parties=[party1, party2],
            end_date=end_date,
        )

        days = contract.days_until_expiry()
        assert 14 <= days <= 15

    def test_get_party_by_role(self):
        """Test get_party_by_role method."""
        buyer = Party(name="Buyer", role=PartyRole.BUYER)
        seller = Party(name="Seller", role=PartyRole.SELLER)

        contract = Contract(
            title="Test",
            contract_type=ContractType.SALES,
            parties=[buyer, seller],
        )

        found_buyer = contract.get_party_by_role(PartyRole.BUYER)
        assert found_buyer.name == "Buyer"

        found_seller = contract.get_party_by_role(PartyRole.SELLER)
        assert found_seller.name == "Seller"

    def test_is_fully_signed(self):
        """Test is_fully_signed method."""
        party1 = Party(name="A", role=PartyRole.BUYER)
        party2 = Party(name="B", role=PartyRole.SELLER)

        contract = Contract(
            title="Test",
            contract_type=ContractType.SALES,
            parties=[party1, party2],
        )

        # No signatures
        assert contract.is_fully_signed() is False

        # Add signed signatures
        sig1 = Signature(
            contract_id=contract.id,
            signer_id=uuid4(),
            signer_name="A",
            signer_email="a@test.com",
            signer_role=PartyRole.BUYER,
            status=SignatureStatus.SIGNED,
        )

        sig2 = Signature(
            contract_id=contract.id,
            signer_id=uuid4(),
            signer_name="B",
            signer_email="b@test.com",
            signer_role=PartyRole.SELLER,
            status=SignatureStatus.SIGNED,
        )

        contract.signatures = [sig1, sig2]
        assert contract.is_fully_signed() is True

    def test_get_pending_signatures(self):
        """Test get_pending_signatures method."""
        party1 = Party(name="A", role=PartyRole.BUYER)
        party2 = Party(name="B", role=PartyRole.SELLER)

        contract = Contract(
            title="Test",
            contract_type=ContractType.SALES,
            parties=[party1, party2],
        )

        sig1 = Signature(
            contract_id=contract.id,
            signer_id=uuid4(),
            signer_name="A",
            signer_email="a@test.com",
            signer_role=PartyRole.BUYER,
            status=SignatureStatus.PENDING,
        )

        sig2 = Signature(
            contract_id=contract.id,
            signer_id=uuid4(),
            signer_name="B",
            signer_email="b@test.com",
            signer_role=PartyRole.SELLER,
            status=SignatureStatus.SIGNED,
        )

        contract.signatures = [sig1, sig2]
        pending = contract.get_pending_signatures()

        assert len(pending) == 1
        assert pending[0].signer_name == "A"

    def test_get_overdue_obligations(self):
        """Test get_overdue_obligations method."""
        party1 = Party(name="A", role=PartyRole.BUYER)
        party2 = Party(name="B", role=PartyRole.SELLER)

        contract = Contract(
            title="Test",
            contract_type=ContractType.SALES,
            parties=[party1, party2],
        )

        # Overdue obligation
        overdue_obl = Obligation(
            contract_id=contract.id,
            title="Overdue Payment",
            description="Payment overdue",
            obligation_type=ObligationType.PAYMENT,
            responsible_party=uuid4(),
            due_date=datetime.utcnow() - timedelta(days=1),
            status=ObligationStatus.PENDING,
        )

        # Future obligation
        future_obl = Obligation(
            contract_id=contract.id,
            title="Future Payment",
            description="Future payment",
            obligation_type=ObligationType.PAYMENT,
            responsible_party=uuid4(),
            due_date=datetime.utcnow() + timedelta(days=30),
            status=ObligationStatus.PENDING,
        )

        contract.obligations = [overdue_obl, future_obl]
        overdue = contract.get_overdue_obligations()

        assert len(overdue) == 1
        assert overdue[0].title == "Overdue Payment"


class TestObligation:
    """Tests for Obligation model."""

    def test_create_obligation(self):
        """Test creating an obligation."""
        obligation = Obligation(
            contract_id=uuid4(),
            title="Payment Due",
            description="Monthly payment",
            obligation_type=ObligationType.PAYMENT,
            responsible_party=uuid4(),
            due_date=datetime.now() + timedelta(days=30),
        )

        assert obligation.title == "Payment Due"
        assert obligation.obligation_type == ObligationType.PAYMENT
        assert obligation.status == ObligationStatus.PENDING

    def test_obligation_amount_validation(self):
        """Test obligation amount validation."""
        with pytest.raises(ValueError, match="non-negative"):
            Obligation(
                contract_id=uuid4(),
                title="Test",
                description="Test",
                obligation_type=ObligationType.PAYMENT,
                responsible_party=uuid4(),
                amount=-100,
            )


class TestMilestone:
    """Tests for Milestone model."""

    def test_create_milestone(self):
        """Test creating a milestone."""
        milestone = Milestone(
            contract_id=uuid4(),
            title="Phase 1 Complete",
            description="Complete phase 1",
            due_date=datetime.now() + timedelta(days=60),
            payment_trigger=True,
        )

        assert milestone.title == "Phase 1 Complete"
        assert milestone.status == MilestoneStatus.PENDING
        assert milestone.payment_trigger is True


class TestSignature:
    """Tests for Signature model."""

    def test_create_signature(self):
        """Test creating a signature."""
        signature = Signature(
            contract_id=uuid4(),
            signer_id=uuid4(),
            signer_name="John Doe",
            signer_email="john@example.com",
            signer_role=PartyRole.BUYER,
        )

        assert signature.signer_name == "John Doe"
        assert signature.status == SignatureStatus.PENDING
        assert signature.notarized is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
