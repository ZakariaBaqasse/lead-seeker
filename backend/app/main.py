from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import verify_api_key
from app.api.leads import router as leads_router
from app.api.pipeline import router as pipeline_router
from app.api.stats import router as stats_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # APScheduler setup will be added in Phase 9
    yield


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
