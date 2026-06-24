import json
import re
from typing import Any

from fastapi import HTTPException

from app.core.config import settings
from app.schemas.analysis_graph_schema import (
    GoogleSearchResult,
    OcrAnalysisResult,
    ProductCandidate,
    SearchIdentificationResult,
    VisualFeatureAnalysisResult,
)
from app.schemas.detection_schema import AnalyzeFrameRequest, AnalyzeFrameResponse
from app.services.gms_openai_client import call_chat_completion, extract_json_object
from app.services.prompts.judge_prompt import SEARCH_IDENTIFICATION_PROMPT
from app.services.prompts.ocr_prompt import OCR_SYSTEM_PROMPT, build_ocr_user_prompt
from app.services.prompts.visual_prompt import VISUAL_SYSTEM_PROMPT, build_visual_user_prompt


def analyze_ocr(request: AnalyzeFrameRequest) -> OcrAnalysisResult:
    provider = settings.ai_detection_provider.lower()
    if provider == "mock":
        return _mock_ocr(request)
    if provider != "gpt":
        raise HTTPException(status_code=500, detail=f"Unsupported AI_DETECTION_PROVIDER: {settings.ai_detection_provider}")

    parsed = _call_image_json(
        OCR_SYSTEM_PROMPT,
        build_ocr_user_prompt(request),
        request.image_base64,
        temperature=0.0,
    )
    result = _normalize_ocr(parsed)
    _print_split_debug("OCR", parsed, result)
    return result


def analyze_visual_features(request: AnalyzeFrameRequest) -> VisualFeatureAnalysisResult:
    provider = settings.ai_detection_provider.lower()
    if provider == "mock":
        return _mock_visual(request)
    if provider != "gpt":
        raise HTTPException(status_code=500, detail=f"Unsupported AI_DETECTION_PROVIDER: {settings.ai_detection_provider}")

    parsed = _call_image_json(
        VISUAL_SYSTEM_PROMPT,
        build_visual_user_prompt(request),
        request.image_base64,
        temperature=0.1,
    )
    result = _normalize_visual(parsed)
    _print_split_debug("VISUAL", parsed, result)
    return result


def synthesize_initial_detection(
    ocr: OcrAnalysisResult,
    visual: VisualFeatureAnalysisResult,
) -> AnalyzeFrameResponse:
    key_features = _unique([
        *(visual.key_features or []),
        visual.material,
        visual.style,
        _join(*ocr.visible_text_candidates[:2]) if ocr.visible_text_candidates else None,
    ])[:6]
    logo_text = ocr.visible_text_candidates[0] if ocr.visible_text_candidates else None
    brand = ocr.brand_text_candidates[0] if ocr.brand_text_candidates else None
    model_name = ocr.model_text_candidates[0] if ocr.model_text_candidates else None
    target_name = _join(brand, model_name, visual.color, visual.style, visual.product_type)

    if not target_name:
        target_name = visual.product_type or "Unknown product"

    confidence = _clamp((ocr.confidence * 0.35) + (visual.confidence * 0.65))

    return AnalyzeFrameResponse(
        target_name=target_name,
        category_name=visual.category_name or visual.product_type or "기타",
        brand=brand,
        model_name=model_name,
        color=visual.color,
        shape=visual.shape,
        logo_text=logo_text,
        key_features=key_features,
        confidence=confidence,
    )


