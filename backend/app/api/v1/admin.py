"""Admin endpoints for system statistics."""
import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request
from app.api.deps import get_current_user
from app.schemas.auth import UserContext
from app.services.ai.schema_index import SchemaIndexService

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

EVOLUTION_DIR = Path("../doc/evolution")


def _find_latest_summary() -> dict | None:
    """Find the latest evolution summary JSON file and return its contents."""
    if not EVOLUTION_DIR.exists():
        return None
    json_files = sorted(EVOLUTION_DIR.glob("*-summary.json"), reverse=True)
    if not json_files:
        return None
    return json.loads(json_files[0].read_text(encoding="utf-8"))


@router.get("/stats")
async def admin_stats(
    current_user: UserContext = Depends(get_current_user),
):
    """Get daily evolution stats (admin only)."""
    if current_user.role_level > 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    data = _find_latest_summary()
    if data:
        return data
    return {"status": "no_data", "message": "Evolution report not yet generated"}


@router.get("/schema-refresh")
async def schema_refresh(
    request: Request,
    current_user: UserContext = Depends(get_current_user),
):
    """Manual schema cache refresh (admin only).
    
    Requires admin role (role_level <= 1) to prevent unauthorized cache invalidation
    which could cause cache stampede under high concurrency.
    """
    if current_user.role_level > 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    svc: SchemaIndexService = request.app.state.schema_svc
    await svc.refresh()
    return {"status": "refreshed"}
