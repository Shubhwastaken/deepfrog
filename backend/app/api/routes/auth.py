from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.db.models import User
from app.services.auth_service import (
    begin_password_login,
    get_current_user,
    get_user_role,
    refresh_login_token,
    verify_login_otp,
)

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


class OTPVerifyRequest(BaseModel):
    challenge_id: str
    otp_code: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/login")
async def login(req: LoginRequest) -> dict:
    return await begin_password_login(req.email, req.password)


@router.post("/verify-otp")
async def verify_otp(req: OTPVerifyRequest) -> dict:
    return await verify_login_otp(req.challenge_id, req.otp_code)


@router.post("/refresh")
async def refresh(req: RefreshTokenRequest) -> dict:
    return await refresh_login_token(req.refresh_token)


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)) -> dict:
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": get_user_role(current_user),
    }
