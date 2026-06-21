from fastapi import FastAPI

from app.api.commerce_query_router import router as commerce_query_router
from app.api.detection_router import router as detection_router


app = FastAPI(
    title="SyncShopper AI Server",
    description="AI Detection server for SyncShopper",
    version="1.0.0",
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "syncshopper-ai-server",
    }


app.include_router(detection_router, prefix="/api/ai", tags=["AI Detection"])
app.include_router(commerce_query_router, prefix="/api/ai", tags=["Commerce Query"])
