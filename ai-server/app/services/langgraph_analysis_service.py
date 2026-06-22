import json
import math
import re
from typing import Any, Callable, TypedDict

from fastapi import HTTPException
from langgraph.graph import END, START, StateGraph

from app.core.config import settings
from app.schemas.analysis_graph_schema import (
    ProductCandidate,
    ResultQuality,
    ShoppingAnalysisRequest,
    ShoppingAnalysisResponse,
)
from app.schemas.commerce_query_schema import CommerceQueryRequest, CommerceQueryResponse
from app.schemas.detection_schema import AnalyzeFrameResponse
from app.services.commerce_query_service import generate_commerce_query
from app.services.detection_service import analyze_frame
from app.services.gms_openai_client import call_chat_completion, extract_json_object
from app.services.naver_shopping_service import search_naver_shopping


ACCESSORY_HARD_TERMS = [
    "보호필름",
    "강화유리",
    "액정보호",
    "파우치",
    "키링",
    "스트랩",
    "스티커",
    "스킨",
    "거치대",
    "홀더",
    "필름",
    "pouch",
    "film",
    "protector",
    "strap",
    "sticker",
    "holder",
]
ACCESSORY_SOFT_TERMS = ["케이스", "커버", "case", "cover"]
ACCESSORY_TARGET_TERMS = ACCESSORY_HARD_TERMS + ACCESSORY_SOFT_TERMS

CATEGORY_GROUPS = {
    "electronics": [
        "전자",
        "디지털",
        "가전",
        "이어폰",
        "헤드폰",
        "헤드셋",
        "스마트폰",
        "노트북",
        "태블릿",
        "카메라",
        "음향",
        "충전",
        "airpods",
        "headphone",
        "earbuds",
        "laptop",
        "phone",
        "camera",
    ],
    "fashion": [
        "패션",
        "의류",
        "신발",
        "운동화",
        "스니커즈",
        "가방",
        "잡화",
        "모자",
        "지갑",
        "시계",
        "sneakers",
        "shoes",
        "bag",
        "watch",
        "wallet",
    ],
    "beauty": [
        "뷰티",
        "화장품",
        "향수",
        "스킨케어",
        "메이크업",
        "립스틱",
        "쿠션",
        "cosmetics",
        "perfume",
    ],
    "home": [
        "가구",
        "인테리어",
        "생활",
        "주방",
        "침구",
        "조명",
        "의자",
        "테이블",
        "furniture",
        "kitchen",
        "chair",
        "table",
    ],
}


class ShoppingAnalysisState(TypedDict, total=False):
    request: ShoppingAnalysisRequest
    frame_analysis: AnalyzeFrameResponse
    query: CommerceQueryResponse
    active_queries: list[str]
    tried_queries: list[str]
    search_candidates: list[ProductCandidate]
    filtered_candidates: list[ProductCandidate]
    reranked_candidates: list[ProductCandidate]
    best_candidates: list[ProductCandidate]
    quality: ResultQuality
    retry_count: int
    response: ShoppingAnalysisResponse


def analyze_shopping(request: ShoppingAnalysisRequest) -> ShoppingAnalysisResponse:
    initial_state: ShoppingAnalysisState = {
        "request": request,
        "retry_count": 0,
        "tried_queries": [],
        "best_candidates": [],
    }
    _print_graph_debug("START", {"request": request})
    try:
        result = _analysis_graph.invoke(initial_state)
        response = result["response"]
        _print_graph_debug("END", {"response": response})
        return response
    except Exception as exc:
        _print_graph_error("FAILED", exc)
        raise


def _frame_analyzer_node(state: ShoppingAnalysisState) -> dict[str, Any]:
    request = state["request"]
    return {"frame_analysis": analyze_frame(request)}


