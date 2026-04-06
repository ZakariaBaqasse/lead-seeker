import logging
from datetime import date, datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.pipeline import ExtractionResult
from app.models.lead import Lead

logger = logging.getLogger(__name__)

VALID_REGIONS = {"Europe", "USA"}
MIN_EMPLOYEES = 10
MAX_EMPLOYEES = 50
MAX_FUNDING_AGE_DAYS = 365


def filter_lead(extraction: ExtractionResult) -> bool:
    """Return True if the lead passes all filter criteria, False if it should be rejected."""
    if not extraction.is_relevant:
        logger.debug("Rejected (not relevant): %s", extraction.company_name)
        return False

    if extraction.sector != "GenAI":
        logger.debug("Rejected (sector=%s): %s", extraction.sector, extraction.company_name)
        return False

    if extraction.region not in VALID_REGIONS:
        logger.debug("Rejected (region=%s): %s", extraction.region, extraction.company_name)
        return False

    if extraction.employee_count_estimate is not None:
        if not (MIN_EMPLOYEES <= extraction.employee_count_estimate <= MAX_EMPLOYEES):
            logger.debug(
                "Rejected (employees=%s): %s",
                extraction.employee_count_estimate,
                extraction.company_name,
            )
            return False

    if not extraction.company_name or not extraction.funding_amount or not extraction.funding_date:
        logger.debug("Rejected (missing required fields): %s", extraction.company_name)
        return False

    try:
        funding_date = datetime.strptime(extraction.funding_date, "%Y-%m-%d").date()
        cutoff = date.today() - timedelta(days=MAX_FUNDING_AGE_DAYS)
        if funding_date < cutoff:
            logger.debug(
                "Rejected (funding too old=%s): %s", funding_date, extraction.company_name
            )
            return False
    except (ValueError, TypeError) as e:
        logger.debug(
            "Rejected (invalid funding_date=%s): %s — %s",
            extraction.funding_date,
            extraction.company_name,
            e,
        )
        return False

    return True


async def is_duplicate(session: AsyncSession, extraction: ExtractionResult) -> bool:
    """Check if a lead already exists in the DB. Returns True if duplicate."""
    if extraction.company_domain:
        result = await session.execute(
            select(Lead).where(Lead.company_domain == extraction.company_domain)
        )
        if result.scalar_one_or_none() is not None:
            logger.debug("Duplicate (domain match): %s", extraction.company_domain)
            return True

    if extraction.company_name:
        result = await session.execute(
            select(Lead).where(func.lower(Lead.company_name) == extraction.company_name.lower())
        )
        if result.scalar_one_or_none() is not None:
            logger.debug("Duplicate (name match): %s", extraction.company_name)
            return True

    return False
