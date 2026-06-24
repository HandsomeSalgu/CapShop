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
        should_skip, score_stats = _should_skip_gpt_visual_rerank(candidates)
        if should_skip:
            print(
                "\n[SyncShopper Visual Reranker] "
                "skipped GPT visual rerank because text score was strong enough "
                f"candidate_count={len(candidates)} "
                f"top_text_score={score_stats['top_text_score']:.3f} "
                f"top3_avg_text_score={score_stats['top3_avg_text_score']:.3f} "
                f"top_threshold={settings.skip_visual_rerank_top_score:.3f} "
                f"avg_threshold={settings.skip_visual_rerank_avg_score:.3f}",
                flush=True,
            )
            reranked = _fallback_visual_rerank(
                candidates,
                visual_reason="skipped GPT visual rerank because text score was strong enough",
            )
        else:
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


def _should_skip_gpt_visual_rerank(candidates: list[Any]) -> tuple[bool, dict[str, float]]:
    text_scores = sorted(
        [float(getattr(candidate, "text_score", 0.0) or 0.0) for candidate in candidates],
        reverse=True,
    )
    top_text_score = text_scores[0] if text_scores else 0.0
    top_three_scores = text_scores[:3]
    top3_avg_text_score = (
        sum(top_three_scores) / len(top_three_scores)
        if top_three_scores
        else 0.0
    )
    should_skip = (
        (len(candidates) <= 3 and top_text_score >= settings.skip_visual_rerank_top_score)
        or top3_avg_text_score >= settings.skip_visual_rerank_avg_score
    )

    return should_skip, {
        "top_text_score": top_text_score,
        "top3_avg_text_score": top3_avg_text_score,
    }