def _query_generator_node(state: ShoppingAnalysisState) -> dict[str, Any]:
    request = state["request"]
    frame_analysis = state["frame_analysis"]
    commerce_request = _to_commerce_request(request, frame_analysis)
    query = generate_commerce_query(commerce_request)

    return {
        "query": query,
        "active_queries": _query_candidates(query),
    }


def _naver_search_node(state: ShoppingAnalysisState) -> dict[str, Any]:
    request = state["request"]
    active_queries = state.get("active_queries") or _query_candidates(state["query"])
    limit = request.max_candidates
    per_query_display = max(5, min(settings.naver_shopping_display, math.ceil(limit / len(active_queries))))
    tried_queries = _unique([*(state.get("tried_queries") or []), *active_queries])

    candidates_by_key: dict[str, ProductCandidate] = {}
    for query in active_queries:
        if len(candidates_by_key) >= limit:
            break

        for candidate in search_naver_shopping(query, display=per_query_display):
            key = _candidate_key(candidate)
            if key not in candidates_by_key:
                candidates_by_key[key] = candidate

            if len(candidates_by_key) >= limit:
                break

    return {
        "search_candidates": list(candidates_by_key.values()),
        "tried_queries": tried_queries,
    }


def _text_filter_node(state: ShoppingAnalysisState) -> dict[str, Any]:
    frame_analysis = state["frame_analysis"]
    query = state["query"]
    target_text = _target_text(frame_analysis, query)
    target_is_accessory = _contains_any(target_text, ACCESSORY_TARGET_TERMS)
    target_group = _infer_category_group(target_text)

    filtered: list[ProductCandidate] = []
    for candidate in state.get("search_candidates") or []:
        candidate_text = _candidate_text(candidate)
        candidate_group = _infer_category_group(candidate_text)
        text_score = _text_similarity_score(frame_analysis, query, candidate)
        strong_identity = _has_strong_identity(frame_analysis, candidate_text)

        if not target_is_accessory and _contains_any(candidate_text, ACCESSORY_HARD_TERMS):
            continue

        if (
            not target_is_accessory
            and _contains_any(candidate_text, ACCESSORY_SOFT_TERMS)
            and not strong_identity
            and text_score < 0.7
        ):
            continue

        if target_group and candidate_group and target_group != candidate_group and text_score < 0.55:
            continue

        filtered.append(_copy_candidate(
            candidate,
            text_score=text_score,
            filter_reason="title/category matched target product",
        ))

    return {
        "filtered_candidates": sorted(filtered, key=lambda item: item.text_score, reverse=True),
    }


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

    best_candidates = _merge_best_candidates(state.get("best_candidates") or [], reranked)

    return {
        "reranked_candidates": reranked,
        "best_candidates": best_candidates,
    }


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


def _retry_query_generator_node(state: ShoppingAnalysisState) -> dict[str, Any]:
    provider = settings.ai_commerce_query_provider.lower()
    retry_count = state.get("retry_count", 0) + 1

    if provider == "gpt":
        query = _gpt_retry_query(state)
    elif provider == "mock":
        query = _fallback_retry_query(state)
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Unsupported AI_COMMERCE_QUERY_PROVIDER: {settings.ai_commerce_query_provider}",
        )

    return {
        "query": query,
        "active_queries": _query_candidates(query),
        "retry_count": retry_count,
    }


def _final_formatter_node(state: ShoppingAnalysisState) -> dict[str, Any]:
    best_candidates = state.get("best_candidates") or []
    selected = [
        candidate
        for candidate in best_candidates
        if candidate.final_score >= 0.55 or candidate.visual_score >= 0.55
    ][:5]

    if not selected:
        selected = best_candidates[:5]

    response = ShoppingAnalysisResponse(
        frame_analysis=state["frame_analysis"],
        query=state["query"],
        selected_products=selected,
        searched_products_count=len(state.get("search_candidates") or []),
        filtered_products_count=len(state.get("filtered_candidates") or []),
        quality=state["quality"],
        retry_count=state.get("retry_count", 0),
        tried_queries=state.get("tried_queries") or [],
    )

    return {"response": response}


