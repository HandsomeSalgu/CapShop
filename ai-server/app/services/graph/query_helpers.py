import re
from typing import Any

from app.schemas.analysis_graph_schema import ShoppingAnalysisRequest
from app.schemas.commerce_query_schema import CommerceQueryRequest, CommerceQueryResponse
from app.schemas.detection_schema import AnalyzeFrameResponse
from app.services.commerce_query_service import _koreanize_search_query
from app.services.graph.candidate_utils import _unique
from app.services.graph.state import ShoppingAnalysisState
from app.services.scoring.category_rules import (
    COLOR_MATCH_TERMS,
    GRAPHIC_MATCH_TERMS,
    NAVER_SEARCH_SOURCES,
    SPORTS_MATCH_TERMS,
    _contains_any,
)


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

def _query_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    return [
        str(item).strip()
        for item in value
        if item and str(item).strip()
    ]
