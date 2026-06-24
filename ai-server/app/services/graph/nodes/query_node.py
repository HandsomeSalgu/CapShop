from typing import Any

from fastapi import HTTPException

from app.core.config import settings
from app.schemas.commerce_query_schema import CommerceQueryResponse
from app.services.commerce_query_service import generate_commerce_query, _koreanize_search_query
from app.services.gemini_client import call_chat_completion, extract_json_object
from app.services.graph.debug import _model_to_dict, _print_graph_debug
from app.services.graph.query_helpers import (
    _category_queries,
    _commerce_request_from_frame,
    _flatten_source_queries,
    _korean_naver_queries,
    _query_candidates_by_source,
    _query_list,
    _to_commerce_request,
    _visible_text_queries,
    _visual_queries,
    _with_query_suffix,
)
from app.services.graph.state import ShoppingAnalysisState
from app.services.prompts.query_prompt import build_retry_query_messages
from app.services.scoring.category_rules import _clamp


def _query_generator_node(state: ShoppingAnalysisState) -> dict[str, Any]:
    request = state["request"]
    frame_analysis = state["frame_analysis"]
    commerce_request = _to_commerce_request(request, frame_analysis)
    query = generate_commerce_query(commerce_request)
    source_queries = _query_candidates_by_source(query, frame_analysis)

    return {
        "query": query,
        "active_queries": _flatten_source_queries(source_queries),
        "source_queries": source_queries,
    }

def _retry_query_generator_node(state: ShoppingAnalysisState) -> dict[str, Any]:
    provider = settings.ai_commerce_query_provider.lower()
    retry_count = state.get("retry_count", 0) + 1

    if provider == "gemini":
        query = _gemini_retry_query(state)
    elif provider == "mock":
        query = _fallback_retry_query(state)
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Unsupported AI_COMMERCE_QUERY_PROVIDER: {settings.ai_commerce_query_provider}",
        )

    source_queries = _query_candidates_by_source(query, state["frame_analysis"])
    return {
        "query": query,
        "active_queries": _flatten_source_queries(source_queries),
        "source_queries": source_queries,
        "retry_count": retry_count,
    }

def _gemini_retry_query(state: ShoppingAnalysisState) -> CommerceQueryResponse:
    candidates = state.get("best_candidates") or []
    raw_content = call_chat_completion(
        build_retry_query_messages(
            detected_product=_model_to_dict(state["frame_analysis"]),
            previous_query=_model_to_dict(state["query"]),
            tried_queries=state.get("tried_queries") or [],
            quality=_model_to_dict(state["quality"]),
            top_candidates=[_model_to_dict(candidate) for candidate in candidates[:5]],
        ),
        model=settings.gemini_query_model,
        temperature=0.25,
    )
    parsed = extract_json_object(raw_content)
    _print_graph_debug("retry_query_generator.ai_response", {
        "raw_content": raw_content,
        "parsed": parsed,
    })
    return _normalize_query_response(parsed, state)

