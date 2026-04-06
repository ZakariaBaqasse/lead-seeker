from fastapi import APIRouter, Depends

from app.auth import verify_api_key

router = APIRouter(prefix="/api/leads", tags=["leads"], dependencies=[Depends(verify_api_key)])
