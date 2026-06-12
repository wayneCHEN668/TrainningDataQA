from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import engine
from app.core.redis import redis_pool
from app.services.ai.schema_index import SchemaIndexService
from app.jobs.scheduler import scheduler, register_jobs
from app.schemas.health import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    redis_available = False
    try:
        schema_svc = SchemaIndexService(redis=redis_pool)
        await schema_svc.load()
        redis_available = True
    except Exception:
        schema_svc = SchemaIndexService(redis=None)
        await schema_svc.load()
    app.state.schema_svc = schema_svc
    register_jobs()
    scheduler.start()
    yield
    # Shutdown
    scheduler.shutdown(wait=False)
    await engine.dispose()
    if redis_available:
        try:
            await redis_pool.aclose()
        except Exception:
            pass


app = FastAPI(
    title="SkillCloudHS AI API",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/api/v1/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version="0.1.0")


@app.get("/api/v1/admin/schema-refresh")
async def schema_refresh():
    """Manual schema cache refresh (auth to be added in Phase 7)."""
    svc: SchemaIndexService = app.state.schema_svc
    await svc.refresh()
    return {"status": "refreshed"}
