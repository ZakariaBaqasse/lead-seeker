import asyncio
import logging
from datetime import datetime, timezone, date

from sqlalchemy.ext.asyncio import AsyncSession
from app.db import AsyncSessionLocal
from app.models.lead import Lead
from app.models.pipeline_run import PipelineRun
from app.pipeline.sources.serpapi import fetch_serpapi
from app.pipeline.sources.rss_feeds import fetch_rss_feeds
from app.pipeline.sources import dedupe_by_url
from app.pipeline.extractor import extract_article
from app.pipeline.fetcher import enrich_article_body
from app.pipeline.filter import filter_lead, is_duplicate
from app.pipeline.drafter import draft_email
from app.pipeline.enricher import enrich_lead
from app.pipeline.sources import RawArticle
from app.profile import get_profile

logger = logging.getLogger(__name__)


_processing_semaphore = asyncio.Semaphore(5)


async def _process_article(
    article: RawArticle, profile: dict | None
) -> tuple[int, int, dict | None]:
    """Process a single article with its own DB session.

    Returns (articles_processed_delta, leads_created_delta, error_dict | None).
    Acquires the semaphore individually so asyncio.gather() is bounded to
    _processing_semaphore's limit of concurrent Jina Reader requests.
    """
    async with _processing_semaphore:
        try:
            article = await enrich_article_body(article)
            extraction = await extract_article(article)
            if extraction is None:
                return 0, 0, None

            if not filter_lead(extraction):
                return 0, 0, None

            # Session 1: dedup check only
            async with AsyncSessionLocal() as session:
                if await is_duplicate(session, extraction):
                    return 0, 0, None

            # Enrichment (external API calls, no DB session)
            enrichment = await enrich_lead(extraction)

            funding_date = None
            if extraction.funding_date:
                try:
                    funding_date = date.fromisoformat(extraction.funding_date)
                except ValueError:
                    pass

            # Session 2: insert lead + draft email
            async with AsyncSessionLocal() as session:
                lead = Lead(
                    company_name=extraction.company_name,
                    company_domain=extraction.company_domain,
                    company_description=extraction.summary,
                    region=extraction.region,
                    country=extraction.country,
                    employee_count=enrichment.employee_count if enrichment else extraction.employee_count_estimate,
                    funding_amount=extraction.funding_amount,
                    funding_date=funding_date,
                    funding_round=extraction.funding_round,
                    news_headline=article.headline,
                    news_url=article.url,
                    cto_name=enrichment.cto_name if enrichment else None,
                    linkedin_url=enrichment.linkedin_url if enrichment else None,
                    product_description=enrichment.product_description if enrichment else None,
                    tech_stack=enrichment.tech_stack if enrichment else None,
                    status="draft",
                    email_draft=None,
                )
                session.add(lead)
                await session.commit()
                await session.refresh(lead)
                logger.info("Pipeline: created lead '%s'", lead.company_name)

                if profile:
                    lead_data = {
                        "company_name": lead.company_name,
                        "company_description": lead.company_description,
                        "funding_amount": lead.funding_amount,
                        "funding_round": lead.funding_round,
                        "funding_date": lead.funding_date,
                        "country": lead.country,
                        "region": lead.region,
                        "cto_name": lead.cto_name,
                        "product_description": lead.product_description,
                        "tech_stack": lead.tech_stack,
                    }
                    email_draft = await draft_email(lead_data, profile)
                    lead.email_draft = email_draft
                    await session.commit()

            return 1, 1, None

        except Exception as e:
            logger.error(
                "Pipeline: error processing article '%s': %s",
                article.headline[:80],
                e,
            )
            return 0, 0, {"article": article.headline[:80], "error": str(e)}


async def run_pipeline(session: AsyncSession) -> PipelineRun:
    """Run the full lead discovery pipeline.

    Creates a PipelineRun record, orchestrates all stages, and updates
    the record on completion. Uses try/except/else/finally to ensure the
    record is always updated, even on unhandled exceptions.
    """
    pipeline_run = PipelineRun(
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    session.add(pipeline_run)
    await session.commit()
    await session.refresh(pipeline_run)

    articles_fetched = 0
    articles_processed = 0
    leads_created = 0
    errors = []
    pipeline_run_status = "failed"

    try:
        # Step 1: Fetch from all sources concurrently
        logger.info("Pipeline: fetching from all sources")
        results = await asyncio.gather(
            fetch_serpapi(),
            fetch_rss_feeds(),
            return_exceptions=True,
        )

        all_articles = []
        source_names = ["serpapi", "rss_feeds"]
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("Source %s failed: %s", source_names[i], result)
                errors.append({"source": source_names[i], "error": str(result)})
            else:
                all_articles.extend(result)

        # Step 2: URL-level deduplication
        all_articles = dedupe_by_url(all_articles)
        articles_fetched = len(all_articles)
        logger.info("Pipeline: %d articles after dedup", articles_fetched)

        # Step 3: Load profile once
        try:
            profile = get_profile()
        except Exception as e:
            logger.error("Failed to load profile: %s", e)
            profile = None

        # Step 4: Process all articles in parallel, each acquiring the semaphore individually
        results = await asyncio.gather(
            *[_process_article(article, profile) for article in all_articles],
            return_exceptions=True,
        )
        for result in results:
            if isinstance(result, Exception):
                errors.append({"article": "unknown", "error": str(result)})
            else:
                processed_delta, created_delta, error = result
                articles_processed += processed_delta
                leads_created += created_delta
                if error:
                    errors.append(error)

        logger.info(
            "Pipeline complete: fetched=%d processed=%d leads=%d errors=%d",
            articles_fetched,
            articles_processed,
            leads_created,
            len(errors),
        )

    except Exception as pipeline_error:
        logger.error("Pipeline crashed: %s", pipeline_error, exc_info=True)
        errors.append({"pipeline": "fatal", "error": str(pipeline_error)})
        pipeline_run_status = "failed"
        # No raise — finally commits status="failed" and the return below sends PipelineRunOut
    else:
        pipeline_run_status = "completed"
    finally:
        pipeline_run.completed_at = datetime.now(timezone.utc)
        pipeline_run.articles_fetched = articles_fetched
        pipeline_run.articles_processed = articles_processed
        pipeline_run.leads_created = leads_created
        pipeline_run.errors = errors if errors else None
        pipeline_run.status = pipeline_run_status
        session.add(pipeline_run)
        try:
            await session.commit()
        except Exception as e:
            logger.error("Failed to update pipeline_run: %s", e)

    return pipeline_run
