"""
Lead enrichment service using third-party APIs.
"""
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

import httpx
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from modules.lead_generation.models import Lead

settings = get_settings()


class EnrichmentService:
    """Service for enriching lead data."""

    @staticmethod
    async def enrich_lead(
        db: AsyncSession,
        lead_id: UUID,
        provider: str = "clearbit"
    ) -> Optional[Lead]:
        """
        Enrich lead data using external API.

        Args:
            db: Database session
            lead_id: Lead ID
            provider: Enrichment provider (clearbit, hunter)

        Returns:
            Enriched lead or None
        """
        try:
            result = await db.execute(
                select(Lead).where(Lead.id == lead_id)
            )
            lead = result.scalar_one_or_none()

            if not lead:
                logger.error(f"Lead not found: {lead_id}")
                return None

            enrichment_data = None

            if provider == "clearbit":
                enrichment_data = await EnrichmentService._enrich_with_clearbit(
                    lead.email
                )
            elif provider == "hunter":
                enrichment_data = await EnrichmentService._enrich_with_hunter(
                    lead.email
                )
            else:
                logger.warning(f"Unknown enrichment provider: {provider}")

            if enrichment_data:
                lead.enrichment_data = enrichment_data
                lead.enrichment_status = "completed"
                lead.enrichment_provider = provider
                lead.enriched_at = datetime.utcnow()

                # Update lead fields from enrichment data
                if "person" in enrichment_data:
                    person = enrichment_data["person"]
                    if not lead.first_name and "first_name" in person:
                        lead.first_name = person["first_name"]
                    if not lead.last_name and "last_name" in person:
                        lead.last_name = person["last_name"]
                    if not lead.job_title and "job_title" in person:
                        lead.job_title = person["job_title"]

                if "company" in enrichment_data:
                    company = enrichment_data["company"]
                    if not lead.company and "name" in company:
                        lead.company = company["name"]

                await db.commit()
                await db.refresh(lead)

                logger.info(f"Lead enriched successfully: {lead_id}")
                return lead
            else:
                lead.enrichment_status = "failed"
                await db.commit()
                logger.warning(f"Lead enrichment failed: {lead_id}")
                return lead

        except Exception as e:
            await db.rollback()
            logger.error(f"Error enriching lead: {e}")
            raise

    @staticmethod
    async def _enrich_with_clearbit(email: str) -> Optional[Dict[str, Any]]:
        """
        Enrich lead data using Clearbit API.

        Args:
            email: Email address

        Returns:
            Enrichment data or None
        """
        if not settings.clearbit_api_key:
            logger.warning("Clearbit API key not configured")
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://person.clearbit.com/v2/combined/find?email={email}",
                    headers={"Authorization": f"Bearer {settings.clearbit_api_key}"},
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Clearbit enrichment successful for: {email}")
                    return {
                        "person": {
                            "first_name": data.get("person", {}).get("name", {}).get("givenName"),
                            "last_name": data.get("person", {}).get("name", {}).get("familyName"),
                            "job_title": data.get("person", {}).get("employment", {}).get("title"),
                            "bio": data.get("person", {}).get("bio"),
                            "location": data.get("person", {}).get("location"),
                            "linkedin": data.get("person", {}).get("linkedin", {}).get("handle"),
                            "twitter": data.get("person", {}).get("twitter", {}).get("handle"),
                        },
                        "company": {
                            "name": data.get("company", {}).get("name"),
                            "domain": data.get("company", {}).get("domain"),
                            "industry": data.get("company", {}).get("category", {}).get("industry"),
                            "employees": data.get("company", {}).get("metrics", {}).get("employees"),
                            "revenue": data.get("company", {}).get("metrics", {}).get("estimatedAnnualRevenue"),
                            "description": data.get("company", {}).get("description"),
                        }
                    }
                elif response.status_code == 404:
                    logger.info(f"No Clearbit data found for: {email}")
                else:
                    logger.warning(f"Clearbit API error: {response.status_code}")

                return None
        except Exception as e:
            logger.error(f"Clearbit enrichment error: {e}")
            return None

    @staticmethod
    async def _enrich_with_hunter(email: str) -> Optional[Dict[str, Any]]:
        """
        Enrich lead data using Hunter API.

        Args:
            email: Email address

        Returns:
            Enrichment data or None
        """
        if not settings.hunter_api_key:
            logger.warning("Hunter API key not configured")
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.hunter.io/v2/email-verifier",
                    params={"email": email, "api_key": settings.hunter_api_key},
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json().get("data", {})
                    logger.info(f"Hunter enrichment successful for: {email}")
                    return {
                        "verification": {
                            "status": data.get("status"),
                            "score": data.get("score"),
                            "result": data.get("result"),
                        },
                        "person": {
                            "first_name": data.get("first_name"),
                            "last_name": data.get("last_name"),
                            "position": data.get("position"),
                        },
                        "sources": data.get("sources", [])
                    }
                else:
                    logger.warning(f"Hunter API error: {response.status_code}")

                return None
        except Exception as e:
            logger.error(f"Hunter enrichment error: {e}")
            return None