def _route_after_judge(state: ShoppingAnalysisState) -> str:
    quality = state["quality"]
    max_retries = state["request"].max_retries

    if quality.is_good or state.get("retry_count", 0) >= max_retries:
        next_node = "final_formatter"
    else:
        next_node = "retry_query_generator"

    _print_graph_debug("result_judge.route", {
        "next_node": next_node,
        "is_good": quality.is_good,
        "retry_count": state.get("retry_count", 0),
        "max_retries": max_retries,
        "quality": quality,
    })
    return next_node


def _build_graph():
    workflow = StateGraph(ShoppingAnalysisState)
    workflow.add_node("frame_analyzer", _with_node_logging("frame_analyzer", _frame_analyzer_node))
    workflow.add_node("query_generator", _with_node_logging("query_generator", _query_generator_node))
    workflow.add_node("naver_search", _with_node_logging("naver_search", _naver_search_node))
    workflow.add_node("text_filter", _with_node_logging("text_filter", _text_filter_node))
    workflow.add_node("visual_reranker", _with_node_logging("visual_reranker", _visual_reranker_node))
    workflow.add_node("result_judge", _with_node_logging("result_judge", _result_judge_node))
    workflow.add_node("retry_query_generator", _with_node_logging("retry_query_generator", _retry_query_generator_node))
    workflow.add_node("final_formatter", _with_node_logging("final_formatter", _final_formatter_node))

    workflow.add_edge(START, "frame_analyzer")
    workflow.add_edge("frame_analyzer", "query_generator")
    workflow.add_edge("query_generator", "naver_search")
    workflow.add_edge("naver_search", "text_filter")
    workflow.add_edge("text_filter", "visual_reranker")
    workflow.add_edge("visual_reranker", "result_judge")
    workflow.add_conditional_edges(
        "result_judge",
        _route_after_judge,
        {
            "final_formatter": "final_formatter",
            "retry_query_generator": "retry_query_generator",
        },
    )
    workflow.add_edge("retry_query_generator", "naver_search")
    workflow.add_edge("final_formatter", END)

    return workflow.compile()


def _with_node_logging(
    node_name: str,
    node_func: Callable[[ShoppingAnalysisState], dict[str, Any]],
) -> Callable[[ShoppingAnalysisState], dict[str, Any]]:
    def wrapped_node(state: ShoppingAnalysisState) -> dict[str, Any]:
        try:
            result = node_func(state)
            _print_graph_debug(node_name, result)
            return result
        except Exception as exc:
            _print_graph_error(node_name, exc)
            raise

    return wrapped_node


def _to_commerce_request(
    request: ShoppingAnalysisRequest,
    frame_analysis: AnalyzeFrameResponse,
) -> CommerceQueryRequest:
    return CommerceQueryRequest(
        target_name=frame_analysis.target_name,
        category_name=frame_analysis.category_name,
        brand=frame_analysis.brand,
        model_name=frame_analysis.model_name,
        color=frame_analysis.color,
        shape=frame_analysis.shape,
        logo_text=frame_analysis.logo_text,
        key_features=frame_analysis.key_features,
        confidence=frame_analysis.confidence,
        subtitle_text=request.subtitle_text,
        video_id=request.video_id,
        timestamp_sec=request.timestamp_sec,
    )


def _query_candidates(query: CommerceQueryResponse) -> list[str]:
    return _unique([
        query.primary_query,
        *(query.fallback_queries or []),
    ])


def _candidate_key(candidate: ProductCandidate) -> str:
    return (
        candidate.external_product_id
        or candidate.product_id
        or candidate.link
        or f"{candidate.title}:{candidate.mall_name or ''}"
    ).lower()


