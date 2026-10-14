from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Family Tree API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


# Routers will be included here:
# app.include_router(auth.router, prefix="/api/v1")
# app.include_router(persons.router, prefix="/api/v1")
# app.include_router(relationships.router, prefix="/api/v1")
