from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, report, results, upload
from app.core.config import settings
from app.db.models import Base
from app.db.session import get_engine
from app.services.auth_service import ensure_default_user

app = FastAPI(title="Customs Brain API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(results.router, prefix="/api", tags=["results"])
app.include_router(report.router, prefix="/api", tags=["report"])

@app.on_event("startup")
async def startup() -> None:
    async with get_engine().begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    await ensure_default_user()

@app.get("/health")
def health(): return {"status": "ok"}
