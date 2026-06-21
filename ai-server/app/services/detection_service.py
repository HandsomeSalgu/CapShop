from fastapi import HTTPException

from app.core.config import settings
from app.schemas.detection_schema import AnalyzeFrameRequest, AnalyzeFrameResponse
from app.services.gpt_vision_detection_service import analyze_frame_with_gpt_vision
from app.services.mock_detection_service import analyze_frame_mock
from app.utils.image_utils import is_valid_base64_image


def analyze_frame(request: AnalyzeFrameRequest) -> AnalyzeFrameResponse:
    if not is_valid_base64_image(request.image_base64):
        raise HTTPException(
            status_code=400,
            detail="image_base64 must be a valid data:image base64 string",
        )

    provider = settings.ai_detection_provider.lower()

    if provider == "mock":
        return analyze_frame_mock(request)

    if provider == "gpt":
        return analyze_frame_with_gpt_vision(request)

    raise HTTPException(
        status_code=500,
        detail=f"Unsupported AI_DETECTION_PROVIDER: {settings.ai_detection_provider}",
    )