def _fallback_retry_query(state: ShoppingAnalysisState) -> CommerceQueryResponse:
    frame_analysis = state["frame_analysis"]
    query_context = _commerce_request_from_frame(frame_analysis)
    tried_queries = set(query.lower() for query in state.get("tried_queries") or [])
    candidates = _korean_naver_queries([
        " ".join(part for part in [frame_analysis.brand, frame_analysis.model_name] if part),
        " ".join(part for part in [frame_analysis.brand, frame_analysis.target_name] if part),
        " ".join(part for part in [frame_analysis.color, frame_analysis.shape, frame_analysis.category_name] if part),
        " ".join(part for part in [frame_analysis.target_name, "정품"] if part),
        frame_analysis.category_name,
    ], query_context)
    fresh_candidates = [query for query in candidates if query and query.lower() not in tried_queries]

    raw_primary_query = fresh_candidates[0] if fresh_candidates else f"{frame_analysis.target_name} 상품"
    primary_query = _koreanize_search_query(raw_primary_query, query_context) or "상품"
    fallback_queries = _korean_naver_queries(fresh_candidates[1:5], query_context)
    exact_queries = _korean_naver_queries(_visible_text_queries(frame_analysis), query_context)
    visual_queries = _korean_naver_queries(_visual_queries(frame_analysis), query_context)
    category_queries = _korean_naver_queries(_category_queries(frame_analysis), query_context)

    return CommerceQueryResponse(
        primary_query=primary_query,
        exact_text_queries=exact_queries,
        visual_queries=visual_queries,
        category_queries=category_queries,
        shopping_queries=_korean_naver_queries([primary_query, *exact_queries, *visual_queries, *category_queries], query_context)[:6],
        image_queries=_korean_naver_queries([*visual_queries, *exact_queries], query_context)[:6],
        blog_queries=_korean_naver_queries([*_with_query_suffix(exact_queries, "후기"), *_with_query_suffix(visual_queries, "착용")], query_context)[:5],
        cafe_queries=_korean_naver_queries([*_with_query_suffix(exact_queries, "정보"), *_with_query_suffix(visual_queries, "후기")], query_context)[:5],
        web_queries=_korean_naver_queries([*exact_queries, *category_queries, primary_query], query_context)[:6],
        fallback_queries=fallback_queries,
        normalized_brand=frame_analysis.brand,
        normalized_model=frame_analysis.model_name,
        normalized_category=frame_analysis.category_name,
        query_confidence=_clamp(frame_analysis.confidence * 0.9),
        reason="Previous result quality was low, so a broader mock retry query was generated.",
    )

def _normalize_query_response(parsed: dict[str, Any], state: ShoppingAnalysisState) -> CommerceQueryResponse:
    frame_analysis = state["frame_analysis"]
    query_context = _commerce_request_from_frame(frame_analysis)
    primary_query = _koreanize_search_query(
        str(parsed.get("primary_query") or frame_analysis.target_name or "상품").strip(),
        query_context,
    ) or "상품"
    fallback_queries = parsed.get("fallback_queries") or []
    exact_queries = _korean_naver_queries([*_query_list(parsed.get("exact_text_queries")), *_visible_text_queries(frame_analysis)], query_context)[:5]
    visual_queries = _korean_naver_queries([*_query_list(parsed.get("visual_queries")), *_visual_queries(frame_analysis)], query_context)[:5]
    category_queries = _korean_naver_queries([*_query_list(parsed.get("category_queries")), *_category_queries(frame_analysis)], query_context)[:5]

    if not isinstance(fallback_queries, list):
        fallback_queries = []

    fallback_queries = _korean_naver_queries(_query_list(fallback_queries), query_context)

    return CommerceQueryResponse(
        primary_query=primary_query,
        exact_text_queries=exact_queries,
        visual_queries=visual_queries,
        category_queries=category_queries,
        shopping_queries=_korean_naver_queries([
            *_query_list(parsed.get("shopping_queries")),
            primary_query,
            *exact_queries,
            *visual_queries,
            *category_queries,
        ], query_context)[:6],
        image_queries=_korean_naver_queries([
            *_query_list(parsed.get("image_queries")),
            *visual_queries,
            *exact_queries,
        ], query_context)[:6],
        blog_queries=_korean_naver_queries([
            *_query_list(parsed.get("blog_queries")),
            *_with_query_suffix(exact_queries, "후기"),
            *_with_query_suffix(visual_queries, "착용"),
        ], query_context)[:5],
        cafe_queries=_korean_naver_queries([
            *_query_list(parsed.get("cafe_queries")),
            *_with_query_suffix(exact_queries, "정보"),
            *_with_query_suffix(visual_queries, "후기"),
        ], query_context)[:5],
        web_queries=_korean_naver_queries([
            *_query_list(parsed.get("web_queries")),
            *exact_queries,
            *category_queries,
            primary_query,
        ], query_context)[:6],
        fallback_queries=fallback_queries[:5],
        normalized_brand=parsed.get("normalized_brand") or frame_analysis.brand,
        normalized_model=parsed.get("normalized_model") or frame_analysis.model_name,
        normalized_category=parsed.get("normalized_category") or frame_analysis.category_name,
        query_confidence=_clamp(parsed.get("query_confidence", frame_analysis.confidence)),
        reason=str(parsed.get("reason") or "Retry query generated after weak result quality.").strip(),
    )
