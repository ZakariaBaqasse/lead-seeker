import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import leads, stats
from app.api.pipeline import pipeline_router, profile_router
from app.config import settings
from app.pipeline.runner import run_pipeline

logger = logging.getLogger(__name__)


async def _scheduled_pipeline_job() -> None:
    """Wrapper for the daily pipeline cron job. Catches all exceptions to keep scheduler alive."""
    logger.info("Scheduled pipeline job starting...")
    try:
        run = await run_pipeline()
        logger.info(
            "Scheduled pipeline complete — leads_created=%d, errors=%d",
            run.leads_created,
            len(run.errors or []),
        )
    except Exception as e:
        # pipeline_run record is already updated to status='failed' inside run_pipeline()
        logger.error("Scheduled pipeline job failed: %s", e, exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _scheduled_pipeline_job,
        CronTrigger(
            hour=settings.PIPELINE_SCHEDULE_HOUR,
            minute=settings.PIPELINE_SCHEDULE_MINUTE,
            timezone="UTC",
        ),
        id="daily_pipeline",
        name="Daily lead discovery pipeline",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "Scheduler started — pipeline runs daily at %02d:%02d UTC",
        settings.PIPELINE_SCHEDULE_HOUR,
        settings.PIPELINE_SCHEDULE_MINUTE,
    )
    yield
    scheduler.shutdown(wait=False)
    logger.info("Scheduler shut down")


# Auth is applied per-router (not globally) so that /health is excluded.
# Each router in app/api/ includes `dependencies=[Depends(verify_api_key)]`.
app = FastAPI(title="Lead Seeker API", lifespan=lifespan)

# Dev-only CORS for the SvelteKit frontend
if "localhost" in settings.DATABASE_URL:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(leads.router)
app.include_router(stats.router)
app.include_router(pipeline_router, prefix="/api")
app.include_router(profile_router, prefix="/api")


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
