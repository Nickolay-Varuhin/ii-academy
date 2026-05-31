"""Точка входа — FastAPI приложение «ИИ-Академия»."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db, async_session
from seed import seed_database
from config import CORS_ORIGINS, DEBUG
from routers import (auth_router, dialog_router, skills_router,
                     admin_router, hr_router, assignments_router,
                     reports_router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with async_session() as db:
        await seed_database(db)
    yield


app = FastAPI(
    title="ИИ-Академия API",
    description="Платформа развития Soft-Skills с AI-тьютором",
    version="3.1.0",
    lifespan=lifespan,
    debug=DEBUG,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(dialog_router.router)
app.include_router(skills_router.router)
app.include_router(hr_router.router)
app.include_router(admin_router.router)
app.include_router(assignments_router.router)
app.include_router(reports_router.router)


@app.get("/", tags=["Система"])
async def root():
    return {"name": "ИИ-Академия API", "version": "3.1.0", "docs": "/docs"}


@app.get("/api/health", tags=["Система"])
async def health():
    return {"status": "ok"}
