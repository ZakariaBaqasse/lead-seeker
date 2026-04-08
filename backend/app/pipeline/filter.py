import logging
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead
from app.schemas.lead import ExtractionResult

logger = logging.getLogger(__name__)

MIN_EMPLOYEES = 10
MAX_EMPLOYEES = 50
MAX_FUNDING_AGE_DAYS = 365  # 12 months


def filter_lead(extraction: ExtractionResult) -> bool:
    """Return True if the lead passes all filters (should be kept), False if it should be discarded."""

    if not extraction.is_relevant:
        logger.debug("Filtered out (not relevant): %s", extraction.company_name)
        return False

    if not extraction.company_name:
        logger.debug("Filtered out (missing company_name)")
        return False

    if not extraction.funding_amount:
        logger.debug("Filtered out (missing funding_amount): %s", extraction.company_name)
        return False

    if not extraction.funding_date:
        logger.debug("Filtered out (missing funding_date): %s", extraction.company_name)
        return False

    # Sector filter
    if extraction.sector and extraction.sector.upper() != "GENAI":
        logger.debug("Filtered out (sector=%s): %s", extraction.sector, extraction.company_name)
        return False

    # Region filter
    if extraction.region and extraction.region.upper() not in {"EUROPE", "USA"}:
        logger.debug("Filtered out (region=%s): %s", extraction.region, extraction.company_name)
        return False

    # Employee count filter (only apply if present)
    if extraction.employee_count_estimate is not None:
        if not (MIN_EMPLOYEES <= extraction.employee_count_estimate <= MAX_EMPLOYEES):
            logger.debug(
                "Filtered out (employees=%d): %s",
                extraction.employee_count_estimate,
                extraction.company_name,
            )
            return False

    # Funding date recency filter
    try:
        funding_date = date.fromisoformat(extraction.funding_date)
        cutoff = date.today() - timedelta(days=MAX_FUNDING_AGE_DAYS)
        if funding_date < cutoff:
            logger.debug(
                "Filtered out (funding too old: %s): %s", funding_date, extraction.company_name
            )
            return False
    except (ValueError, TypeError):
        logger.debug(
            "Filtered out (invalid funding_date '%s'): %s",
            extraction.funding_date,
            extraction.company_name,
        )
        return False

    return True


async def is_duplicate(session: AsyncSession, extraction: ExtractionResult) -> bool:
    """Return True if this lead already exists in the database."""

    # Domain-based check (uses the partial unique index)
    if extraction.company_domain:
        result = await session.execute(
            select(Lead.id).where(Lead.company_domain == extraction.company_domain).limit(1)
        )
        if result.scalar_one_or_none() is not None:
            logger.debug("Duplicate (domain match): %s", extraction.company_domain)
            return True

    # Name-based fallback: case-insensitive match
    if extraction.company_name:
        result = await session.execute(
            select(Lead.id)
            .where(func.lower(Lead.company_name) == extraction.company_name.lower())
            .limit(1)
        )
        if result.scalar_one_or_none() is not None:
            logger.debug("Duplicate (name match): %s", extraction.company_name)
            return True

    return False