def _target_text(frame_analysis: AnalyzeFrameResponse, query: CommerceQueryResponse) -> str:
    return " ".join(str(part) for part in [
        frame_analysis.target_name,
        frame_analysis.category_name,
        frame_analysis.brand,
        frame_analysis.model_name,
        frame_analysis.color,
        frame_analysis.shape,
        frame_analysis.logo_text,
        " ".join(frame_analysis.key_features or []),
        query.primary_query,
        " ".join(query.fallback_queries or []),
    ] if part)


def _candidate_text(candidate: ProductCandidate) -> str:
    return " ".join(str(part) for part in [
        candidate.title,
        candidate.brand,
        candidate.maker,
        candidate.category1,
        candidate.category2,
        candidate.category3,
        candidate.category4,
    ] if part).lower()


def _text_similarity_score(
    frame_analysis: AnalyzeFrameResponse,
    query: CommerceQueryResponse,
    candidate: ProductCandidate,
) -> float:
    target_text = _target_text(frame_analysis, query).lower()
    candidate_text = _candidate_text(candidate)
    target_tokens = set(_tokens(target_text))
    candidate_tokens = set(_tokens(candidate_text))

    score = 0.15
    if target_tokens:
        score += 0.25 * (len(target_tokens & candidate_tokens) / len(target_tokens))

    if frame_analysis.brand and frame_analysis.brand.lower() in candidate_text:
        score += 0.2

    if frame_analysis.model_name:
        model_tokens = set(_tokens(frame_analysis.model_name.lower()))
        if model_tokens and model_tokens <= candidate_tokens:
            score += 0.25
        elif model_tokens & candidate_tokens:
            score += 0.15

    if frame_analysis.color and frame_analysis.color.lower() in candidate_text:
        score += 0.05

    target_category_group = _infer_category_group(frame_analysis.category_name)
    if target_category_group and target_category_group == _infer_category_group(candidate_text):
        score += 0.1

    if query.normalized_category and query.normalized_category.lower() in candidate_text:
        score += 0.05

    return _clamp(score)


def _has_strong_identity(frame_analysis: AnalyzeFrameResponse, candidate_text: str) -> bool:
    if frame_analysis.model_name:
        model_tokens = set(_tokens(frame_analysis.model_name.lower()))
        if model_tokens and model_tokens <= set(_tokens(candidate_text)):
            return True

    return bool(frame_analysis.brand and frame_analysis.brand.lower() in candidate_text)


def _fallback_visual_rerank(candidates: list[ProductCandidate]) -> list[ProductCandidate]:
    reranked = [
        _copy_candidate(
            candidate,
            visual_score=candidate.text_score,
            final_score=candidate.text_score,
            visual_reason="mock visual score copied from text/category score",
        )
        for candidate in candidates
    ]
    return sorted(reranked, key=lambda item: item.final_score, reverse=True)


