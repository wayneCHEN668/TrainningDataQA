from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import engine
from app.services.ai.schema_index import SchemaIndexService
from app.jobs.scheduler import scheduler, register_jobs
from app.schemas.health import HealthResponse
from app.api.v1.auth import router as auth_router
from app.api.v1.ai_query import router as ai_query_router
from app.api.v1.admin import router as admin_router
from app.api.v1.reports import router as reports_router
from app.jobs.cleanup_reports import cleanup_expired_reports


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    schema_svc = SchemaIndexService()
    await schema_svc.load()
    app.state.schema_svc = schema_svc
    register_jobs()
    scheduler.add_job(
        cleanup_expired_reports,
        "interval",
        hours=1,
        id="cleanup_reports",
        replace_existing=True,
    )
    scheduler.start()
    yield
    # Shutdown
    scheduler.shutdown(wait=False)
    await engine.dispose()


app = FastAPI(
    title="SkillCloudHS AI API",
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(auth_router)
app.include_router(ai_query_router)
app.include_router(admin_router)
app.include_router(reports_router, prefix="/api/v1")


@app.get("/api/v1/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version="0.1.0")


@app.get("/api/v1/admin/schema-refresh")
async def schema_refresh():
    """Manual schema cache refresh (auth to be added in Phase 7)."""
    svc: SchemaIndexService = app.state.schema_svc
    await svc.refresh()
    return {"status": "refreshed"}
