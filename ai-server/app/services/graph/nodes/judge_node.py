from typing import Any

from fastapi import HTTPException

from app.core.config import settings
from app.schemas.analysis_graph_schema import ProductCandidate, ResultQuality, ShoppingAnalysisResponse
from app.services.gms_openai_client import call_chat_completion, extract_json_object
from app.services.graph.candidate_utils import _is_recommendable_product
from app.services.graph.debug import _model_to_dict, _print_graph_debug
from app.services.graph.state import ShoppingAnalysisState
from app.services.prompts.judge_prompt import build_result_judge_messages
from app.services.scoring.category_rules import _clamp


def _result_judge_node(state: ShoppingAnalysisState) -> dict[str, Any]:
    provider = settings.ai_result_judge_provider.lower()

    if provider == "mock":
        quality = _fallback_result_judge(state.get("best_candidates") or [])
    elif provider == "gpt":
        quality = _gpt_result_judge(state)
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Unsupported AI_RESULT_JUDGE_PROVIDER: {settings.ai_result_judge_provider}",
        )

    return {"quality": quality}

def _final_formatter_node(state: ShoppingAnalysisState) -> dict[str, Any]:
    best_candidates = state.get("best_candidates") or []
    quality = state["quality"]
    strong_candidates = [
        candidate
        for candidate in best_candidates
        if _is_recommendable_product(candidate)
        if candidate.final_score >= 0.62 or candidate.visual_score >= 0.62
    ][:5]
    similar_candidates = [
        candidate
        for candidate in best_candidates
        if candidate.final_score >= 0.42 or candidate.visual_score >= 0.42 or candidate.text_score >= 0.5
    ][:5]

    if quality.is_good and strong_candidates:
        selected = strong_candidates
        similar = []
        match_status = "GOOD_MATCH"
        message = "Detected product has enough high-confidence search matches."
    elif similar_candidates:
        selected = []
        similar = similar_candidates
        match_status = "SIMILAR_ONLY"
        message = "No reliable exact match was found. Similar candidates are separated for review."
    else:
        selected = []
        similar = []
        match_status = "LOW_CONFIDENCE"
        message = "No reliable product recommendation was found from the current search results."

    response = ShoppingAnalysisResponse(
        frame_analysis=state["frame_analysis"],
        ocr_analysis=state.get("ocr_analysis"),
        visual_analysis=state.get("visual_analysis"),
        search_identification=state.get("search_identification"),
        query=state["query"],
        selected_products=selected,
        similar_products=similar,
        google_search_results=state.get("google_search_results") or [],
        match_status=match_status,
        message=message,
        searched_products_count=len(state.get("search_candidates") or []),
        filtered_products_count=len(state.get("filtered_candidates") or []),
        quality=quality,
        retry_count=state.get("retry_count", 0),
        tried_queries=state.get("tried_queries") or [],
        source_counts=state.get("source_counts") or {},
        google_source_counts=state.get("google_source_counts") or {},
    )

    return {"response": response}

def _fallback_result_judge(candidates: list[ProductCandidate]) -> ResultQuality:
    similar_candidates = [
        candidate
        for candidate in candidates
        if candidate.final_score >= 0.6 or candidate.visual_score >= 0.6
    ]
    top_three = candidates[:3]
    average_top_score = (
        sum(candidate.final_score for candidate in top_three) / len(top_three)
        if top_three
        else 0.0
    )
    is_good = len(similar_candidates) >= 3 and average_top_score >= 0.6

    return ResultQuality(
        is_good=is_good,
        score=_clamp(average_top_score),
        enough_similar_count=len(similar_candidates),
        reason=(
            "Top candidates have enough text/visual similarity."
            if is_good
            else "Fewer than 3 candidates passed the similarity threshold."
        ),
    )

def _gpt_result_judge(state: ShoppingAnalysisState) -> ResultQuality:
    candidates = state.get("best_candidates") or []
    raw_content = call_chat_completion(
        build_result_judge_messages(
            detected_product=_model_to_dict(state["frame_analysis"]),
            query=_model_to_dict(state["query"]),
            candidates=[_model_to_dict(candidate) for candidate in candidates[:8]],
        ),
        model=settings.gms_openai_query_model,
        temperature=0.0,
    )
    parsed = extract_json_object(raw_content)
    _print_graph_debug("result_judge.ai_response", {
        "raw_content": raw_content,
        "parsed": parsed,
    })

    return ResultQuality(
        is_good=bool(parsed.get("is_good")),
        score=_clamp(parsed.get("score", 0.0)),
        enough_similar_count=max(0, int(parsed.get("enough_similar_count", 0) or 0)),
        reason=str(parsed.get("reason") or "").strip() or "AI judged result quality.",
    )