def _gpt_visual_rerank(
    request: ShoppingAnalysisRequest,
    frame_analysis: AnalyzeFrameResponse,
    candidates: list[ProductCandidate],
) -> list[ProductCandidate]:
    candidates_to_score = candidates[:12]
    candidate_ids = [_candidate_prompt_id(index, candidate) for index, candidate in enumerate(candidates_to_score)]
    metadata = [
        {
            "candidate_id": candidate_id,
            "title": candidate.title,
            "brand": candidate.brand,
            "maker": candidate.maker,
            "category": " > ".join(
                part
                for part in [candidate.category1, candidate.category2, candidate.category3, candidate.category4]
                if part
            ),
            "text_score": candidate.text_score,
        }
        for candidate_id, candidate in zip(candidate_ids, candidates_to_score)
    ]

    content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                "Compare the reference YouTube capture with each shopping candidate thumbnail. "
                "Score visual similarity only for the actual product, ignoring cases, pouches, "
                "screen protectors, and unrelated accessories. Return only valid JSON.\n\n"
                f"Detected product: {_model_to_dict(frame_analysis)}\n"
                f"Candidates: {metadata}\n\n"
                "Return JSON: {\"scores\":[{\"candidate_id\":\"...\",\"visual_score\":0.0,\"reason\":\"...\"}]}"
            ),
        },
        {
            "type": "image_url",
            "image_url": {"url": request.image_base64},
        },
    ]

    for candidate_id, candidate in zip(candidate_ids, candidates_to_score):
        content.append({
            "type": "text",
            "text": f"Candidate {candidate_id}: {candidate.title}",
        })
        if candidate.image:
            content.append({
                "type": "image_url",
                "image_url": {"url": candidate.image},
            })

    raw_content = call_chat_completion(
        [
            {
                "role": "developer",
                "content": (
                    "You are a visual product reranker for Naver Shopping results. "
                    "Use the reference image and candidate thumbnails to score similarity from 0.0 to 1.0. "
                    "Return JSON only."
                ),
            },
            {
                "role": "user",
                "content": content,
            },
        ],
        model=settings.gms_openai_model,
        temperature=0.0,
    )
    parsed = extract_json_object(raw_content)
    _print_graph_debug("visual_reranker.ai_response", {
        "raw_content": raw_content,
        "parsed": parsed,
    })
    scores_by_id = _parse_visual_scores(parsed)

    reranked: list[ProductCandidate] = []
    for candidate_id, candidate in zip(candidate_ids, candidates_to_score):
        score_data = scores_by_id.get(candidate_id, {})
        visual_score = _clamp(score_data.get("visual_score", candidate.text_score * 0.8))
        final_score = _clamp((visual_score * 0.7) + (candidate.text_score * 0.3))
        reranked.append(_copy_candidate(
            candidate,
            visual_score=visual_score,
            final_score=final_score,
            visual_reason=score_data.get("reason") or "AI visual reranker score",
        ))

    for candidate in candidates[12:]:
        final_score = _clamp(candidate.text_score * 0.75)
        reranked.append(_copy_candidate(
            candidate,
            visual_score=final_score,
            final_score=final_score,
            visual_reason="not sent to AI reranker; estimated from text/category score",
        ))

    return sorted(reranked, key=lambda item: item.final_score, reverse=True)


def _parse_visual_scores(parsed: dict[str, Any]) -> dict[str, dict[str, Any]]:
    scores = parsed.get("scores") or []
    if not isinstance(scores, list):
        raise HTTPException(
            status_code=502,
            detail="Visual reranker response must include a scores list",
        )

    scores_by_id: dict[str, dict[str, Any]] = {}
    for item in scores:
        if not isinstance(item, dict):
            continue

        candidate_id = str(item.get("candidate_id") or "").strip()
        if not candidate_id:
            continue

        scores_by_id[candidate_id] = {
            "visual_score": item.get("visual_score"),
            "reason": item.get("reason"),
        }

    return scores_by_id


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
        [
            {
                "role": "developer",
                "content": (
                    "You are a product search result quality judge. "
                    "Decide whether the current result set is good enough. Return JSON only."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Judge these Naver Shopping candidates for the detected product.\n"
                    "Good means at least 3 candidates are visually/textually similar enough "
                    "and the scores are not weak.\n\n"
                    f"Detected product: {_model_to_dict(state['frame_analysis'])}\n"
                    f"Query: {_model_to_dict(state['query'])}\n"
                    f"Candidates: {[_model_to_dict(candidate) for candidate in candidates[:8]]}\n\n"
                    "Return JSON with exactly these keys: "
                    "{\"is_good\": boolean, \"score\": number, "
                    "\"enough_similar_count\": number, \"reason\": string}"
                ),
            },
        ],
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


