from typing import Any

from fastapi import HTTPException

from app.services.graph.state import ShoppingAnalysisState
from app.services.split_frame_analysis_service import analyze_ocr
from app.utils.image_utils import is_valid_base64_image


def _ocr_analyzer_node(state: ShoppingAnalysisState) -> dict[str, Any]:
    request = state["request"]
    if not is_valid_base64_image(request.image_base64):
        raise HTTPException(
            status_code=400,
            detail="image_base64 must be a valid data:image base64 string",
        )
    return {"ocr_analysis": analyze_ocr(request)}
