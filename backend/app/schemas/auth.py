from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    user_code: str = Field(..., min_length=1, description="工号/学号")
    password: str = Field(..., min_length=1, description="密码")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    user_name: str
    role_level: int
    dept_code: str | None = None

class UserContext(BaseModel):
    """Injected into request context after auth."""
    user_id: str
    user_code: str
    user_name: str
    role_level: int
    dept_code: str | None = None