def identify_from_search(
    frame_analysis: AnalyzeFrameResponse,
    ocr: OcrAnalysisResult | None,
    visual: VisualFeatureAnalysisResult | None,
    naver_candidates: list[ProductCandidate],
    google_results: list[GoogleSearchResult],
) -> SearchIdentificationResult:
    provider = settings.ai_detection_provider.lower()
    if provider != "gpt" or not settings.gms_openai_api_key:
        return _fallback_identification(frame_analysis, ocr, visual, naver_candidates, google_results)

    payload = {
        "current_detection": _model_to_dict(frame_analysis),
        "ocr_analysis": _model_to_dict(ocr) if ocr else None,
        "visual_analysis": _model_to_dict(visual) if visual else None,
        "naver_candidates": [_candidate_summary(candidate) for candidate in naver_candidates[:10]],
        "google_results": [_model_to_dict(result) for result in google_results[:8]],
    }
    raw_content = call_chat_completion(
        [
            {"role": "developer", "content": SEARCH_IDENTIFICATION_PROMPT},
            {
                "role": "user",
                "content": (
                    "Resolve the most likely product identity from this evidence.\n"
                    + json.dumps(payload, ensure_ascii=False)
                ),
            },
        ],
        model=settings.gms_openai_query_model,
        temperature=0.1,
    )
    parsed = extract_json_object(raw_content)
    result = _normalize_identification(parsed, frame_analysis)
    _print_split_debug("SEARCH_IDENTIFICATION", parsed, result)
    return result


def apply_identification_to_frame(
    frame_analysis: AnalyzeFrameResponse,
    identification: SearchIdentificationResult | None,
) -> AnalyzeFrameResponse:
    if not identification:
        return frame_analysis

    return AnalyzeFrameResponse(
        target_name=identification.target_name or frame_analysis.target_name,
        category_name=identification.category_name or frame_analysis.category_name,
        brand=identification.brand if identification.brand is not None else frame_analysis.brand,
        model_name=identification.model_name if identification.model_name is not None else frame_analysis.model_name,
        color=identification.color if identification.color is not None else frame_analysis.color,
        shape=identification.shape if identification.shape is not None else frame_analysis.shape,
        logo_text=identification.logo_text if identification.logo_text is not None else frame_analysis.logo_text,
        key_features=identification.key_features or frame_analysis.key_features,
        confidence=max(frame_analysis.confidence, identification.confidence),
    )


def _call_image_json(
    system_prompt: str,
    user_prompt: str,
    image_base64: str,
    *,
    temperature: float,
) -> dict[str, Any]:
    raw_content = call_chat_completion(
        [
            {"role": "developer", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": image_base64}},
                ],
            },
        ],
        model=settings.gms_openai_vision_model,
        temperature=temperature,
    )
    return extract_json_object(raw_content)


def _normalize_ocr(data: dict[str, Any]) -> OcrAnalysisResult:
    return OcrAnalysisResult(
        raw_text=_clean_optional(data.get("raw_text")),
        visible_text_candidates=_string_list(data.get("visible_text_candidates"))[:8],
        brand_text_candidates=_string_list(data.get("brand_text_candidates"))[:5],
        model_text_candidates=_string_list(data.get("model_text_candidates"))[:5],
        confidence=_clamp(data.get("confidence", 0.0)),
        reason=_clean_optional(data.get("reason")),
    )


def _normalize_visual(data: dict[str, Any]) -> VisualFeatureAnalysisResult:
    return VisualFeatureAnalysisResult(
        product_type=_clean_optional(data.get("product_type")),
        category_name=_clean_optional(data.get("category_name")),
        color=_clean_optional(data.get("color")),
        shape=_clean_optional(data.get("shape")),
        material=_clean_optional(data.get("material")),
        style=_clean_optional(data.get("style")),
        key_features=_string_list(data.get("key_features"))[:8],
        confidence=_clamp(data.get("confidence", 0.0)),
        reason=_clean_optional(data.get("reason")),
    )


def _normalize_identification(
    data: dict[str, Any],
    fallback: AnalyzeFrameResponse,
) -> SearchIdentificationResult:
    return SearchIdentificationResult(
        target_name=str(data.get("target_name") or fallback.target_name or "Unknown product").strip(),
        category_name=str(data.get("category_name") or fallback.category_name or "기타").strip(),
        brand=_clean_optional(data.get("brand")),
        model_name=_clean_optional(data.get("model_name")),
        color=_clean_optional(data.get("color")) or fallback.color,
        shape=_clean_optional(data.get("shape")) or fallback.shape,
        logo_text=_clean_optional(data.get("logo_text")) or fallback.logo_text,
        key_features=_string_list(data.get("key_features"))[:8] or fallback.key_features,
        confidence=_clamp(data.get("confidence", fallback.confidence)),
        evidence=_string_list(data.get("evidence"))[:8],
        reason=_clean_optional(data.get("reason")),
    )


