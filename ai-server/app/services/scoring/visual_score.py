from typing import Any
from urllib.parse import urlparse

from fastapi import HTTPException

from app.core.config import settings
from app.schemas.analysis_graph_schema import ProductCandidate, ShoppingAnalysisRequest
from app.schemas.detection_schema import AnalyzeFrameResponse
from app.services.gemini_client import call_chat_completion, extract_json_object
from app.services.graph.candidate_utils import _candidate_prompt_id, _copy_candidate
from app.services.graph.debug import _model_to_dict, _print_graph_debug
from app.services.prompts.visual_prompt import _visual_rerank_messages
from app.services.scoring.category_rules import _clamp


def _fallback_visual_rerank(
    candidates: list[ProductCandidate],
    *,
    visual_reason: str = "mock visual score copied from text/category score",
) -> list[ProductCandidate]:
    reranked = [
        _copy_candidate(
            candidate,
            visual_score=candidate.text_score,
            final_score=candidate.text_score,
            visual_reason=visual_reason,
        )
        for candidate in candidates
    ]
    return sorted(reranked, key=lambda item: item.final_score, reverse=True)

def _gemini_visual_rerank(
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
            "reason": "candidate image URL was not safe for Gemini image input",
        })

    messages = _visual_rerank_messages(content)
    try:
        raw_content = call_chat_completion(
            messages,
            model=settings.gemini_model,
            temperature=0.0,
        )
    except HTTPException as exc:
        if not _is_invalid_candidate_image_error(exc):
            raise

        _print_graph_debug("visual_reranker.image_retry", {
            "reason": "Gemini rejected at least one candidate image URL; retrying without candidate images",
            "detail": exc.detail,
        })
        raw_content = call_chat_completion(
            _visual_rerank_messages(_without_candidate_images(content, request.image_base64)),
            model=settings.gemini_model,
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
    return (
        "invalid_image_url" in detail
        or "Error while downloading" in detail
        or "candidate image download" in detail
    )

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
