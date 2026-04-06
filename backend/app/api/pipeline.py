from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.db import get_db
from app.models.pipeline_run import PipelineRun
from app.pipeline.runner import run_pipeline
from app.profile import get_profile
from app.schemas.pipeline import PipelineRunOut

pipeline_router = APIRouter(prefix="/pipeline", tags=["pipeline"], dependencies=[Depends(verify_api_key)])
profile_router = APIRouter(prefix="/profile", tags=["profile"], dependencies=[Depends(verify_api_key)])


@pipeline_router.post("/run", response_model=PipelineRunOut)
async def trigger_pipeline():
    """Manually trigger the full discovery pipeline. Blocks until complete (~2 min max).
    SvelteKit callers should use HTTP timeout >= 120s."""
    pipeline_run = await run_pipeline()
    return PipelineRunOut.model_validate(pipeline_run)


@pipeline_router.get("/status", response_model=PipelineRunOut | None)
async def pipeline_status(db: AsyncSession = Depends(get_db)):
    """Return the most recent pipeline run record."""
    result = await db.execute(
        select(PipelineRun).order_by(PipelineRun.started_at.desc()).limit(1)
    )
    run = result.scalar_one_or_none()
    if run is None:
        return None
    return PipelineRunOut.model_validate(run)


@profile_router.post("/reload")
async def reload_profile():
    """Clear the profile cache and reload from disk. Returns validation result."""
    get_profile.cache_clear()
    try:
        profile = get_profile()
        return {"status": "ok", "name": profile.get("name"), "projects_count": len(profile.get("projects", []))}
    except ValueError as e:
        return {"status": "error", "detail": str(e)}
