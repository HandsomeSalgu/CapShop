import json
from typing import Any, Optional

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.schemas.commerce_query_schema import CommerceQueryRequest, CommerceQueryResponse


SYSTEM_PROMPT = """
You are a commerce search query generator for SyncShopper.

Your task is to convert visual product detection results into high-quality search queries for a Korean commerce search API such as Naver Shopping.

Rules:
1. Return only one JSON object.
2. Do not include markdown.
3. Do not include explanations outside JSON.
4. Generate one primary_query and multiple fallback_queries.
5. primary_query should be concise and useful for shopping search.
6. primary_query should usually be 2 to 6 words.
7. If brand and model are known, use them in primary_query.
8. If model is unknown, use brand + product category.
9. If brand is unknown, use product type, color, or category.
10. Do not invent brand or model names.
11. Do not include YouTube UI text, browser UI text, captions UI, comments, or unrelated text.
12. Prefer Korean shopping-friendly query terms when useful.
13. Include English fallback query when brand/model are English.
14. query_confidence must be between 0.0 and 1.0.
15. If detection confidence is low, generate broader queries and lower query_confidence.

Return JSON with exactly these keys:
{
  "primary_query": string,
  "fallback_queries": string[],
  "normalized_brand": string | null,
  "normalized_model": string | null,
  "normalized_category": string | null,
  "query_confidence": number,
  "reason": string
}
""".strip()


