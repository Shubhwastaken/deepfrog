from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db_session
from app.db.models import User
from app.core.security import create_access_token, get_password_hash, verify_password, get_email_hash, encryptor
import uuid

from typing import Optional

router = APIRouter()

class UserAuth(BaseModel):
    email: str
    password: str
    name: Optional[str] = None

@router.post("/register")
async def register(req: UserAuth, db: AsyncSession = Depends(get_db_session)):
    # Check if user already exists using blind index
    email_hash = get_email_hash(req.email)
    existing_user = await db.execute(select(User).filter(User.email_hash == email_hash))
    if existing_user.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    new_user = User(
        id=str(uuid.uuid4()),
        email_encrypted=encryptor.encrypt(req.email),
        email_hash=email_hash,
        password=get_password_hash(req.password),
        name_encrypted=encryptor.encrypt(req.name) if req.name else None
    )
    db.add(new_user)
    await db.commit()
    return {"message": "User registered successfully"}

@router.post("/login")
async def login(req: UserAuth, db: AsyncSession = Depends(get_db_session)):
    # Find user using blind index
    email_hash = get_email_hash(req.email)
    stmt = select(User).filter(User.email_hash == email_hash)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
        
    if not verify_password(req.password, user.password):
        raise HTTPException(status_code=401, detail="Incorrect password")
    
    return {"access_token": create_access_token({"sub": req.email}), "token_type": "bearer"}
