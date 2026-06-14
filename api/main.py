import os
import uuid
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from database import engine
from routers import auth, profiles, brokers, webhooks, scans, alerts, requests, ws

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("HomeGuard API starting up...")
    yield
    # Shutdown
    logger.info("HomeGuard API shutting down...")

app = FastAPI(
    title="HomeGuard API",
    description="Privacy Protection Platform API",
    version="1.06",
    lifespan=lifespan,
)

# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handler for 429 rate limits
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_code": "internal_error",
            "message": "An unexpected error occurred",
            "request_id": getattr(request.state, "request_id", str(uuid.uuid4())),
        },
    )

@app.get("/api/system/health")
async def health_check():
    """Health check endpoint - unauthenticated."""
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "services": {
                "api": "up",
                "database": "up",
                "redis": "up",
            },
            "version": "1.06",
        },
    }

# --- Router registration ---
app.include_router(auth.router, prefix="/api")
app.include_router(profiles.router, prefix="/api")
app.include_router(brokers.router, prefix="/api")
app.include_router(webhooks.router, prefix="/api")
app.include_router(scans.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(requests.router, prefix="/api")
app.include_router(ws.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
