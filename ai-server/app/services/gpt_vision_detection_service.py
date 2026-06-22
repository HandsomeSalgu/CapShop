import json
import logging
from typing import Any

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.schemas.detection_schema import AnalyzeFrameRequest, AnalyzeFrameResponse


logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
You are a visual commerce detection system for SyncShopper.

Your task is to analyze a captured image from a YouTube video and identify the single most purchase-relevant product in the selected area.

Rules:
1. Return only one JSON object.
2. Do not include markdown.
3. Do not include explanations outside JSON.
4. Identify only one product candidate.
5. Focus on purchasable consumer products such as fashion items, electronics, cosmetics, accessories, shoes, bags, furniture, kitchen items, and lifestyle goods.
6. Ignore YouTube UI, captions UI, buttons, comments, side recommendation thumbnails, player controls, browser UI, and unrelated text.
7. Do not identify people or infer personal identity.
8. If a brand or model is visible or strongly implied, include it.
9. If brand or model is unknown, return null for that field.
10. If the object is unclear or not purchase-relevant, return Unknown product with low confidence.
11. confidence must be a number between 0.0 and 1.0.

Return JSON with exactly these keys:
{
  "target_name": string,
  "category_name": string,
  "brand": string | null,
  "model_name": string | null,
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


def _extract_json_content(content: str) -> dict[str, Any]:
    cleaned = content.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to parse GPT Vision response as JSON: {_truncate(content)}",
        ) from exc

    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=502,
            detail="GPT Vision response JSON must be an object",
        )

    return parsed


def _normalize_response(data: dict[str, Any]) -> AnalyzeFrameResponse:
    target_name = data.get("target_name") or "Unknown product"
    category_name = data.get("category_name") or "기타"
    brand = data.get("brand")
    model_name = data.get("model_name")

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
        confidence=confidence,
    )


def _build_payload(request: AnalyzeFrameRequest) -> dict[str, Any]:
    return {
        "model": settings.gms_openai_model,
        "messages": [
            {
                "role": "system",
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
        ],
        "temperature": 0.1,
    }


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
            "model": settings.gms_openai_model,
            "video_id": request.video_id,
            "timestamp_sec": request.timestamp_sec,
            "subtitle_text": _truncate(request.subtitle_text or "", 300),
            "image_base64_chars": len(request.image_base64 or ""),
        },
        "gpt_raw_content": _truncate(raw_content, 2000),
        "parsed_detection": parsed,
        "normalized_detection": _response_to_dict(normalized),
    }
    print(
        "\n[SyncShopper AI Detection Result]\n"
        + json.dumps(debug_payload, ensure_ascii=False, indent=2),
        flush=True,
    )


def analyze_frame_with_gpt_vision(request: AnalyzeFrameRequest) -> AnalyzeFrameResponse:
    if not settings.gms_openai_api_key:
        raise HTTPException(
            status_code=500,
            detail="GMS_OPENAI_API_KEY is not configured",
        )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.gms_openai_api_key}",
    }
    payload = _build_payload(request)

    try:
        with httpx.Client(timeout=settings.gms_openai_timeout_sec) as client:
            response = client.post(
                settings.gms_openai_chat_completions_url,
                headers=headers,
                json=payload,
            )
    except httpx.TimeoutException as exc:
        logger.warning("GPT Vision request timed out")
        raise HTTPException(
            status_code=504,
            detail="GPT Vision request timed out",
        ) from exc
    except httpx.RequestError as exc:
        logger.warning("GPT Vision request failed: %s", str(exc))
        raise HTTPException(
            status_code=502,
            detail=f"GPT Vision request failed: {str(exc)}",
        ) from exc

    if response.status_code >= 400:
        logger.warning(
            "GPT Vision API error: status=%s image_chars=%s response=%s",
            response.status_code,
            len(request.image_base64 or ""),
            _truncate(response.text),
        )
        raise HTTPException(
            status_code=502,
            detail=f"GPT Vision API error: {response.status_code} {_truncate(response.text)}",
        )

    try:
        response_json = response.json()
    except json.JSONDecodeError as exc:
        logger.warning("GPT Vision API returned non-JSON response: %s", _truncate(response.text))
        raise HTTPException(
            status_code=502,
            detail=f"GPT Vision API returned non-JSON response: {_truncate(response.text)}",
        ) from exc

    try:
        content = response_json["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        logger.warning(
            "Unexpected GPT Vision response format: %s",
            _truncate(json.dumps(response_json, ensure_ascii=False)),
        )
        raise HTTPException(
            status_code=502,
            detail=f"Unexpected GPT Vision response format: {_truncate(json.dumps(response_json, ensure_ascii=False))}",
        ) from exc

    parsed = _extract_json_content(content)
    normalized = _normalize_response(parsed)
    _print_detection_debug(request, content, parsed, normalized)
    return normalized
