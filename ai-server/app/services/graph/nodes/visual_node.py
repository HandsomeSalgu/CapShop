from typing import Any

from app.services.graph.state import ShoppingAnalysisState
from app.services.split_frame_analysis_service import analyze_visual_features, synthesize_initial_detection


def _visual_feature_analyzer_node(state: ShoppingAnalysisState) -> dict[str, Any]:
    return {"visual_analysis": analyze_visual_features(state["request"])}


def _frame_synthesizer_node(state: ShoppingAnalysisState) -> dict[str, Any]:
    frame_analysis = synthesize_initial_detection(
        state["ocr_analysis"],
        state["visual_analysis"],
    )
    return {"frame_analysis": frame_analysis}
