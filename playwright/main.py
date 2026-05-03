import logging
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Playwright Executor", version="1.0.0")

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "pool_size": 3,
        "pool_available": 3,
        "pool_busy": 0,
        "chromium_version": "120.0",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001)