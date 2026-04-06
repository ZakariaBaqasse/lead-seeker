from fastapi import APIRouter, Depends

from app.auth import verify_api_key
from app.profile import get_profile

pipeline_router = APIRouter(prefix="/pipeline", tags=["pipeline"], dependencies=[Depends(verify_api_key)])
profile_router = APIRouter(prefix="/profile", tags=["profile"], dependencies=[Depends(verify_api_key)])

# pipeline_router endpoints will be added in Phase 8


@profile_router.post("/reload")
async def reload_profile():
    """Clear the profile cache and reload from disk. Returns validation result."""
    get_profile.cache_clear()
    try:
        profile = get_profile()
        return {"status": "ok", "name": profile.get("name"), "projects_count": len(profile.get("projects", []))}
    except ValueError as e:
        return {"status": "error", "detail": str(e)}
