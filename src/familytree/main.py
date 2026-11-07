"""FastAPI application with Jinja2 templates and REST API."""

from __future__ import annotations

import threading
import time
import webbrowser

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from familytree.core.database import engine, init_db
from familytree.core.config import settings
from familytree.api.v1.endpoints import pages, persons

app = FastAPI(title="Family Tree Web", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Init DB (must be called after models are imported)
init_db()

# Include routers
app.include_router(pages.router)
app.include_router(persons.router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


# Auto-open browser on startup
def open_browser() -> None:
    time.sleep(2)
    url = f"http://{settings.host}:{settings.port}"
    try:
        webbrowser.open(url)
    except Exception:
        pass


threading.Thread(target=open_browser, daemon=True).start()


if __name__ == "__main__":
    import uvicorn

    print(f"Запуск Family Tree Web на http://{settings.host}:{settings.port}")
    print("Откроется браузер автоматически...")

    uvicorn.run(
        "familytree.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )
