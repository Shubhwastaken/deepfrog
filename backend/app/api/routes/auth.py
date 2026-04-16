from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.security import create_access_token

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

FAKE_USERS = {"admin@customs.ai": "secret"}

@router.post("/login")
def login(req: LoginRequest):
    if FAKE_USERS.get(req.email) != req.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": create_access_token({"sub": req.email}), "token_type": "bearer"}
