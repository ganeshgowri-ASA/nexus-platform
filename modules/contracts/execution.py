"""Contract execution and e-signature management.

This module handles e-signature integration, witness management,
notarization, and execution tracking.
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

import structlog

from .contract_types import Signature, SignatureStatus, PartyRole

logger = structlog.get_logger(__name__)


class ESignatureProvider:
    """Base class for e-signature providers."""

    async def request_signature(
        self,
        signer_email: str,
        document_url: str,
        callback_url: str,
    ) -> str:
        """Request signature from signer.

        Args:
            signer_email: Signer's email
            document_url: URL to document
            callback_url: Callback URL for completion

        Returns:
            Signature request ID
        """
        raise NotImplementedError

    async def get_signature_status(self, request_id: str) -> str:
        """Get signature status.

        Args:
            request_id: Signature request ID

        Returns:
            Status string
        """
        raise NotImplementedError

    async def download_signed_document(self, request_id: str) -> bytes:
        """Download signed document.

        Args:
            request_id: Signature request ID

        Returns:
            Signed document bytes
        """
        raise NotImplementedError


class DocuSignProvider(ESignatureProvider):
    """DocuSign integration."""

    def __init__(self, api_key: str, account_id: str):
        """Initialize DocuSign provider.

        Args:
            api_key: DocuSign API key
            account_id: DocuSign account ID
        """
        self.api_key = api_key
        self.account_id = account_id

    async def request_signature(
        self,
        signer_email: str,
        document_url: str,
        callback_url: str,
    ) -> str:
        """Request signature via DocuSign."""
        logger.info("Requesting DocuSign signature", signer_email=signer_email)
        # Implementation would use DocuSign API
        return f"docusign_request_{signer_email}"

    async def get_signature_status(self, request_id: str) -> str:
        """Get DocuSign signature status."""
        # Implementation would check DocuSign API
        return "pending"

    async def download_signed_document(self, request_id: str) -> bytes:
        """Download signed document from DocuSign."""
        # Implementation would download from DocuSign
        return b""


class AdobeSignProvider(ESignatureProvider):
    """Adobe Sign integration."""

    def __init__(self, api_key: str):
        """Initialize Adobe Sign provider.

        Args:
            api_key: Adobe Sign API key
        """
        self.api_key = api_key

    async def request_signature(
        self,
        signer_email: str,
        document_url: str,
        callback_url: str,
    ) -> str:
        """Request signature via Adobe Sign."""
        logger.info("Requesting Adobe Sign signature", signer_email=signer_email)
        return f"adobe_request_{signer_email}"

    async def get_signature_status(self, request_id: str) -> str:
        """Get Adobe Sign signature status."""
        return "pending"

    async def download_signed_document(self, request_id: str) -> bytes:
        """Download signed document from Adobe Sign."""
        return b""


class ExecutionManager:
    """Manages contract execution and signatures."""

    def __init__(self, signature_provider: Optional[ESignatureProvider] = None):
        """Initialize execution manager.

        Args:
            signature_provider: E-signature provider instance
        """
        self.signature_provider = signature_provider
        self.signatures: Dict[UUID, List[Signature]] = {}

    async def request_signatures(
        self,
        contract_id: UUID,
        signers: List[Dict],
        document_url: str,
    ) -> List[Signature]:
        """Request signatures from all parties.

        Args:
            contract_id: Contract ID
            signers: List of signer dictionaries
            document_url: URL to contract document

        Returns:
            List of signature requests
        """
        logger.info("Requesting signatures", contract_id=contract_id, signers=len(signers))

        signatures = []
        for signer in signers:
            signature = Signature(
                contract_id=contract_id,
                signer_id=signer["id"],
                signer_name=signer["name"],
                signer_email=signer["email"],
                signer_role=signer["role"],
                status=SignatureStatus.REQUESTED,
            )

            # Request signature via provider
            if self.signature_provider:
                try:
                    request_id = await self.signature_provider.request_signature(
                        signer_email=signer["email"],
                        document_url=document_url,
                        callback_url=f"/api/contracts/{contract_id}/signature-callback",
                    )
                    signature.metadata["provider_request_id"] = request_id
                except Exception as e:
                    logger.error("Failed to request signature", error=str(e))

            signatures.append(signature)

        if contract_id not in self.signatures:
            self.signatures[contract_id] = []
        self.signatures[contract_id].extend(signatures)

        return signatures

    def record_signature(
        self,
        signature_id: UUID,
        signature_data: str,
        ip_address: Optional[str] = None,
        location: Optional[str] = None,
        device_info: Optional[str] = None,
    ) -> Signature:
        """Record a completed signature.

        Args:
            signature_id: Signature ID
            signature_data: Base64 encoded signature
            ip_address: Signer's IP address
            location: Signer's location
            device_info: Device information

        Returns:
            Updated signature
        """
        logger.info("Recording signature", signature_id=signature_id)

        signature = self._get_signature(signature_id)
        signature.status = SignatureStatus.SIGNED
        signature.signed_at = datetime.utcnow()
        signature.signature_data = signature_data
        signature.ip_address = ip_address
        signature.location = location
        signature.device_info = device_info

        return signature

    def add_witness(
        self,
        signature_id: UUID,
        witness_name: str,
        witness_email: str,
    ) -> Signature:
        """Add witness to a signature.

        Args:
            signature_id: Signature ID
            witness_name: Witness name
            witness_email: Witness email

        Returns:
            Updated signature
        """
        logger.info("Adding witness", signature_id=signature_id, witness=witness_name)

        signature = self._get_signature(signature_id)
        signature.witness_name = witness_name
        signature.witness_email = witness_email

        return signature

    def notarize(
        self,
        signature_id: UUID,
        notary_info: Dict,
    ) -> Signature:
        """Add notarization to a signature.

        Args:
            signature_id: Signature ID
            notary_info: Notary information

        Returns:
            Updated signature
        """
        logger.info("Notarizing signature", signature_id=signature_id)

        signature = self._get_signature(signature_id)
        signature.notarized = True
        signature.notary_info = notary_info

        return signature

    def get_signatures(
        self,
        contract_id: UUID,
        status: Optional[SignatureStatus] = None,
    ) -> List[Signature]:
        """Get signatures for a contract.

        Args:
            contract_id: Contract ID
            status: Optional status filter

        Returns:
            List of signatures
        """
        signatures = self.signatures.get(contract_id, [])

        if status:
            signatures = [s for s in signatures if s.status == status]

        return signatures

    def is_fully_executed(self, contract_id: UUID) -> bool:
        """Check if contract is fully executed (all signatures obtained).

        Args:
            contract_id: Contract ID

        Returns:
            True if fully executed
        """
        signatures = self.signatures.get(contract_id, [])
        if not signatures:
            return False

        return all(s.status == SignatureStatus.SIGNED for s in signatures)

    def get_pending_signatures(self, contract_id: UUID) -> List[Signature]:
        """Get pending signatures for a contract.

        Args:
            contract_id: Contract ID

        Returns:
            List of pending signatures
        """
        return self.get_signatures(
            contract_id,
            status=SignatureStatus.REQUESTED,
        )

    async def check_signature_status(self, contract_id: UUID) -> Dict[UUID, str]:
        """Check status of all signatures via provider.

        Args:
            contract_id: Contract ID

        Returns:
            Dictionary mapping signature ID to status
        """
        statuses = {}

        if not self.signature_provider:
            return statuses

        signatures = self.signatures.get(contract_id, [])
        for signature in signatures:
            if signature.status != SignatureStatus.REQUESTED:
                continue

            request_id = signature.metadata.get("provider_request_id")
            if request_id:
                try:
                    status = await self.signature_provider.get_signature_status(request_id)
                    statuses[signature.id] = status
                except Exception as e:
                    logger.error("Failed to check signature status", error=str(e))

        return statuses

    def _get_signature(self, signature_id: UUID) -> Signature:
        """Get signature by ID."""
        for signatures in self.signatures.values():
            for signature in signatures:
                if signature.id == signature_id:
                    return signature
        raise ValueError(f"Signature {signature_id} not found")
