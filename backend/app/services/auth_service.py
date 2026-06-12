from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import UserInfo
from app.schemas.auth import UserContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

async def authenticate_user(db: AsyncSession, user_code: str, password: str) -> UserContext | None:
    result = await db.execute(
        select(UserInfo).where(UserInfo.user_code == user_code)
    )
    user = result.scalar_one_or_none()
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return UserContext(
        user_id=user.user_id,
        user_code=user.user_code,
        user_name=user.user_name,
        role_level=user.role_level,
        dept_code=user.dept_code,
    )
