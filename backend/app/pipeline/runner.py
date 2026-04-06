import asyncio
import logging
import uuid
from datetime import datetime, date as date_type, timezone

from app.db import AsyncSessionLocal
from app.models.lead import Lead
from app.models.pipeline_run import PipelineRun
from app.pipeline.sources import dedupe_by_url
from app.pipeline.sources.google_news import fetch_google_news
from app.pipeline.sources.gnews import fetch_gnews
from app.pipeline.sources.yc_directory import fetch_yc_directory
from app.pipeline.sources.rss_feeds import fetch_rss_feeds
from app.pipeline.extractor import extract_article
from app.pipeline.filter import filter_lead, is_duplicate
from app.pipeline.drafter import draft_email
from app.profile import get_profile

logger = logging.getLogger(__name__)


async def run_pipeline() -> PipelineRun:
    """Run the full lead discovery pipeline. Returns the completed PipelineRun record."""
    async with AsyncSessionLocal() as session:
        run = PipelineRun(
            id=uuid.uuid4(),
            started_at=datetime.now(timezone.utc),
            status="running",
            articles_fetched=0,
            articles_processed=0,
            leads_created=0,
            errors=[],
        )
        session.add(run)
        await session.flush()

        errors: list[str] = []
        leads_created = 0
        articles_processed = 0

        try:
            logger.info("Pipeline: fetching from all sources...")
            results = await asyncio.gather(
                fetch_google_news(),
                fetch_gnews(),
                fetch_yc_directory(),
                fetch_rss_feeds(),
                return_exceptions=True,
            )

            all_articles = []
            for r in results:
                if isinstance(r, Exception):
                    errors.append(f"Source fetch error: {r}")
                    logger.warning("Source fetch error: %s", r)
                else:
                    all_articles.extend(r)

            unique_articles = dedupe_by_url(all_articles)
            articles_fetched = len(unique_articles)
            run.articles_fetched = articles_fetched
            logger.info("Pipeline: %d unique articles after dedup", articles_fetched)

            try:
                profile = get_profile()
            except ValueError as e:
                errors.append(f"Profile load error: {e}")
                profile = None

            for article in unique_articles:
                try:
                    articles_processed += 1

                    extraction = await extract_article(article)
                    if extraction is None:
                        logger.debug("Skipping article (extraction failed): %s", article.url)
                        continue

                    if not filter_lead(extraction):
                        logger.debug("Skipping article (filtered out): %s", extraction.company_name)
                        continue

                    if await is_duplicate(session, extraction):
                        logger.debug("Skipping article (duplicate): %s", extraction.company_name)
                        continue

                    funding_date = None
                    if extraction.funding_date:
                        try:
                            funding_date = date_type.fromisoformat(extraction.funding_date)
                        except ValueError:
                            pass

                    lead = Lead(
                        id=uuid.uuid4(),
                        company_name=extraction.company_name,
                        company_domain=extraction.company_domain,
                        company_description=extraction.summary,
                        region=extraction.region,
                        country=extraction.country,
                        employee_count=extraction.employee_count_estimate,
                        funding_amount=extraction.funding_amount,
                        funding_date=funding_date,
                        funding_round=extraction.funding_round,
                        news_headline=article.headline,
                        news_url=article.url,
                        status="draft",
                    )
                    session.add(lead)
                    await session.flush()

                    if profile:
                        lead_data = {
                            "company_name": lead.company_name,
                            "company_description": lead.company_description,
                            "summary": lead.company_description,
                            "funding_amount": lead.funding_amount,
                            "funding_round": lead.funding_round,
                            "funding_date": lead.funding_date,
                            "country": lead.country,
                            "region": lead.region,
                        }
                        email_draft = await draft_email(lead_data, profile)
                        if email_draft:
                            lead.email_draft = email_draft
                        else:
                            logger.warning("Email draft failed for lead: %s", lead.company_name)

                    leads_created += 1
                    logger.info("Created lead: %s", lead.company_name)

                except Exception as e:
                    error_msg = f"Error processing article {article.url}: {e}"
                    errors.append(error_msg)
                    logger.error(error_msg, exc_info=True)

            run.articles_processed = articles_processed
            run.leads_created = leads_created
            run.errors = errors if errors else None
            run.completed_at = datetime.now(timezone.utc)
            run.status = "completed"
            await session.commit()
            logger.info("Pipeline complete: %d leads created, %d errors", leads_created, len(errors))

        except Exception as e:
            run.status = "failed"
            run.errors = [str(e)]
            run.completed_at = datetime.now(timezone.utc)
            try:
                await session.commit()
            except Exception:
                await session.rollback()
            logger.error("Pipeline failed: %s", e, exc_info=True)
            raise

        return run
