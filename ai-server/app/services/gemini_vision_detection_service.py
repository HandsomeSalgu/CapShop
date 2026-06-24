import json
from typing import Any

from app.core.config import settings
from app.schemas.detection_schema import AnalyzeFrameRequest, AnalyzeFrameResponse
from app.services.gemini_client import call_chat_completion, extract_json_object


SYSTEM_PROMPT = """
You are a visual commerce detection system for SyncShopper.

Your task is to analyze a captured image from a YouTube video and identify the single most purchase-relevant product in the selected area.

Rules:

1. Return only one JSON object.
2. Do not include markdown.
3. Do not include explanations outside JSON.
4. Identify only one product candidate.
5. Focus on purchasable consumer products such as fashion items, electronics, cosmetics, accessories, shoes, bags, furniture, kitchen items, and lifestyle goods.
6. When identifying the product, consider visible visual attributes such as color, shape, material, and style to make the target_name more specific and commerce-search-friendly.
7. Ignore YouTube UI, captions UI, buttons, comments, side recommendation thumbnails, player controls, browser UI, and unrelated text.
8. Do not identify people or infer personal identity.
9. If a brand or model is visible or strongly implied, include it.
10. If brand or model is unknown, return null for that field.
11. If the object is unclear or not purchase-relevant, return Unknown product with low confidence.
12. Extract the dominant product color when visible.
13. Extract the product shape, silhouette, or form factor when useful.
14. Extract visible brand/logo text if present, otherwise return null.
15. key_features must list 2 to 6 concise visual details useful for shopping search, such as material, pattern, texture, color placement, buttons, straps, screen shape, sole shape, or container shape.
16. confidence must be a number between 0.0 and 1.0.

Return JSON with exactly these keys:
{
"target_name": string,
"category_name": string,
"brand": string | null,
"model_name": string | null,
"color": string | null,
"shape": string | null,
"logo_text": string | null,
"key_features": string[],
"confidence": number
}

""".strip()


def _build_user_prompt(request: AnalyzeFrameRequest) -> str:
    subtitle_text = request.subtitle_text or ""

    return f"""
Analyze this captured YouTube frame area.

Context:
- video_id: {request.video_id}
- timestamp_sec: {request.timestamp_sec}
- subtitle_text: {subtitle_text}

Find the single most purchase-relevant product in the image.
Return only valid JSON.
""".strip()


def _build_messages(request: AnalyzeFrameRequest) -> list[dict[str, Any]]:
    return [
        {
            "role": "developer",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": _build_user_prompt(request),
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": request.image_base64,
                    },
                },
            ],
        },
    ]


def _normalize_response(data: dict[str, Any]) -> AnalyzeFrameResponse:
    target_name = data.get("target_name") or "Unknown product"
    category_name = data.get("category_name") or "Other"
    brand = data.get("brand")
    model_name = data.get("model_name")
    color = data.get("color")
    shape = data.get("shape")
    logo_text = data.get("logo_text")
    key_features = data.get("key_features") or []

    if not isinstance(key_features, list):
        key_features = []

    key_features = [
        str(feature).strip()
        for feature in key_features
        if feature and str(feature).strip()
    ]

    try:
        confidence = float(data.get("confidence", 0.55))
    except (TypeError, ValueError):
        confidence = 0.55

    confidence = max(0.0, min(confidence, 1.0))

    return AnalyzeFrameResponse(
        target_name=target_name,
        category_name=category_name,
        brand=brand,
        model_name=model_name,
        color=color,
        shape=shape,
        logo_text=logo_text,
        key_features=key_features[:6],
        confidence=confidence,
    )


def _truncate(value: str, max_length: int = 500) -> str:
    if len(value) <= max_length:
        return value

    return f"{value[:max_length]}..."


def _response_to_dict(response: AnalyzeFrameResponse) -> dict[str, Any]:
    if hasattr(response, "model_dump"):
        return response.model_dump()

    return response.dict()


def _print_detection_debug(
    request: AnalyzeFrameRequest,
    raw_content: str,
    parsed: dict[str, Any],
    normalized: AnalyzeFrameResponse,
) -> None:
    debug_payload = {
        "request": {
            "provider": settings.ai_detection_provider,
            "model": settings.gemini_vision_model,
            "video_id": request.video_id,
            "timestamp_sec": request.timestamp_sec,
            "subtitle_text": _truncate(request.subtitle_text or "", 300),
            "image_base64_chars": len(request.image_base64 or ""),
        },
        "ai_raw_content": _truncate(raw_content, 2000),
        "parsed_detection": parsed,
        "normalized_detection": _response_to_dict(normalized),
    }
    print(
        "\n[SyncShopper AI Detection Result]\n"
        + json.dumps(debug_payload, ensure_ascii=False, indent=2),
        flush=True,
    )


def analyze_frame_with_gemini_vision(request: AnalyzeFrameRequest) -> AnalyzeFrameResponse:
    content = call_chat_completion(
        _build_messages(request),
        model=settings.gemini_vision_model,
        temperature=0.1,
    )
    parsed = extract_json_object(content)
    normalized = _normalize_response(parsed)
    _print_detection_debug(request, content, parsed, normalized)
    return normalized
