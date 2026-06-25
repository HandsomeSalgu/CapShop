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
from app.services.gemini_client import call_chat_completion, extract_json_object
from app.services.prompts.judge_prompt import SEARCH_IDENTIFICATION_PROMPT
from app.services.prompts.ocr_prompt import OCR_SYSTEM_PROMPT, build_ocr_user_prompt
from app.services.prompts.visual_prompt import VISUAL_SYSTEM_PROMPT, build_visual_user_prompt


def analyze_ocr(request: AnalyzeFrameRequest) -> OcrAnalysisResult:
    provider = settings.ai_detection_provider.lower()
    if provider == "mock":
        return _mock_ocr(request)
    if provider != "gemini":
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
    if provider != "gemini":
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


def koreanize_visual_analysis(visual: VisualFeatureAnalysisResult) -> VisualFeatureAnalysisResult:
    haystack = _join(
        visual.product_type,
        visual.category_name,
        visual.color,
        visual.shape,
        visual.material,
        visual.style,
        " ".join(visual.key_features or []),
    ).lower()
    updates = {
        "product_type": _korean_product_type(haystack, visual.product_type),
        "category_name": _korean_category_name(haystack, visual.category_name),
        "color": _korean_color(haystack, visual.color),
        "shape": _korean_shape(haystack, visual.shape),
        "material": _korean_material(haystack, visual.material),
        "style": _korean_style(haystack, visual.style),
        "key_features": _korean_key_features(visual.key_features or [], haystack),
    }
    if hasattr(visual, "model_copy"):
        return visual.model_copy(update=updates)
    return visual.copy(update=updates)


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
        category_name=visual.category_name or visual.product_type or "\uAE30\uD0C0",
        brand=brand,
        model_name=model_name,
        color=visual.color,
        shape=visual.shape,
        logo_text=logo_text,
        key_features=key_features,
        confidence=confidence,
    )


def _korean_product_type(haystack: str, fallback: str | None) -> str | None:
    if _contains_any_text(haystack, ["button-up", "button up", "button-front", "collared", "long sleeve", "long-sleeve"]):
        return "\uAE34\uD314 \uC154\uCE20" if _contains_any_text(haystack, ["long sleeve", "long-sleeve"]) else "\uC154\uCE20"
    if _contains_any_text(haystack, ["t-shirt", "tee", "crew neck", "crewneck"]):
        return "\uD2F0\uC154\uCE20"
    if _contains_any_text(haystack, ["shirt"]):
        return "\uC154\uCE20"
    if _contains_any_text(haystack, ["jacket", "outerwear", "jumper"]):
        return "\uC7AC\uD0B7"
    if _contains_any_text(haystack, ["coat"]):
        return "\uCF54\uD2B8"
    if _contains_any_text(haystack, ["sneaker", "shoe"]):
        return "\uC6B4\uB3D9\uD654"
    return fallback


def _korean_category_name(haystack: str, fallback: str | None) -> str | None:
    if _contains_any_text(haystack, ["apparel", "shirt", "clothing", "fashion"]):
        return "\uB0A8\uC131 \uC758\uB958" if _contains_any_text(haystack, ["men", "men\'s", "male"]) else "\uC758\uB958"
    if _contains_any_text(haystack, ["shoe", "sneaker"]):
        return "\uC2E0\uBC1C"
    if _contains_any_text(haystack, ["electronics", "device"]):
        return "\uC804\uC790\uAE30\uAE30"
    return fallback


def _korean_color(haystack: str, fallback: str | None) -> str | None:
    color_map = [
        (["tan", "beige"], "\uBCA0\uC774\uC9C0"),
        (["khaki"], "\uCE74\uD0A4"),
        (["olive green", "olive-green"], "\uC62C\uB9AC\uBE0C \uADF8\uB9B0"),
        (["black"], "\uAC80\uC815\uC0C9"),
        (["white"], "\uD770\uC0C9"),
        (["blue"], "\uD30C\uB780\uC0C9"),
        (["green"], "\uCD08\uB85D\uC0C9"),
        (["red"], "\uBE68\uAC04\uC0C9"),
        (["orange"], "\uC8FC\uD669\uC0C9"),
        (["yellow"], "\uB178\uB780\uC0C9"),
    ]
    for terms, label in color_map:
        if _contains_any_text(haystack, terms):
            return label
    return fallback


