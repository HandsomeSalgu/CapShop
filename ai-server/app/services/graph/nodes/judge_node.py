import re
from typing import Any

from fastapi import HTTPException

from app.core.config import settings
from app.schemas.analysis_graph_schema import (
    ProductCandidate,
    ResultQuality,
    SearchIdentificationResult,
    ShoppingAnalysisResponse,
)
from app.schemas.detection_schema import AnalyzeFrameResponse
from app.services.gemini_client import call_chat_completion, extract_json_object
from app.services.graph.candidate_utils import _is_recommendable_product
from app.services.graph.debug import _model_to_dict, _print_graph_debug
from app.services.graph.state import ShoppingAnalysisState
from app.services.prompts.judge_prompt import build_candidate_judge_messages
from app.services.scoring.category_rules import _clamp
from app.services.split_frame_analysis_service import apply_identification_to_frame


def _candidate_judge_node(state: ShoppingAnalysisState) -> dict[str, Any]:
    provider = settings.ai_result_judge_provider.lower()
    local_identification = _fallback_search_identification(state)
    local_quality = _fallback_result_judge(state)

    if provider == "mock":
        identification = local_identification
        quality = local_quality
    elif provider == "gemini":
        if not _should_call_gemini_candidate_judge(state, local_quality):
            _print_graph_debug("candidate_judge.local", {
                "reason": "Local candidate quality was decisive; Gemini judge skipped",
                "quality": local_quality,
            })
            identification = local_identification
            quality = local_quality
        else:
            try:
                identification, quality = _gemini_candidate_judge(state)
            except HTTPException as exc:
                if exc.status_code not in {502, 504}:
                    raise

                _print_graph_debug("candidate_judge.fallback", {
                    "reason": "Gemini candidate judge failed; using local fallback result",
                    "status_code": exc.status_code,
                    "detail": exc.detail,
                })
                identification = local_identification
                quality = local_quality
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Unsupported AI_RESULT_JUDGE_PROVIDER: {settings.ai_result_judge_provider}",
        )

    refined_frame_analysis = apply_identification_to_frame(state["frame_analysis"], identification)
    return {
        "search_identification": identification,
        "frame_analysis": refined_frame_analysis,
        "quality": quality,
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

def _fallback_result_judge(state: ShoppingAnalysisState) -> ResultQuality:
    frame_analysis = state["frame_analysis"]
    candidates = state.get("best_candidates") or []
    local_scores = [
        _local_candidate_match_score(frame_analysis, candidate)
        for candidate in candidates
    ]
    strong_count = sum(1 for score in local_scores if score >= 0.72)
    similar_count = sum(1 for score in local_scores if score >= 0.42)
    top_three_scores = local_scores[:3]
    average_top_score = (
        sum(top_three_scores) / len(top_three_scores)
        if top_three_scores
        else 0.0
    )
    is_good = strong_count >= 3 and average_top_score >= 0.68

    return ResultQuality(
        is_good=is_good,
        score=_clamp(average_top_score),
        enough_similar_count=similar_count,
        reason=(
            "Top candidates passed strict local brand/visual matching."
            if is_good
            else "Local judge did not find enough strict brand/visual matches."
        ),
    )


def _should_call_gemini_candidate_judge(
    state: ShoppingAnalysisState,
    local_quality: ResultQuality,
) -> bool:
    candidates = state.get("best_candidates") or []
    if not candidates:
        return False

    if local_quality.is_good and local_quality.score >= 0.72:
        return False

    if local_quality.score < 0.42 and local_quality.enough_similar_count == 0:
        return False

    return True


def _local_candidate_match_score(
    frame_analysis: AnalyzeFrameResponse,
    candidate: ProductCandidate,
) -> float:
    target_text = _join_text([
        frame_analysis.target_name,
        frame_analysis.category_name,
        frame_analysis.brand,
        frame_analysis.model_name,
        frame_analysis.color,
        frame_analysis.shape,
        " ".join(frame_analysis.key_features or []),
    ]).lower()
    candidate_text = _candidate_identity_text(candidate)
    score = 0.0

    brand_matched = bool(frame_analysis.brand and _contains_text(candidate_text, frame_analysis.brand))
    product_matched = _contains_any_text(candidate_text, _product_terms(target_text))
    color_matched = _contains_any_text(candidate_text, _color_terms(target_text))
    quilt_matched = _contains_any_text(candidate_text, _quilt_terms(target_text))
    detail_matched = _contains_any_text(candidate_text, _detail_terms(target_text))

    if brand_matched:
        score += 0.4
    if product_matched:
        score += 0.12
    if color_matched:
        score += 0.15
    if quilt_matched:
        score += 0.13
    if detail_matched:
        score += 0.1
    if candidate.image or candidate.thumbnail:
        score += 0.04
    if _is_recommendable_product(candidate):
        score += 0.06

    if frame_analysis.brand and not brand_matched:
        score = min(score, 0.58)
    if not product_matched:
        score = min(score, 0.5)

    return _clamp(score)


def _candidate_identity_text(candidate: ProductCandidate) -> str:
    return _join_text([
        candidate.title,
        candidate.brand,
        candidate.maker,
        candidate.mall_name,
        candidate.category1,
        candidate.category2,
        candidate.category3,
        candidate.category4,
        candidate.snippet,
        candidate.reason,
    ]).lower()


def _product_terms(target_text: str) -> list[str]:
    if _contains_any_text(target_text, ["jacket", "outerwear", "자켓", "재킷", "점퍼", "아우터"]):
        return ["jacket", "outerwear", "자켓", "재킷", "점퍼", "아우터"]
    return []


def _color_terms(target_text: str) -> list[str]:
    if _contains_any_text(target_text, ["olive green", "olive", "올리브", "올리브그린"]):
        return ["olive green", "olive", "올리브", "올리브그린"]
    if _contains_any_text(target_text, ["green", "그린", "초록"]):
        return ["green", "그린", "초록"]
    return []


def _quilt_terms(target_text: str) -> list[str]:
    if _contains_any_text(target_text, ["quilt", "quilted", "quilting", "퀼팅", "누빔", "diamond"]):
        return ["quilt", "quilted", "quilting", "퀼팅", "누빔", "diamond", "다이아몬드"]
    return []


def _detail_terms(target_text: str) -> list[str]:
    terms: list[str] = []
    if _contains_any_text(target_text, ["snap", "button", "스냅", "버튼"]):
        terms.extend(["snap", "button", "스냅", "버튼"])
    if _contains_any_text(target_text, ["v-neck", "v neck", "브이넥", "v넥", "collarless"]):
        terms.extend(["v-neck", "v neck", "브이넥", "v넥", "collarless"])
    return terms


def _contains_any_text(text: str, terms: list[str]) -> bool:
    return any(_contains_text(text, term) for term in terms)


def _contains_text(text: str, term: str | None) -> bool:
    if not term:
        return False

    normalized = text.lower()
    needle = str(term).lower().strip()
    if not needle:
        return False
    if re.search(r"[a-z0-9]", needle):
        pattern = r"(?<![a-z0-9])" + re.escape(needle) + r"(?![a-z0-9])"
        return bool(re.search(pattern, normalized))
    return needle in normalized


def _join_text(values: list[str | None]) -> str:
    return " ".join(str(value) for value in values if value)

def _fallback_search_identification(state: ShoppingAnalysisState) -> SearchIdentificationResult:
    frame_analysis = state["frame_analysis"]
    ocr = state.get("ocr_analysis")
    visual = state.get("visual_analysis")
    evidence = _unique_strings([
        *(candidate.title for candidate in (state.get("best_candidates") or [])[:3]),
        *(candidate.title for candidate in (state.get("search_candidates") or [])[:3]),
        *(result.title for result in (state.get("google_search_results") or [])[:3]),
    ])[:5]
    logo_text = frame_analysis.logo_text
    if not logo_text and ocr and ocr.visible_text_candidates:
        logo_text = ocr.visible_text_candidates[0]

    key_features = list(frame_analysis.key_features or [])
    if visual and visual.key_features:
        key_features = _unique_strings([*visual.key_features, *key_features])[:8]

    return SearchIdentificationResult(
        target_name=frame_analysis.target_name,
        category_name=frame_analysis.category_name,
        brand=frame_analysis.brand,
        model_name=frame_analysis.model_name,
        color=frame_analysis.color,
        shape=frame_analysis.shape,
        logo_text=logo_text,
        key_features=key_features,
        confidence=frame_analysis.confidence,
        evidence=evidence,
        reason="Fallback candidate judge used split OCR/visual analysis and search candidate titles.",
    )


def _gemini_candidate_judge(state: ShoppingAnalysisState) -> tuple[SearchIdentificationResult, ResultQuality]:
    frame_analysis = state["frame_analysis"]
    candidates = state.get("best_candidates") or state.get("filtered_candidates") or state.get("search_candidates") or []
    raw_content = call_chat_completion(
        build_candidate_judge_messages(
            detected_product=_model_to_dict(frame_analysis),
            ocr_analysis=_compact_ocr_summary(state.get("ocr_analysis")),
            visual_analysis=_compact_visual_summary(state.get("visual_analysis")),
            query=_candidate_judge_query_summary(state["query"]),
            candidates=[_candidate_judge_summary(candidate) for candidate in candidates[:5]],
            google_results=[
                {
                    "title": _truncate_text(result.title),
                    "snippet": _truncate_text(result.snippet),
                    "source_query": _truncate_text(result.source_query, 80),
                }
                for result in (state.get("google_search_results") or [])[:3]
            ],
        ),
        model=settings.gemini_query_model,
        temperature=0.0,
        timeout_sec=min(settings.gemini_timeout_sec, 6.0),
    )
    parsed = extract_json_object(raw_content)
    _print_graph_debug("candidate_judge.ai_response", {
        "raw_content": raw_content,
        "parsed": parsed,
    })

    identification = _normalize_search_identification(parsed.get("identification") or {}, frame_analysis)
    quality = _normalize_result_quality(parsed.get("quality") or {})
    return identification, quality


def _candidate_judge_summary(candidate: ProductCandidate) -> dict[str, Any]:
    return {
        "title": _truncate_text(candidate.title),
        "source": candidate.product_type,
        "source_query": _truncate_text(candidate.source_query, 80),
        "snippet": _truncate_text(candidate.snippet),
        "brand": _truncate_text(candidate.brand, 60),
        "maker": _truncate_text(candidate.maker, 60),
        "category": " > ".join(
            part
            for part in [candidate.category1, candidate.category2, candidate.category3, candidate.category4]
            if part
        ),
        "text_score": candidate.text_score,
        "visual_score": candidate.visual_score,
        "final_score": candidate.final_score,
    }


def _candidate_judge_query_summary(query: Any) -> dict[str, Any]:
    return {
        "primary_query": getattr(query, "primary_query", None),
        "exact_text_queries": list(getattr(query, "exact_text_queries", []) or [])[:3],
        "visual_queries": list(getattr(query, "visual_queries", []) or [])[:3],
        "category_queries": list(getattr(query, "category_queries", []) or [])[:3],
        "normalized_brand": getattr(query, "normalized_brand", None),
        "normalized_model": getattr(query, "normalized_model", None),
        "normalized_category": getattr(query, "normalized_category", None),
    }


def _truncate_text(value: Any, max_length: int = 140) -> str | None:
    if value is None:
        return None

    text = " ".join(str(value).split())
    if len(text) <= max_length:
        return text

    return f"{text[:max_length]}..."


def _compact_ocr_summary(ocr: Any) -> dict[str, Any] | None:
    if not ocr:
        return None

    return {
        "raw_text": getattr(ocr, "raw_text", None),
        "visible_text_candidates": list(getattr(ocr, "visible_text_candidates", []) or [])[:4],
        "brand_text_candidates": list(getattr(ocr, "brand_text_candidates", []) or [])[:3],
        "model_text_candidates": list(getattr(ocr, "model_text_candidates", []) or [])[:3],
        "confidence": getattr(ocr, "confidence", None),
    }


def _compact_visual_summary(visual: Any) -> dict[str, Any] | None:
    if not visual:
        return None

    return {
        "product_type": getattr(visual, "product_type", None),
        "category_name": getattr(visual, "category_name", None),
        "color": getattr(visual, "color", None),
        "shape": getattr(visual, "shape", None),
        "style": getattr(visual, "style", None),
        "key_features": list(getattr(visual, "key_features", []) or [])[:5],
        "confidence": getattr(visual, "confidence", None),
    }


def _normalize_search_identification(
    data: dict[str, Any],
    fallback: AnalyzeFrameResponse,
) -> SearchIdentificationResult:
    if not isinstance(data, dict):
        data = {}

    return SearchIdentificationResult(
        target_name=str(data.get("target_name") or fallback.target_name or "Unknown product").strip(),
        category_name=str(data.get("category_name") or fallback.category_name or "기타").strip(),
        brand=_clean_optional(data.get("brand")) if data.get("brand") is not None else fallback.brand,
        model_name=_clean_optional(data.get("model_name")) if data.get("model_name") is not None else fallback.model_name,
        color=_clean_optional(data.get("color")) or fallback.color,
        shape=_clean_optional(data.get("shape")) or fallback.shape,
        logo_text=_clean_optional(data.get("logo_text")) or fallback.logo_text,
        key_features=_string_list(data.get("key_features"))[:8] or fallback.key_features,
        confidence=_clamp(data.get("confidence", fallback.confidence)),
        evidence=_string_list(data.get("evidence"))[:8],
        reason=_clean_optional(data.get("reason")),
    )


def _normalize_result_quality(data: dict[str, Any]) -> ResultQuality:
    if not isinstance(data, dict):
        data = {}

    try:
        enough_similar_count = int(data.get("enough_similar_count", 0) or 0)
    except (TypeError, ValueError):
        enough_similar_count = 0

    return ResultQuality(
        is_good=bool(data.get("is_good")),
        score=_clamp(data.get("score", 0.0)),
        enough_similar_count=max(0, enough_similar_count),
        reason=str(data.get("reason") or "").strip() or "AI judged candidate quality.",
    )


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    return _unique_strings([str(item).strip() for item in value if item and str(item).strip()])


def _unique_strings(values: list[str | None]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value:
            continue

        normalized = " ".join(str(value).split())
        key = normalized.lower()
        if normalized and key not in seen:
            result.append(normalized)
            seen.add(key)

    return result


def _clean_optional(value: Any) -> str | None:
    if value is None:
        return None

    cleaned = " ".join(str(value).split()).strip()
    return cleaned or None
