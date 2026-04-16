import logging

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_db
from app.limiter import limiter
from app.profile import get_profile
from app.pipeline.runner import run_pipeline
from app.models.pipeline_run import PipelineRun
from app.schemas.pipeline import PipelineRunOut

logger = logging.getLogger(__name__)
router = APIRouter(tags=["pipeline"])


@router.post("/profile/reload")
@limiter.limit("10/minute")
async def reload_profile(request: Request):
    get_profile.cache_clear()
    try:
        profile = get_profile()
        return {
            "status": "ok",
            "name": profile.get("name"),
            "projects_count": len(profile.get("projects", [])),
        }
    except ValueError as e:
        return {"status": "error", "detail": str(e)}


@router.post("/pipeline/run")
@limiter.limit("2/minute")
async def trigger_pipeline(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger the lead discovery pipeline.

    This endpoint is synchronous — it waits for the full pipeline to complete
    before returning (expected duration: < 2 minutes).
    Callers must set HTTP timeout >= 120 seconds.
    """
    background_tasks.add_task(run_pipeline, db)
    return {"status": "ok", "message": "Pipeline triggered"}


@router.get("/pipeline/status", response_model=PipelineRunOut)
@limiter.limit("60/minute")
async def get_pipeline_status(request: Request, db: AsyncSession = Depends(get_db)):
    """Get the most recent pipeline run metadata."""
    result = await db.execute(
        select(PipelineRun).order_by(PipelineRun.started_at.desc()).limit(1)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="No pipeline runs found")
    return run
