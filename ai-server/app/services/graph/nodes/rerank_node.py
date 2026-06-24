from typing import Any

from fastapi import HTTPException

from app.core.config import settings
from app.services.graph.candidate_utils import _merge_best_candidates
from app.services.graph.state import ShoppingAnalysisState
from app.services.scoring.visual_score import _fallback_visual_rerank, _gpt_visual_rerank


def _visual_reranker_node(state: ShoppingAnalysisState) -> dict[str, Any]:
    candidates = state.get("filtered_candidates") or []
    if not candidates:
        return {
            "reranked_candidates": [],
            "best_candidates": state.get("best_candidates") or [],
        }

    provider = settings.ai_visual_reranker_provider.lower()
    if provider == "mock":
        reranked = _fallback_visual_rerank(candidates)
    elif provider == "gpt":
        reranked = _gpt_visual_rerank(state["request"], state["frame_analysis"], candidates)
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Unsupported AI_VISUAL_RERANKER_PROVIDER: {settings.ai_visual_reranker_provider}",
        )

    best_candidates = _merge_best_candidates(
        state.get("best_candidates") or [],
        reranked,
        limit=state["request"].max_candidates,
    )

    return {
        "reranked_candidates": reranked,
        "best_candidates": best_candidates,
    }