def _korean_shape(haystack: str, fallback: str | None) -> str | None:
    parts = []
    if _contains_any_text(haystack, ["collared", "collar"]):
        parts.append("\uCE74\uB77C")
    if _contains_any_text(haystack, ["long sleeve", "long-sleeve"]):
        parts.append("\uAE34\uD314")
    if _contains_any_text(haystack, ["button-up", "button up", "button-front"]):
        parts.append("\uBC84\uD2BC\uC5C5")
    if parts:
        return " ".join(parts)
    return fallback


def _korean_material(haystack: str, fallback: str | None) -> str | None:
    if _contains_any_text(haystack, ["woven fabric", "fabric"]):
        return "\uC9C1\uBB3C"
    if _contains_any_text(haystack, ["cotton"]):
        return "\uBA74"
    if _contains_any_text(haystack, ["polyester"]):
        return "\uD3F4\uB9AC\uC5D0\uC2A4\uD130"
    return fallback


def _korean_style(haystack: str, fallback: str | None) -> str | None:
    parts = []
    if _contains_any_text(haystack, ["plaid", "checkered", "checked", "check pattern", "tartan", "gingham"]):
        parts.append("\uCCB4\uD06C")
    if _contains_any_text(haystack, ["striped", "stripe pattern", "stripes"]):
        parts.append("\uC2A4\uD2B8\uB77C\uC774\uD504")
    if _contains_any_text(haystack, ["houndstooth"]):
        parts.append("\uD558\uC6B0\uC2A4\uD22C\uC2A4")
    if _contains_any_text(haystack, ["casual"]):
        parts.append("\uCE90\uC8FC\uC5BC")
    if _contains_any_text(haystack, ["button-up", "button up", "button-front"]):
        parts.append("\uBC84\uD2BC\uC5C5")
    if _contains_any_text(haystack, ["relaxed fit", "loose fit"]):
        parts.append("\uB8E8\uC988\uD54F")
    if parts:
        return " ".join(parts)
    return fallback


def _korean_key_features(features: list[str], haystack: str) -> list[str]:
    labels = []
    feature_text = " ".join(features).lower() + " " + haystack
    candidates = [
        (["plaid", "checkered", "checked", "check pattern", "tartan", "gingham"], "\uCCB4\uD06C \uD328\uD134"),
        (["striped", "stripe pattern", "stripes"], "\uC2A4\uD2B8\uB77C\uC774\uD504 \uD328\uD134"),
        (["houndstooth"], "\uD558\uC6B0\uC2A4\uD22C\uC2A4 \uD328\uD134"),
        (["color-block", "color block", "colorblocking"], "\uCEEC\uB7EC\uBE14\uB85D"),
        (["ribbed"], "\uB9BD \uC9DC\uC784"),
        (["cable-knit", "cable knit"], "\uCF00\uC774\uBE14 \uB2C8\uD2B8"),
        (["collar", "collared"], "\uCE74\uB77C"),
        (["button-front", "button front", "button-up", "button up"], "\uBC84\uD2BC \uC5EC\uBC08"),
        (["long sleeve", "long-sleeve"], "\uAE34\uD314"),
        (["buttoned cuffs", "cuffs"], "\uBC84\uD2BC \uC18C\uB9E4"),
        (["patch pocket", "chest pocket"], "\uAC00\uC2B4 \uD3EC\uCF13"),
        (["relaxed fit", "loose fit"], "\uB8E8\uC988\uD54F"),
        (["woven fabric"], "\uC9C1\uBB3C \uC18C\uC7AC"),
    ]
    for terms, label in candidates:
        if _contains_any_text(feature_text, terms):
            labels.append(label)
    return _unique(labels)[:6] or features


def _contains_any_text(text: str, terms: list[str]) -> bool:
    return any(term.lower() in text for term in terms if term)



def identify_from_search(
    frame_analysis: AnalyzeFrameResponse,
    ocr: OcrAnalysisResult | None,
    visual: VisualFeatureAnalysisResult | None,
    naver_candidates: list[ProductCandidate],
    google_results: list[GoogleSearchResult],
) -> SearchIdentificationResult:
    provider = settings.ai_detection_provider.lower()
    if provider != "gemini" or not settings.gemini_api_key:
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
        model=settings.gemini_query_model,
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
        model=settings.gemini_vision_model,
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
        category_name=str(data.get("category_name") or fallback.category_name or "\uAE30\uD0C0").strip(),
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
            category_name="\uD328\uC158 \uC758\uB958",
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
        category_name="\uAE30\uD0C0",
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
