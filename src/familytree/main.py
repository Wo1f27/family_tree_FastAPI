"""FastAPI application with Jinja2 templates and REST API."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from familytree.core.database import engine, init_db
from familytree.core.config import settings
from familytree.api.v1.endpoints import pages, persons, photos


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database (tables + migrations)
    init_db()
    yield


app = FastAPI(title="Family Tree Web", version="0.1.0", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
static_dir = Path(__file__).resolve().parent / "static"
print(f"Static directory: {static_dir} (exists: {static_dir.exists()})")
if not static_dir.exists():
    raise RuntimeError(f"Static directory not found: {static_dir}")
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Uploads - serve photo files
uploads_dir = Path(__file__).resolve().parent / "uploads" / "photos"
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# Include routers
app.include_router(pages.router)
app.include_router(persons.router)
app.include_router(photos.router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    print(f"Запуск Family Tree Web на http://{settings.host}:{settings.port}")

    uvicorn.run(
        "familytree.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )
