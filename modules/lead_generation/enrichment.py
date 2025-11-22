"""Lead enrichment using third-party APIs."""

from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
import httpx

from .models import Lead as LeadModel, LeadEnrichment
from shared.utils import generate_uuid
from shared.exceptions import ExternalAPIError
from config.settings import settings
from config.logging_config import get_logger

logger = get_logger(__name__)


class LeadEnricher:
    """Lead enrichment service using third-party APIs."""

    def __init__(self, db: Session):
        self.db = db

    async def enrich_lead(self, lead_id: str) -> Dict[str, Any]:
        """Enrich lead with additional data from external sources."""
        try:
            lead = self.db.query(LeadModel).filter(LeadModel.id == lead_id).first()
            if not lead:
                return {"error": "Lead not found"}

            enriched_data = {}

            # Enrich with Clearbit (if API key available)
            if settings.clearbit_api_key and lead.email:
                clearbit_data = await self._enrich_clearbit(lead.email)
                if clearbit_data:
                    enriched_data["clearbit"] = clearbit_data

            # Enrich with Hunter (if API key available)
            if settings.hunter_api_key and lead.company:
                hunter_data = await self._enrich_hunter(lead.company)
                if hunter_data:
                    enriched_data["hunter"] = hunter_data

            # Apply enriched data to lead
            if enriched_data:
                await self._apply_enrichment(lead, enriched_data)
                
                # Save enrichment record
                enrichment = LeadEnrichment(
                    id=generate_uuid(),
                    lead_id=lead_id,
                    provider="multiple",
                    data=enriched_data,
                    status="completed",
                )
                self.db.add(enrichment)
                self.db.commit()

                logger.info(f"Lead enriched: {lead.email}")

            return enriched_data

        except Exception as e:
            logger.error(f"Error enriching lead: {e}")
            raise

    async def _enrich_clearbit(self, email: str) -> Optional[Dict]:
        """Enrich lead using Clearbit API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://person.clearbit.com/v2/combined/find?email={email}",
                    headers={"Authorization": f"Bearer {settings.clearbit_api_key}"},
                    timeout=10.0,
                )
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            logger.warning(f"Clearbit enrichment failed: {e}")
            return None

    async def _enrich_hunter(self, company: str) -> Optional[Dict]:
        """Enrich company data using Hunter API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.hunter.io/v2/domain-search?company={company}",
                    params={"api_key": settings.hunter_api_key},
                    timeout=10.0,
                )
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            logger.warning(f"Hunter enrichment failed: {e}")
            return None

    async def _apply_enrichment(self, lead: LeadModel, enriched_data: Dict) -> None:
        """Apply enriched data to lead."""
        clearbit = enriched_data.get("clearbit", {})
        person = clearbit.get("person", {})
        company = clearbit.get("company", {})

        if person:
            if not lead.first_name and person.get("name", {}).get("givenName"):
                lead.first_name = person["name"]["givenName"]
            if not lead.last_name and person.get("name", {}).get("familyName"):
                lead.last_name = person["name"]["familyName"]
            if not lead.job_title and person.get("employment", {}).get("title"):
                lead.job_title = person["employment"]["title"]

        if company:
            if not lead.company and company.get("name"):
                lead.company = company["name"]
            if not lead.industry and company.get("category", {}).get("industry"):
                lead.industry = company["category"]["industry"]
            if not lead.company_size and company.get("metrics", {}).get("employees"):
                lead.company_size = str(company["metrics"]["employees"])

        lead.enriched_at = datetime.utcnow()
        self.db.commit()