def _gpt_retry_query(state: ShoppingAnalysisState) -> CommerceQueryResponse:
    raw_content = call_chat_completion(
        [
            {
                "role": "developer",
                "content": (
                    "You are a Naver Shopping retry query generator. "
                    "Generate a better query when the previous result set was weak. Return JSON only."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Create a new search query for the same detected product.\n"
                    "Avoid queries that were already tried. Avoid accessory-focused terms unless "
                    "the target product itself is an accessory.\n\n"
                    f"Detected product: {_model_to_dict(state['frame_analysis'])}\n"
                    f"Previous query: {_model_to_dict(state['query'])}\n"
                    f"Tried queries: {state.get('tried_queries') or []}\n"
                    f"Quality judgement: {_model_to_dict(state['quality'])}\n"
                    f"Top candidates: {[_model_to_dict(candidate) for candidate in (state.get('best_candidates') or [])[:5]]}\n\n"
                    "Return JSON with exactly these keys: "
                    "{\"primary_query\": string, \"fallback_queries\": string[], "
                    "\"normalized_brand\": string | null, \"normalized_model\": string | null, "
                    "\"normalized_category\": string | null, \"query_confidence\": number, \"reason\": string}"
                ),
            },
        ],
        model=settings.gms_openai_query_model,
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
    tried_queries = set(query.lower() for query in state.get("tried_queries") or [])
    candidates = _unique([
        " ".join(part for part in [frame_analysis.brand, frame_analysis.model_name] if part),
        " ".join(part for part in [frame_analysis.brand, frame_analysis.target_name] if part),
        " ".join(part for part in [frame_analysis.color, frame_analysis.shape, frame_analysis.category_name] if part),
        " ".join(part for part in [frame_analysis.target_name, "정품"] if part),
        frame_analysis.category_name,
    ])
    fresh_candidates = [query for query in candidates if query and query.lower() not in tried_queries]

    primary_query = fresh_candidates[0] if fresh_candidates else f"{frame_analysis.target_name} 상품"
    fallback_queries = fresh_candidates[1:5]

    return CommerceQueryResponse(
        primary_query=primary_query,
        fallback_queries=fallback_queries,
        normalized_brand=frame_analysis.brand,
        normalized_model=frame_analysis.model_name,
        normalized_category=frame_analysis.category_name,
        query_confidence=_clamp(frame_analysis.confidence * 0.9),
        reason="Previous result quality was low, so a broader mock retry query was generated.",
    )


def _normalize_query_response(parsed: dict[str, Any], state: ShoppingAnalysisState) -> CommerceQueryResponse:
    frame_analysis = state["frame_analysis"]
    primary_query = str(parsed.get("primary_query") or frame_analysis.target_name or "상품").strip()
    fallback_queries = parsed.get("fallback_queries") or []

    if not isinstance(fallback_queries, list):
        fallback_queries = []

    fallback_queries = [
        str(query).strip()
        for query in fallback_queries
        if query and str(query).strip()
    ]

    return CommerceQueryResponse(
        primary_query=primary_query,
        fallback_queries=fallback_queries[:5],
        normalized_brand=parsed.get("normalized_brand") or frame_analysis.brand,
        normalized_model=parsed.get("normalized_model") or frame_analysis.model_name,
        normalized_category=parsed.get("normalized_category") or frame_analysis.category_name,
        query_confidence=_clamp(parsed.get("query_confidence", frame_analysis.confidence)),
        reason=str(parsed.get("reason") or "Retry query generated after weak result quality.").strip(),
    )


def _merge_best_candidates(
    existing: list[ProductCandidate],
    new_candidates: list[ProductCandidate],
) -> list[ProductCandidate]:
    by_key = {_candidate_key(candidate): candidate for candidate in existing}

    for candidate in new_candidates:
        key = _candidate_key(candidate)
        previous = by_key.get(key)
        if previous is None or candidate.final_score > previous.final_score:
            by_key[key] = candidate

    return sorted(by_key.values(), key=lambda item: item.final_score, reverse=True)


def _infer_category_group(text: str | None) -> str | None:
    if not text:
        return None

    normalized = text.lower()
    for group, keywords in CATEGORY_GROUPS.items():
        if any(keyword.lower() in normalized for keyword in keywords):
            return group

    return None


def _contains_any(text: str | None, terms: list[str]) -> bool:
    if not text:
        return False

    normalized = text.lower()
    return any(term.lower() in normalized for term in terms)


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+|[가-힣]+", text.lower())


def _candidate_prompt_id(index: int, candidate: ProductCandidate) -> str:
    return candidate.product_id or f"candidate-{index + 1}"


def _copy_candidate(candidate: ProductCandidate, **updates: Any) -> ProductCandidate:
    if hasattr(candidate, "model_copy"):
        return candidate.model_copy(update=updates)

    return candidate.copy(update=updates)


def _print_graph_debug(node_name: str, payload: dict[str, Any]) -> None:
    try:
        print(
            f"\n[SyncShopper LangGraph] {node_name} returned\n"
            + json.dumps(_debug_value(payload), ensure_ascii=False, indent=2),
            flush=True,
        )
    except Exception as exc:
        print(
            f"\n[SyncShopper LangGraph] {node_name} returned "
            f"(debug serialization failed: {exc})\n{payload}",
            flush=True,
        )


def _print_graph_error(node_name: str, exc: Exception) -> None:
    payload: dict[str, Any] = {
        "error_type": exc.__class__.__name__,
        "message": str(exc),
    }

    if isinstance(exc, HTTPException):
        payload.update({
            "status_code": exc.status_code,
            "detail": exc.detail,
        })

    print(
        f"\n[SyncShopper LangGraph] {node_name} failed\n"
        + json.dumps(_debug_value(payload), ensure_ascii=False, indent=2),
        flush=True,
    )


def _debug_value(value: Any, *, key: str | None = None) -> Any:
    if key:
        normalized_key = key.lower()

        if "api_key" in normalized_key or "secret" in normalized_key:
            return "<redacted>"

        if normalized_key == "image_base64":
            return f"<base64 image chars={len(value or '')}>"

        if normalized_key in {
            "search_candidates",
            "filtered_candidates",
            "reranked_candidates",
            "best_candidates",
            "selected_products",
        } and isinstance(value, list):
            return _debug_candidate_titles(value)

    if hasattr(value, "model_dump"):
        return _debug_value(value.model_dump())

    if hasattr(value, "dict"):
        return _debug_value(value.dict())

    if isinstance(value, dict):
        return {
            str(item_key): _debug_value(item_value, key=str(item_key))
            for item_key, item_value in value.items()
        }

    if isinstance(value, list):
        max_items = 12
        items = [_debug_value(item) for item in value[:max_items]]
        if len(value) <= max_items:
            return items

        return {
            "count": len(value),
            "items": items,
            "truncated_count": len(value) - max_items,
        }

    if isinstance(value, str):
        return _truncate_for_debug(value)

    if isinstance(value, (int, float, bool)) or value is None:
        return value

    return str(value)


def _debug_candidate_titles(candidates: list[Any]) -> dict[str, Any]:
    titles: list[str] = []

    for candidate in candidates:
        if isinstance(candidate, dict):
            title = candidate.get("title")
        else:
            title = getattr(candidate, "title", None)

        if title:
            titles.append(_truncate_for_debug(str(title), max_length=200))

    return {
        "count": len(candidates),
        "titles": titles,
    }


def _truncate_for_debug(value: str, max_length: int = 1000) -> str:
    if len(value) <= max_length:
        return value

    return f"{value[:max_length]}...<truncated chars={len(value) - max_length}>"


def _model_to_dict(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()

    if hasattr(model, "dict"):
        return model.dict()

    return dict(model)


def _unique(values: list[str | None]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        if not value:
            continue

        normalized = str(value).strip()
        key = normalized.lower()
        if normalized and key not in seen:
            result.append(normalized)
            seen.add(key)

    return result


def _clamp(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0

    return max(0.0, min(number, 1.0))


_analysis_graph = _build_graph()
