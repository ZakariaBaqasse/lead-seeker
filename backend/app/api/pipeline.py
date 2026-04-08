import logging

from fastapi import APIRouter

from app.profile import get_profile

logger = logging.getLogger(__name__)
router = APIRouter(tags=["pipeline"])


@router.post("/profile/reload")
async def reload_profile():
    get_profile.cache_clear()
    try:
        profile = get_profile()
        return {"status": "ok", "name": profile.get("name"), "projects_count": len(profile.get("projects", []))}
    except ValueError as e:
        return {"status": "error", "detail": str(e)}
