import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import verify_api_key
from app.config import settings
from app.api.leads import router as leads_router
from app.api.pipeline import router as pipeline_router
from app.api.stats import router as stats_router

logger = logging.getLogger(__name__)


async def _scheduled_pipeline_job():
    from app.db import AsyncSessionLocal
    from app.pipeline.runner import run_pipeline
    session = AsyncSessionLocal()
    try:
        logger.info("Scheduled pipeline starting")
        await run_pipeline(session)
        logger.info("Scheduled pipeline finished")
    except Exception as e:
        logger.error("Scheduled pipeline error: %s", e, exc_info=True)
    finally:
        await session.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _scheduled_pipeline_job,
        trigger="cron",
        hour=settings.PIPELINE_SCHEDULE_HOUR,
        minute=settings.PIPELINE_SCHEDULE_MINUTE,
        timezone="UTC",
        id="daily_pipeline",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "Scheduler started: daily pipeline at %02d:%02d UTC",
        settings.PIPELINE_SCHEDULE_HOUR,
        settings.PIPELINE_SCHEDULE_MINUTE,
    )
    yield
    scheduler.shutdown(wait=False)
    logger.info("Scheduler shut down")


app = FastAPI(
    title="Lead Seeker API",
    lifespan=lifespan,
    dependencies=[Depends(verify_api_key)],
)

# Dev-only CORS — not needed in production (SvelteKit calls FastAPI server-side)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(leads_router, prefix="/api")
app.include_router(pipeline_router, prefix="/api")
app.include_router(stats_router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
