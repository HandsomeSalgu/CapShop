from typing import Any

from app.schemas.analysis_graph_schema import ProductCandidate
from app.services.graph.candidate_utils import _copy_candidate
from app.services.graph.state import ShoppingAnalysisState
from app.services.scoring.category_rules import (
    ACCESSORY_HARD_TERMS,
    ACCESSORY_SOFT_TERMS,
    ACCESSORY_TARGET_TERMS,
    _clamp,
    _contains_any,
    _infer_category_group,
)
from app.services.scoring.text_score import (
    _candidate_text,
    _has_strong_identity,
    _keyword_relevance_score,
    _target_text,
    _text_similarity_score,
)


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
