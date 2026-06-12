"""Admin endpoints for system statistics."""
import json
from fastapi import APIRouter, Depends, HTTPException
import redis.asyncio as aioredis
from app.core.redis import get_redis
from app.api.deps import get_current_user
from app.schemas.auth import UserContext

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/stats")
async def admin_stats(
    current_user: UserContext = Depends(get_current_user),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Get daily evolution stats (admin only)."""
    if current_user.role_level > 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        cached = await redis.get("evolution_stats:daily")
        if cached:
            return json.loads(cached)
    except Exception:
        pass
    return {"status": "no_data", "message": "Evolution report not yet generated"}
