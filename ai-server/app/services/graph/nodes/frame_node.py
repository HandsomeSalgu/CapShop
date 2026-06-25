from concurrent.futures import ThreadPoolExecutor
from typing import Any

from fastapi import HTTPException

from app.services.graph.state import ShoppingAnalysisState
from app.services.split_frame_analysis_service import (
    analyze_ocr,
    analyze_visual_features,
    koreanize_visual_analysis,
    synthesize_initial_detection,
)
from app.services.gemini_vision_detection_service import analyze_frame_with_gemini_vision
from app.schemas.analysis_graph_schema import OcrAnalysisResult, VisualFeatureAnalysisResult
from app.utils.image_utils import is_valid_base64_image


def _frame_analyzer_node(state: ShoppingAnalysisState) -> dict[str, Any]:
    request = state["request"]
    if not is_valid_base64_image(request.image_base64):
        raise HTTPException(
            status_code=400,
            detail="image_base64 must be a valid data:image base64 string",
        )

    if request.search_mode == "fast":
        frame_analysis = analyze_frame_with_gemini_vision(request)
        return {
            "ocr_analysis": OcrAnalysisResult(
                confidence=0.0,
                reason="Fast mode uses direct Gemini image identification instead of OCR.",
            ),
            "visual_analysis": VisualFeatureAnalysisResult(
                product_type=frame_analysis.category_name,
                category_name=frame_analysis.category_name,
                color=frame_analysis.color,
                shape=frame_analysis.shape,
                key_features=frame_analysis.key_features,
                confidence=frame_analysis.confidence,
                reason="Fast mode direct Gemini image identification.",
            ),
            "frame_analysis": frame_analysis,
        }

    with ThreadPoolExecutor(max_workers=2) as executor:
        ocr_future = executor.submit(analyze_ocr, request)
        visual_future = executor.submit(analyze_visual_features, request)
        ocr_analysis = ocr_future.result()
        visual_analysis = koreanize_visual_analysis(visual_future.result())

    frame_analysis = synthesize_initial_detection(ocr_analysis, visual_analysis)
    return {
        "ocr_analysis": ocr_analysis,
        "visual_analysis": visual_analysis,
        "frame_analysis": frame_analysis,
    }
