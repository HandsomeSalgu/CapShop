from app.schemas.analysis_graph_schema import ProductCandidate
from app.schemas.commerce_query_schema import CommerceQueryResponse
from app.schemas.detection_schema import AnalyzeFrameResponse
from app.services.graph.query_helpers import _target_text_from_frame, _visible_text_variants
from app.services.scoring.category_rules import (
    COLOR_MATCH_TERMS,
    GRAPHIC_MATCH_TERMS,
    SPORTS_MATCH_TERMS,
    TEXT_NEGATIVE_TERMS,
    _clamp,
    _contains_any,
    _infer_category_group,
    _tokens,
)


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
