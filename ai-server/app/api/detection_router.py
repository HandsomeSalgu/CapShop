from fastapi import APIRouter

from app.schemas.detection_schema import AnalyzeFrameRequest, AnalyzeFrameResponse
from app.services.detection_service import analyze_frame


router = APIRouter()


@router.post("/analyze-frame", response_model=AnalyzeFrameResponse)
def analyze_frame_endpoint(request: AnalyzeFrameRequest):
    return analyze_frame(request)
