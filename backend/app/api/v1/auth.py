from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import create_access_token
from app.services.auth_service import authenticate_user
from app.schemas.auth import LoginRequest, TokenResponse, UserContext
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, body.user_code, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user_code or password",
        )
    token = create_access_token(data=user.model_dump())
    return TokenResponse(
        access_token=token,
        user_id=user.user_id,
        user_name=user.user_name,
        role_level=user.role_level,
        dept_code=user.dept_code,
    )

@router.get("/me", response_model=UserContext)
async def me(current_user: UserContext = Depends(get_current_user)):
    return current_user
