import json
import math
import re
from typing import Any, Callable, TypedDict
from urllib.parse import urlparse

from fastapi import HTTPException
from langgraph.graph import END, START, StateGraph

from app.core.config import settings
from app.schemas.analysis_graph_schema import (
    GoogleSearchResult,
    OcrAnalysisResult,
    ProductCandidate,
    ResultQuality,
    SearchIdentificationResult,
    ShoppingAnalysisRequest,
    ShoppingAnalysisResponse,
    VisualFeatureAnalysisResult,
)
from app.schemas.commerce_query_schema import CommerceQueryRequest, CommerceQueryResponse
from app.schemas.detection_schema import AnalyzeFrameResponse
from app.services.commerce_query_service import generate_commerce_query, _koreanize_search_query
from app.services.google_search_service import search_google_custom
from app.services.gms_openai_client import call_chat_completion, extract_json_object
from app.services.naver_shopping_service import search_naver_source
from app.services.split_frame_analysis_service import (
    analyze_ocr,
    analyze_visual_features,
    apply_identification_to_frame,
    identify_from_search,
    synthesize_initial_detection,
)
from app.utils.image_utils import is_valid_base64_image


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

NAVER_SEARCH_SOURCES = [
    "NAVER_SHOPPING",
    "NAVER_IMAGE",
    "NAVER_BLOG",
    "NAVER_CAFE",
    "NAVER_WEB",
]
TEXT_NEGATIVE_TERMS = ["카라", "폴로", "무지", "기본티", "레이어드"]
COLOR_MATCH_TERMS = ["주황", "오렌지", "orange"]
GRAPHIC_MATCH_TERMS = ["그래픽", "프린트", "레터링", "문구", "graphic", "print", "lettering"]
SPORTS_MATCH_TERMS = ["저지", "스포츠", "유니폼", "축구", "jersey", "sports", "uniform", "soccer", "football"]


class ShoppingAnalysisState(TypedDict, total=False):
    request: ShoppingAnalysisRequest
    ocr_analysis: OcrAnalysisResult
    visual_analysis: VisualFeatureAnalysisResult
    frame_analysis: AnalyzeFrameResponse
    query: CommerceQueryResponse
    active_queries: list[str]
    source_queries: dict[str, list[str]]
    tried_queries: list[str]
    source_counts: dict[str, int]
    google_search_results: list[GoogleSearchResult]
    google_source_counts: dict[str, int]
    search_identification: SearchIdentificationResult
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


def _ocr_analyzer_node(state: ShoppingAnalysisState) -> dict[str, Any]:
    request = state["request"]
    if not is_valid_base64_image(request.image_base64):
        raise HTTPException(
            status_code=400,
            detail="image_base64 must be a valid data:image base64 string",
        )
    return {"ocr_analysis": analyze_ocr(request)}


def _visual_feature_analyzer_node(state: ShoppingAnalysisState) -> dict[str, Any]:
    return {"visual_analysis": analyze_visual_features(state["request"])}


def _frame_synthesizer_node(state: ShoppingAnalysisState) -> dict[str, Any]:
    frame_analysis = synthesize_initial_detection(
        state["ocr_analysis"],
        state["visual_analysis"],
    )
    return {"frame_analysis": frame_analysis}


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


def _naver_search_node(state: ShoppingAnalysisState) -> dict[str, Any]:
    request = state["request"]
    source_queries = state.get("source_queries") or _query_candidates_by_source(state["query"], state["frame_analysis"])
    active_queries = _flatten_source_queries(source_queries)
    limit = request.max_candidates
    tried_queries = _unique([*(state.get("tried_queries") or []), *active_queries])
    active_sources = [source for source in NAVER_SEARCH_SOURCES if source_queries.get(source)]
    per_source_limit = max(3, math.ceil(limit / max(1, len(active_sources))))

    candidates_by_key: dict[str, ProductCandidate] = {}
    source_counts = {source: 0 for source in NAVER_SEARCH_SOURCES}
    for source in active_sources:
        queries = source_queries.get(source) or []
        per_query_display = max(2, min(settings.naver_shopping_display, math.ceil(per_source_limit / len(queries))))

        for query in queries:
            if source_counts[source] >= per_source_limit:
                break

            for candidate in search_naver_source(source, query, display=per_query_display):
                if source_counts[source] >= per_source_limit:
                    break

                enriched_candidate = _copy_candidate(
                    candidate,
                    product_type=candidate.product_type or source,
                    source_query=candidate.source_query or query,
                    query_type=candidate.query_type or source.replace("NAVER_", ""),
                )
                key = _candidate_key(enriched_candidate)
                if key in candidates_by_key:
                    continue

                candidates_by_key[key] = enriched_candidate
                source_counts[source] += 1

    candidates = list(candidates_by_key.values())[:limit]

    return {
        "search_candidates": candidates,
        "tried_queries": tried_queries,
        "source_counts": _source_counts(candidates, source_counts),
    }


def _google_search_node(state: ShoppingAnalysisState) -> dict[str, Any]:
    request = state["request"]
    queries = _google_query_candidates(state)
    if not queries:
        return {
            "google_search_results": [],
            "google_source_counts": {"GOOGLE_CUSTOM_SEARCH": 0},
        }

    limit = min(12, request.max_candidates)
    per_query_display = max(1, min(settings.google_custom_search_display, math.ceil(limit / len(queries))))
    results_by_key: dict[str, GoogleSearchResult] = {}

    for query in queries:
        if len(results_by_key) >= limit:
            break

        for result in search_google_custom(query, display=per_query_display):
            key = _google_result_key(result)
            if key not in results_by_key:
                results_by_key[key] = result
            if len(results_by_key) >= limit:
                break

    results = list(results_by_key.values())
    return {
        "google_search_results": results,
        "google_source_counts": {"GOOGLE_CUSTOM_SEARCH": len(results)},
    }


def _search_identifier_node(state: ShoppingAnalysisState) -> dict[str, Any]:
    identification = identify_from_search(
        state["frame_analysis"],
        state.get("ocr_analysis"),
        state.get("visual_analysis"),
        state.get("search_candidates") or [],
        state.get("google_search_results") or [],
    )
    refined_frame_analysis = apply_identification_to_frame(state["frame_analysis"], identification)
    return {
        "search_identification": identification,
        "frame_analysis": refined_frame_analysis,
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
        base_score = _text_similarity_score(frame_analysis, query, candidate)
        keyword_score, keyword_reasons = _keyword_relevance_score(frame_analysis, candidate)
        text_score = _clamp(base_score + keyword_score)
        strong_identity = _has_strong_identity(frame_analysis, candidate_text)

        if not target_is_accessory and _contains_any(candidate_text, ACCESSORY_HARD_TERMS) and text_score < 0.65:
            continue

        if (
            not target_is_accessory
            and _contains_any(candidate_text, ACCESSORY_SOFT_TERMS)
            and not strong_identity
            and text_score < 0.6
        ):
            continue

        if target_group and candidate_group and target_group != candidate_group and text_score < 0.5:
            continue

        if text_score < 0.28:
            continue

        filtered.append(_copy_candidate(
            candidate,
            text_score=text_score,
            filter_reason=", ".join(keyword_reasons) or "score-based text/category match",
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

    best_candidates = _merge_best_candidates(
        state.get("best_candidates") or [],
        reranked,
        limit=state["request"].max_candidates,
    )

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

    source_queries = _query_candidates_by_source(query, state["frame_analysis"])
    return {
        "query": query,
        "active_queries": _flatten_source_queries(source_queries),
        "source_queries": source_queries,
        "retry_count": retry_count,
    }


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
        message = "Detected product has enough high-confidence Naver search matches."
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


def _is_recommendable_product(candidate: ProductCandidate) -> bool:
    return candidate.product_type == "NAVER_SHOPPING" and bool(candidate.link)


def _build_graph():
    workflow = StateGraph(ShoppingAnalysisState)
    workflow.add_node("ocr_analyzer", _with_node_logging("ocr_analyzer", _ocr_analyzer_node))
    workflow.add_node("visual_feature_analyzer", _with_node_logging("visual_feature_analyzer", _visual_feature_analyzer_node))
    workflow.add_node("frame_synthesizer", _with_node_logging("frame_synthesizer", _frame_synthesizer_node))
    workflow.add_node("query_generator", _with_node_logging("query_generator", _query_generator_node))
    workflow.add_node("naver_search", _with_node_logging("naver_search", _naver_search_node))
    workflow.add_node("google_search", _with_node_logging("google_search", _google_search_node))
    workflow.add_node("search_identifier", _with_node_logging("search_identifier", _search_identifier_node))
    workflow.add_node("text_filter", _with_node_logging("text_filter", _text_filter_node))
    workflow.add_node("visual_reranker", _with_node_logging("visual_reranker", _visual_reranker_node))
    workflow.add_node("result_judge", _with_node_logging("result_judge", _result_judge_node))
    workflow.add_node("retry_query_generator", _with_node_logging("retry_query_generator", _retry_query_generator_node))
    workflow.add_node("final_formatter", _with_node_logging("final_formatter", _final_formatter_node))

    workflow.add_edge(START, "ocr_analyzer")
    workflow.add_edge("ocr_analyzer", "visual_feature_analyzer")
    workflow.add_edge("visual_feature_analyzer", "frame_synthesizer")
    workflow.add_edge("frame_synthesizer", "query_generator")
    workflow.add_edge("query_generator", "naver_search")
    workflow.add_edge("naver_search", "google_search")
    workflow.add_edge("google_search", "search_identifier")
    workflow.add_edge("search_identifier", "text_filter")
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
        *(query.exact_text_queries or []),
        *(query.visual_queries or []),
        *(query.category_queries or []),
        *(query.shopping_queries or []),
        *(query.image_queries or []),
        *(query.blog_queries or []),
        *(query.cafe_queries or []),
        *(query.web_queries or []),
        *(query.fallback_queries or []),
    ])


def _query_candidates_by_source(
    query: CommerceQueryResponse,
    frame_analysis: AnalyzeFrameResponse,
) -> dict[str, list[str]]:
    query_context = _commerce_request_from_frame(frame_analysis)
    primary = _korean_naver_queries([query.primary_query], query_context)
    exact = _korean_naver_queries([*(query.exact_text_queries or []), *_visible_text_queries(frame_analysis)], query_context)
    visual = _korean_naver_queries([*(query.visual_queries or []), *_visual_queries(frame_analysis)], query_context)
    category = _korean_naver_queries([*(query.category_queries or []), *_category_queries(frame_analysis)], query_context)

    return {
        "NAVER_SHOPPING": _korean_naver_queries([
            *primary,
            *(query.shopping_queries or []),
            *exact,
            *visual,
            *category,
            *(query.fallback_queries or []),
        ], query_context)[:8],
        "NAVER_IMAGE": _korean_naver_queries([
            *(query.image_queries or []),
            *visual,
            *exact,
        ], query_context)[:6],
        "NAVER_BLOG": _korean_naver_queries([
            *(query.blog_queries or []),
            *_with_query_suffix(exact, "후기"),
            *_with_query_suffix(visual, "착용"),
            *visual,
        ], query_context)[:5],
        "NAVER_CAFE": _korean_naver_queries([
            *(query.cafe_queries or []),
            *_with_query_suffix(exact, "정보"),
            *_with_query_suffix(visual, "후기"),
            *visual,
        ], query_context)[:5],
        "NAVER_WEB": _korean_naver_queries([
            *(query.web_queries or []),
            *exact,
            *category,
            *primary,
        ], query_context)[:6],
    }


def _korean_naver_queries(
    values: list[str | None],
    query_context: CommerceQueryRequest,
) -> list[str]:
    return _unique([
        _koreanize_search_query(value, query_context)
        for value in values
    ])


def _commerce_request_from_frame(frame_analysis: AnalyzeFrameResponse) -> CommerceQueryRequest:
    return CommerceQueryRequest(
        target_name=frame_analysis.target_name,
        category_name=frame_analysis.category_name,
        brand=frame_analysis.brand,
        model_name=frame_analysis.model_name,
        color=frame_analysis.color,
        shape=frame_analysis.shape,
        logo_text=frame_analysis.logo_text,
        key_features=frame_analysis.key_features or [],
        confidence=frame_analysis.confidence,
    )


def _flatten_source_queries(source_queries: dict[str, list[str]]) -> list[str]:
    queries: list[str] = []
    for source in NAVER_SEARCH_SOURCES:
        queries.extend(source_queries.get(source) or [])
    return _unique(queries)


def _google_query_candidates(state: ShoppingAnalysisState) -> list[str]:
    query = state["query"]
    frame_analysis = state["frame_analysis"]
    ocr = state.get("ocr_analysis")
    visual = state.get("visual_analysis")
    ocr_queries = []
    if ocr:
        product = _product_query_term(frame_analysis)
        ocr_queries = [
            _join_query(text, product)
            for text in ocr.visible_text_candidates[:4]
        ]

    return _unique([
        *(query.exact_text_queries or []),
        *(query.visual_queries or []),
        *(query.category_queries or []),
        *(query.web_queries or []),
        *ocr_queries,
        _join_query(visual.color if visual else None, visual.style if visual else None, visual.product_type if visual else None),
        query.primary_query,
    ])[:6]


def _google_result_key(result: GoogleSearchResult) -> str:
    return (result.link or f"{result.title}:{result.display_link or ''}").lower()


def _visible_text_queries(frame_analysis: AnalyzeFrameResponse) -> list[str]:
    variants = _visible_text_variants(frame_analysis.logo_text)
    product = _product_query_term(frame_analysis)
    return _unique([
        f"{variant} {product}"
        for variant in variants
        if variant and product
    ] + [
        f"\"{variant}\" {product}"
        for variant in variants
        if variant and product
    ])


def _visible_text_variants(value: str | None) -> list[str]:
    if not value:
        return []

    normalized = re.sub(r"\s+", " ", value).strip()
    clean = re.sub(r"[^0-9A-Za-z가-힣 ]+", " ", normalized)
    clean = re.sub(r"\s+", " ", clean).strip()
    compact = clean.replace(" ", "")
    tokens = [token for token in clean.split(" ") if len(token) >= 3]
    return _unique([normalized, clean, compact, *tokens])[:4]


def _visual_queries(frame_analysis: AnalyzeFrameResponse) -> list[str]:
    color = _color_query_term(frame_analysis)
    product = _product_query_term(frame_analysis)
    style = _style_query_term(frame_analysis)
    return _unique([
        _join_query(color, style, product),
        _join_query(color, "그래픽", product),
        _join_query(color, "프린트", product),
        _join_query(color, "레터링", product),
    ])


def _category_queries(frame_analysis: AnalyzeFrameResponse) -> list[str]:
    color = _color_query_term(frame_analysis)
    product = _product_query_term(frame_analysis)
    queries = [
        _join_query(frame_analysis.category_name, product, color),
        _join_query(product, color),
    ]
    if _looks_like_sports_item(frame_analysis):
        queries.extend([
            _join_query("스포츠 저지 반팔", color),
            _join_query("축구 유니폼", color),
        ])
    return _unique(queries)


def _english_queries(frame_analysis: AnalyzeFrameResponse) -> list[str]:
    haystack = _target_text_from_frame(frame_analysis).lower()
    color = "orange" if _contains_any(haystack, COLOR_MATCH_TERMS) else None
    style = "graphic" if _contains_any(haystack, GRAPHIC_MATCH_TERMS) else None
    product = "sports jersey" if _looks_like_sports_item(frame_analysis) else "t-shirt"
    return _unique([_join_query(color, style, product), frame_analysis.target_name])


def _with_query_suffix(queries: list[str], suffix: str) -> list[str]:
    return [f"{query} {suffix}" for query in queries if query]


def _join_query(*parts: str | None) -> str | None:
    joined = " ".join(str(part).strip() for part in parts if part and str(part).strip())
    return joined or None


def _product_query_term(frame_analysis: AnalyzeFrameResponse) -> str:
    haystack = _target_text_from_frame(frame_analysis).lower()
    if _contains_any(haystack, ["jersey", "저지", "유니폼"]):
        return "저지"
    if _contains_any(haystack, ["t-shirt", "tee", "shirt", "short sleeve", "반팔", "티셔츠"]):
        return "반팔티"
    return frame_analysis.category_name or frame_analysis.target_name or "상품"


def _color_query_term(frame_analysis: AnalyzeFrameResponse) -> str | None:
    haystack = _target_text_from_frame(frame_analysis).lower()
    if _contains_any(haystack, COLOR_MATCH_TERMS):
        return "주황색"
    if _contains_any(haystack, ["black", "검정", "블랙"]):
        return "검정색"
    if _contains_any(haystack, ["white", "흰색", "화이트"]):
        return "흰색"
    if _contains_any(haystack, ["red", "빨간", "레드"]):
        return "빨간색"
    return frame_analysis.color


def _style_query_term(frame_analysis: AnalyzeFrameResponse) -> str | None:
    haystack = _target_text_from_frame(frame_analysis).lower()
    if _contains_any(haystack, GRAPHIC_MATCH_TERMS):
        return "그래픽"
    return None


def _looks_like_sports_item(frame_analysis: AnalyzeFrameResponse) -> bool:
    return _contains_any(_target_text_from_frame(frame_analysis).lower(), SPORTS_MATCH_TERMS)


def _target_text_from_frame(frame_analysis: AnalyzeFrameResponse) -> str:
    return " ".join(str(part) for part in [
        frame_analysis.target_name,
        frame_analysis.category_name,
        frame_analysis.brand,
        frame_analysis.model_name,
        frame_analysis.color,
        frame_analysis.shape,
        frame_analysis.logo_text,
        " ".join(frame_analysis.key_features or []),
    ] if part)


def _source_counts(
    candidates: list[ProductCandidate],
    fallback_counts: dict[str, int] | None = None,
) -> dict[str, int]:
    counts = {source: 0 for source in NAVER_SEARCH_SOURCES}
    if fallback_counts:
        counts.update({source: 0 for source in fallback_counts})

    for candidate in candidates:
        source = candidate.product_type or "UNKNOWN"
        counts[source] = counts.get(source, 0) + 1

    return counts


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
        " ".join(query.exact_text_queries or []),
        " ".join(query.visual_queries or []),
        " ".join(query.category_queries or []),
        " ".join(query.shopping_queries or []),
        " ".join(query.image_queries or []),
        " ".join(query.blog_queries or []),
        " ".join(query.cafe_queries or []),
        " ".join(query.web_queries or []),
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
        candidate.snippet,
        candidate.source_query,
        candidate.query_type,
        candidate.product_type,
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


def _keyword_relevance_score(
    frame_analysis: AnalyzeFrameResponse,
    candidate: ProductCandidate,
) -> tuple[float, list[str]]:
    candidate_text = _candidate_text(candidate)
    target_text = _target_text_from_frame(frame_analysis).lower()
    reasons: list[str] = []
    points = 0

    if _contains_any(candidate_text, TEXT_NEGATIVE_TERMS):
        points -= 20
        reasons.append("negative apparel keyword penalty")

    if _contains_any(target_text, COLOR_MATCH_TERMS) and _contains_any(candidate_text, COLOR_MATCH_TERMS):
        points += 20
        reasons.append("color keyword matched")

    if _contains_any(target_text, GRAPHIC_MATCH_TERMS) and _contains_any(candidate_text, GRAPHIC_MATCH_TERMS):
        points += 20
        reasons.append("graphic/text keyword matched")

    if _contains_any(target_text, SPORTS_MATCH_TERMS) and _contains_any(candidate_text, SPORTS_MATCH_TERMS):
        points += 15
        reasons.append("sports/jersey keyword matched")

    if _visible_text_match(frame_analysis, candidate_text):
        points += 30
        reasons.append("visible text candidate matched")

    if candidate.image or candidate.thumbnail:
        points += 10
        reasons.append("image present")

    if candidate.product_type == "NAVER_SHOPPING":
        points += 5
        reasons.append("shopping source")
    elif candidate.product_type == "NAVER_IMAGE":
        points += 4
        reasons.append("image source")
    elif candidate.product_type in {"NAVER_BLOG", "NAVER_CAFE"}:
        points += 2
        reasons.append("community source")

    return points / 100.0, reasons


def _visible_text_match(frame_analysis: AnalyzeFrameResponse, candidate_text: str) -> bool:
    variants = _visible_text_variants(frame_analysis.logo_text)
    return any(variant.lower() in candidate_text for variant in variants if len(variant) >= 3)


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
    safe_image_urls = [
        _safe_candidate_image_url(candidate)
        for candidate in candidates_to_score
    ]
    metadata = [
        {
            "candidate_id": candidate_id,
            "title": candidate.title,
            "source": candidate.product_type,
            "snippet": candidate.snippet,
            "brand": candidate.brand,
            "maker": candidate.maker,
            "category": " > ".join(
                part
                for part in [candidate.category1, candidate.category2, candidate.category3, candidate.category4]
                if part
            ),
            "text_score": candidate.text_score,
            "image_attached": bool(image_url),
        }
        for candidate_id, candidate, image_url in zip(candidate_ids, candidates_to_score, safe_image_urls)
    ]

    content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                "Compare the reference YouTube capture with each search candidate image. "
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

    skipped_image_count = 0
    for candidate_id, candidate, image_url in zip(candidate_ids, candidates_to_score, safe_image_urls):
        content.append({
            "type": "text",
            "text": f"Candidate {candidate_id}: {candidate.title}",
        })
        if image_url:
            content.append({
                "type": "image_url",
                "image_url": {"url": image_url},
            })
        elif candidate.image or candidate.thumbnail:
            skipped_image_count += 1

    if skipped_image_count:
        _print_graph_debug("visual_reranker.image_filter", {
            "skipped_candidate_image_count": skipped_image_count,
            "reason": "candidate image URL was not safe for GMS/OpenAI image_url input",
        })

    messages = _visual_rerank_messages(content)
    try:
        raw_content = call_chat_completion(
            messages,
            model=settings.gms_openai_model,
            temperature=0.0,
        )
    except HTTPException as exc:
        if not _is_invalid_candidate_image_error(exc):
            raise

        _print_graph_debug("visual_reranker.image_retry", {
            "reason": "GMS/OpenAI rejected at least one candidate image URL; retrying without candidate images",
            "detail": exc.detail,
        })
        raw_content = call_chat_completion(
            _visual_rerank_messages(_without_candidate_images(content, request.image_base64)),
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


def _visual_rerank_messages(content: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "role": "developer",
            "content": (
                "You are a visual product reranker for Naver search results. "
                "Use the reference image and available candidate thumbnails to score similarity from 0.0 to 1.0. "
                "If a candidate image is not attached, estimate conservatively from text metadata. "
                "Return JSON only."
            ),
        },
        {
            "role": "user",
            "content": content,
        },
    ]


def _safe_candidate_image_url(candidate: ProductCandidate) -> str | None:
    for url in [candidate.image, candidate.thumbnail]:
        if _is_safe_image_url(url):
            return url
    return None


def _is_safe_image_url(url: str | None) -> bool:
    if not url:
        return False

    normalized = url.strip()
    if normalized.startswith("data:image/"):
        return True

    parsed = urlparse(normalized)
    if parsed.scheme.lower() != "https":
        return False

    return bool(parsed.netloc)


def _is_invalid_candidate_image_error(exc: HTTPException) -> bool:
    detail = str(exc.detail or exc)
    return "invalid_image_url" in detail or "Error while downloading" in detail


def _without_candidate_images(
    content: list[dict[str, Any]],
    reference_image_url: str,
) -> list[dict[str, Any]]:
    return [
        item
        for item in content
        if item.get("type") != "image_url"
        or (item.get("image_url") or {}).get("url") == reference_image_url
    ]


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
                    "Judge these Naver search candidates for the detected product.\n"
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
                    "You are a source-specific Naver retry query generator. "
                    "Generate better Shopping/Image/Blog/Cafe/Web queries when the previous result set was weak. "
                    "Return JSON only."
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
                    "{\"primary_query\": string, \"exact_text_queries\": string[], "
                    "\"visual_queries\": string[], \"category_queries\": string[], "
                    "\"shopping_queries\": string[], \"image_queries\": string[], "
                    "\"blog_queries\": string[], \"cafe_queries\": string[], "
                    "\"web_queries\": string[], \"fallback_queries\": string[], "
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


def _merge_best_candidates(
    existing: list[ProductCandidate],
    new_candidates: list[ProductCandidate],
    *,
    limit: int = 30,
) -> list[ProductCandidate]:
    by_key = {_candidate_key(candidate): candidate for candidate in existing}

    for candidate in new_candidates:
        key = _candidate_key(candidate)
        previous = by_key.get(key)
        if previous is None or candidate.final_score > previous.final_score:
            by_key[key] = candidate

    return sorted(by_key.values(), key=lambda item: item.final_score, reverse=True)[:limit]


def _query_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    return [
        str(item).strip()
        for item in value
        if item and str(item).strip()
    ]


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
            "google_search_results",
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
