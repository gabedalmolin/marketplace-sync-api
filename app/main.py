from fastapi import FastAPI

from app.api.health import router as health_router

app = FastAPI(
    title="Marketplace Sync API",
    version="0.1.0",
    description="Receive, store, and synchronize marketplace order events.",
)

app.include_router(health_router)
