from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import leads, pipeline, stats
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Phase 9: APScheduler will be started here
    yield
    # Phase 9: APScheduler will be shut down here


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
app.include_router(pipeline.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