def _build_user_prompt(request: CommerceQueryRequest) -> str:
    return f"""
Create commerce search queries from the following detection result.

Detection Result:
- target_name: {request.target_name or ""}
- category_name: {request.category_name or ""}
- brand: {request.brand or ""}
- model_name: {request.model_name or ""}
- confidence: {request.confidence}

Context:
- subtitle_text: {request.subtitle_text or ""}
- video_id: {request.video_id or ""}
- timestamp_sec: {request.timestamp_sec if request.timestamp_sec is not None else ""}

Generate search queries for Naver Shopping.
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
            detail=f"Failed to parse commerce query response as JSON: {_truncate(content)}",
        ) from exc

    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=502,
            detail="Commerce query response JSON must be an object",
        )

    return parsed


def _normalize_response(data: dict[str, Any], request: CommerceQueryRequest) -> CommerceQueryResponse:
    primary_query = str(data.get("primary_query") or _build_fallback_primary_query(request)).strip()
    if not primary_query:
        primary_query = "상품"

    fallback_queries = data.get("fallback_queries") or []
    if not isinstance(fallback_queries, list):
        fallback_queries = []

    fallback_queries = [
        str(query).strip()
        for query in fallback_queries
        if query and str(query).strip()
    ]

    try:
        query_confidence = float(data.get("query_confidence", request.confidence))
    except (TypeError, ValueError):
        query_confidence = request.confidence

    query_confidence = max(0.0, min(query_confidence, 1.0))

    reason = data.get("reason") or "Detection 결과를 기반으로 Commerce 검색어를 생성했습니다."

    return CommerceQueryResponse(
        primary_query=primary_query,
        fallback_queries=fallback_queries[:5],
        normalized_brand=data.get("normalized_brand"),
        normalized_model=data.get("normalized_model"),
        normalized_category=data.get("normalized_category"),
        query_confidence=query_confidence,
        reason=str(reason).strip(),
    )


def _build_fallback_primary_query(request: CommerceQueryRequest) -> str:
    parts: list[str] = []

    if request.brand:
        parts.append(request.brand)

    if request.model_name:
        parts.append(request.model_name)
    elif request.target_name and request.target_name.lower() != "unknown product":
        parts.append(request.target_name)
    elif request.category_name:
        parts.append(request.category_name)
    else:
        parts.append("상품")

    return " ".join(parts).strip()


def _generate_mock_commerce_query(request: CommerceQueryRequest) -> CommerceQueryResponse:
    primary_query = _build_fallback_primary_query(request) or "상품"
    fallback_candidates = [
        request.target_name,
        " ".join(part for part in [request.brand, request.target_name] if part),
        " ".join(part for part in [request.brand, request.category_name] if part),
        request.category_name,
    ]

    fallback_queries = []
    for query in fallback_candidates:
        if query and query.strip() and query.strip() != primary_query and query.strip() not in fallback_queries:
            fallback_queries.append(query.strip())

    return _debug_response(request, CommerceQueryResponse(
        primary_query=primary_query,
        fallback_queries=fallback_queries[:5],
        normalized_brand=request.brand,
        normalized_model=request.model_name,
        normalized_category=request.category_name,
        query_confidence=max(0.0, min(request.confidence or 0.7, 1.0)),
        reason="Mock commerce query generated from detection result.",
    ), provider="mock")


def _build_payload(request: CommerceQueryRequest) -> dict[str, Any]:
    return {
        "model": settings.gms_openai_query_model,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": _build_user_prompt(request),
            },
        ],
        "temperature": 0.2,
    }


def _truncate(value: str, max_length: int = 500) -> str:
    if len(value) <= max_length:
        return value

    return f"{value[:max_length]}..."


def _response_to_dict(response: CommerceQueryResponse) -> dict[str, Any]:
    if hasattr(response, "model_dump"):
        return response.model_dump()

    return response.dict()


def _print_query_debug(
    request: CommerceQueryRequest,
    response: CommerceQueryResponse,
    raw_content: Optional[str] = None,
    parsed: Optional[dict[str, Any]] = None,
    provider: Optional[str] = None,
) -> None:
    debug_payload = {
        "request_detection": {
            "target_name": request.target_name,
            "category_name": request.category_name,
            "brand": request.brand,
            "model_name": request.model_name,
            "confidence": request.confidence,
            "subtitle_text": _truncate(request.subtitle_text or "", 300),
            "video_id": request.video_id,
            "timestamp_sec": request.timestamp_sec,
        },
        "provider": provider or settings.ai_commerce_query_provider,
        "model": settings.gms_openai_query_model,
        "gpt_raw_content": _truncate(raw_content, 2000) if raw_content is not None else None,
        "parsed_query": parsed,
        "normalized_query": _response_to_dict(response),
    }
    print(
        "\n[SyncShopper AI Commerce Query Result]\n"
        + json.dumps(debug_payload, ensure_ascii=False, indent=2),
        flush=True,
    )


def _debug_response(
    request: CommerceQueryRequest,
    response: CommerceQueryResponse,
    provider: Optional[str] = None,
) -> CommerceQueryResponse:
    _print_query_debug(request, response, provider=provider)
    return response


def generate_commerce_query(request: CommerceQueryRequest) -> CommerceQueryResponse:
    provider = settings.ai_commerce_query_provider.lower()

    if provider == "mock":
        return _generate_mock_commerce_query(request)

    if provider != "gpt":
        raise HTTPException(
            status_code=500,
            detail=f"Unsupported AI_COMMERCE_QUERY_PROVIDER: {settings.ai_commerce_query_provider}",
        )

    if not settings.gms_openai_api_key:
        raise HTTPException(
            status_code=500,
            detail="GMS_OPENAI_API_KEY is not configured",
        )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.gms_openai_api_key}",
    }

    try:
        with httpx.Client(timeout=settings.gms_openai_timeout_sec) as client:
            response = client.post(
                settings.gms_openai_chat_completions_url,
                headers=headers,
                json=_build_payload(request),
            )
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail="Commerce query generation request timed out",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Commerce query generation request failed: {str(exc)}",
        ) from exc

    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"Commerce query generation API error: {response.status_code} {_truncate(response.text)}",
        )

    try:
        response_json = response.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Commerce query generation API returned non-JSON response: {_truncate(response.text)}",
        ) from exc

    try:
        content = response_json["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unexpected commerce query response format: {_truncate(json.dumps(response_json, ensure_ascii=False))}",
        ) from exc

    parsed = _extract_json_content(content)
    normalized = _normalize_response(parsed, request)
    _print_query_debug(request, normalized, raw_content=content, parsed=parsed)
    return normalized
