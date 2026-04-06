from fastapi import APIRouter, Depends

from app.auth import verify_api_key

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"], dependencies=[Depends(verify_api_key)])