def _fallback_identification(
    frame_analysis: AnalyzeFrameResponse,
    ocr: OcrAnalysisResult | None,
    visual: VisualFeatureAnalysisResult | None,
    naver_candidates: list[ProductCandidate],
    google_results: list[GoogleSearchResult],
) -> SearchIdentificationResult:
    evidence = _unique([
        *(result.title for result in google_results[:3]),
        *(candidate.title for candidate in naver_candidates[:3]),
    ])[:5]
    logo_text = frame_analysis.logo_text
    if not logo_text and ocr and ocr.visible_text_candidates:
        logo_text = ocr.visible_text_candidates[0]

    key_features = frame_analysis.key_features
    if visual and visual.key_features:
        key_features = _unique([*visual.key_features, *key_features])[:8]

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
        reason="Fallback identification used split OCR/visual analysis and search result titles.",
    )


def _mock_ocr(request: AnalyzeFrameRequest) -> OcrAnalysisResult:
    text = f"{request.video_id} {request.subtitle_text or ''}"
    candidates = _unique(re.findall(r"[A-Za-z][A-Za-z0-9 ]{1,24}", text))[:5]
    return OcrAnalysisResult(
        raw_text=" ".join(candidates) or None,
        visible_text_candidates=candidates,
        brand_text_candidates=[item for item in candidates if item.lower() in {"nike", "apple", "sony"}],
        model_text_candidates=[item for item in candidates if re.search(r"\d", item)],
        confidence=0.7 if candidates else 0.2,
        reason="Mock OCR extracted text-like tokens from request context.",
    )


def _mock_visual(request: AnalyzeFrameRequest) -> VisualFeatureAnalysisResult:
    text = f"{request.video_id} {request.subtitle_text or ''}".lower()
    if "jersey" in text or "orange" in text:
        return VisualFeatureAnalysisResult(
            product_type="sports jersey t-shirt",
            category_name="패션 의류",
            color="orange",
            shape="short-sleeve crewneck top",
            material="polyester-like jersey fabric",
            style="graphic sportswear",
            key_features=["orange body", "black lettering", "graphic print", "short sleeves"],
            confidence=0.78,
            reason="Mock visual analysis matched jersey/orange context.",
        )
    return VisualFeatureAnalysisResult(
        product_type="Unknown product",
        category_name="기타",
        color=None,
        shape=None,
        material=None,
        style=None,
        key_features=[],
        confidence=0.45,
        reason="Mock visual analysis did not match a known fixture.",
    )


def _candidate_summary(candidate: ProductCandidate) -> dict[str, Any]:
    return {
        "title": candidate.title,
        "source": candidate.product_type,
        "snippet": candidate.snippet,
        "brand": candidate.brand,
        "mall_name": candidate.mall_name,
        "category": " > ".join(
            part
            for part in [candidate.category1, candidate.category2, candidate.category3, candidate.category4]
            if part
        ),
        "text_score": candidate.text_score,
    }


def _print_split_debug(label: str, parsed: dict[str, Any], normalized: Any) -> None:
    print(
        f"\n[SyncShopper Split Analysis] {label}\n"
        + json.dumps(
            {
                "parsed": parsed,
                "normalized": _model_to_dict(normalized),
            },
            ensure_ascii=False,
            indent=2,
        ),
        flush=True,
    )


def _model_to_dict(model: Any) -> dict[str, Any]:
    if model is None:
        return {}
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    return dict(model)


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return _unique([str(item).strip() for item in value if item and str(item).strip()])


def _unique(values: list[str | None]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value:
            continue
        normalized = re.sub(r"\s+", " ", value).strip()
        key = normalized.lower()
        if normalized and key not in seen:
            result.append(normalized)
            seen.add(key)
    return result


def _join(*parts: str | None) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip())


def _clean_optional(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"\s+", " ", str(value)).strip()
    return cleaned or None


def _clamp(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    return max(0.0, min(number, 1.0))
