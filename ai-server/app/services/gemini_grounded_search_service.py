import json
import re
from typing import Any

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.schemas.analysis_graph_schema import ProductCandidate
from app.services.cache import search_cache


GEMINI_GROUNDED_SEARCH_SOURCE = "GEMINI_GROUNDED_SEARCH"


def search_gemini_grounded_products(query: str, *, display: int = 5) -> list[ProductCandidate]:
    if not settings.gemini_api_key:
        _print_gemini_search_log(query, [], note="GEMINI_API_KEY is not configured")
        return []

    cache_key = ("GEMINI_GROUNDED_SEARCH", query, display, settings.gemini_search_model)
    cached_results = _get_cached_results(cache_key)
    if cached_results is not None:
        _print_cache_log("hit", query)
        return cached_results

    _print_cache_log("miss", query)

    try:
        payload = _call_gemini_interactions(query, display=display)
        candidates = _parse_gemini_candidates(payload, query=query, display=display)
    except Exception as exc:
        _print_gemini_search_log(query, [], note=f"Gemini grounded search skipped: {_error_message(exc)}")
        return []

    _set_cached_results(cache_key, candidates)
    _print_gemini_search_log(query, candidates)
    return candidates


def _call_gemini_interactions(query: str, *, display: int) -> dict[str, Any]:
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": settings.gemini_api_key or "",
    }
    payload = {
        "model": settings.gemini_search_model,
        "input": _build_search_prompt(query, display=display),
        "tools": [{"type": "google_search"}],
        "store": False,
        "generation_config": {
            "temperature": 0.0,
        },
    }

    try:
        with httpx.Client(timeout=settings.gemini_search_timeout_seconds) as client:
            response = client.post(settings.gemini_search_endpoint, headers=headers, json=payload)
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="Gemini grounded search request timed out") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Gemini grounded search request failed: {str(exc)}") from exc

    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"Gemini grounded search API error: {response.status_code} {_response_error_detail(response)}",
        )

    try:
        response_json = response.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Gemini grounded search returned non-JSON response: {_truncate(response.text)}",
        ) from exc

    if not isinstance(response_json, dict):
        raise HTTPException(status_code=502, detail="Gemini grounded search response must be a JSON object")

    return response_json


def _build_search_prompt(query: str, *, display: int) -> str:
    return (
        "Use Google Search grounding to find purchasable product candidates for SyncShopper.\n"
        "Return only valid JSON. Do not include markdown, prose, comments, or citations outside JSON.\n"
        f"Search query: {query}\n"
        f"Maximum products: {max(1, min(display, 10))}\n\n"
        "Each product must be a real purchasable product or highly relevant product listing. "
        "Prefer Korean shopping results when they are relevant. Avoid articles, videos, ads-only pages, "
        "and category pages unless no product pages are available.\n\n"
        "Return this exact JSON shape:\n"
        "{\n"
        '  "products": [\n'
        "    {\n"
        '      "title": "product title",\n'
        '      "brand": "brand or null",\n'
        '      "mall": "seller or site name or null",\n'
        '      "price_text": "visible price text or null",\n'
        '      "url": "product URL or null",\n'
        '      "image_url": "product image URL or null",\n'
        '      "reason": "short reason this matches the query",\n'
        '      "confidence": 0.0\n'
        "    }\n"
        "  ]\n"
        "}"
    )


def _parse_gemini_candidates(
    response_json: dict[str, Any],
    *,
    query: str,
    display: int,
) -> list[ProductCandidate]:
    output_text = _extract_output_text(response_json)
    parsed = _extract_json_object(output_text)
    products = parsed.get("products") or []
    if not isinstance(products, list):
        raise HTTPException(status_code=502, detail="Gemini grounded search JSON must include a products list")

    candidates: list[ProductCandidate] = []
    for item in products:
        if not isinstance(item, dict):
            continue

        candidate = _product_to_candidate(item, query=query)
        if candidate:
            candidates.append(candidate)

        if len(candidates) >= display:
            break

    return candidates


def _product_to_candidate(item: dict[str, Any], *, query: str) -> ProductCandidate | None:
    title = _optional_text(item.get("title"))
    if not title:
        return None

    url = _optional_text(item.get("url"))
    image_url = _optional_text(item.get("image_url"))
    brand = _optional_text(item.get("brand"))
    mall = _optional_text(item.get("mall"))
    price_text = _optional_text(item.get("price_text"))
    reason = _optional_text(item.get("reason"))
    confidence = _confidence(item.get("confidence"))
    snippet = _candidate_snippet(price_text=price_text, reason=reason)

    return ProductCandidate(
        title=title,
        link=url,
        image=image_url,
        thumbnail=image_url,
        lprice=_price_to_int(price_text),
        price_text=price_text,
        mall_name=mall,
        external_product_id=url,
        product_type=GEMINI_GROUNDED_SEARCH_SOURCE,
        query_type="GOOGLE_GROUNDING",
        source_query=query,
        snippet=snippet,
        brand=brand,
        text_score=confidence * 0.7,
        confidence=confidence,
        reason=reason,
    )


def _extract_output_text(response_json: dict[str, Any]) -> str:
    output_text = response_json.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    texts: list[str] = []
    for step in response_json.get("steps") or []:
        if not isinstance(step, dict) or step.get("type") != "model_output":
            continue

        for block in step.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str):
                texts.append(block["text"])

    if texts:
        return "\n".join(texts).strip()

    raise HTTPException(
        status_code=502,
        detail=f"Unexpected Gemini grounded search response format: {_truncate(json.dumps(response_json, ensure_ascii=False))}",
    )


def _extract_json_object(content: str) -> dict[str, Any]:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end <= start:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to parse Gemini grounded search output as JSON: {_truncate(content)}",
            )
        try:
            parsed = json.loads(cleaned[start:end + 1])
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to parse Gemini grounded search output as JSON: {_truncate(content)}",
            ) from exc

    if not isinstance(parsed, dict):
        raise HTTPException(status_code=502, detail="Gemini grounded search output JSON must be an object")

    return parsed


def _response_error_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return _truncate(response.text)

    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            message = _optional_text(error.get("message"))
            status = _optional_text(error.get("status"))
            return _truncate(" | ".join(part for part in [status, message] if part) or response.text)

    return _truncate(response.text)


def _candidate_snippet(*, price_text: str | None, reason: str | None) -> str | None:
    parts = [part for part in [price_text, reason] if part]
    return " | ".join(parts) if parts else None


def _price_to_int(price_text: str | None) -> int | None:
    if not price_text:
        return None

    match = re.search(r"\d[\d,]*", price_text)
    if not match:
        return None

    try:
        return int(match.group(0).replace(",", ""))
    except ValueError:
        return None


def _confidence(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.5

    if number < 0:
        return 0.0
    if number > 1:
        return 1.0
    return number


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    if not text or text.lower() in {"null", "none", "n/a"}:
        return None

    return text


def _print_gemini_search_log(
    query: str,
    results: list[ProductCandidate],
    *,
    note: str | None = None,
) -> None:
    samples = [_truncate(result.title, 80) for result in results[:3] if result.title]
    suffix = f" note='{_truncate(note, 240)}'" if note else ""
    print(
        "\n[SyncShopper Gemini Grounded Search] "
        f"query='{_truncate(query, 120)}' result_count={len(results)} samples={samples}{suffix}",
        flush=True,
    )


def _get_cached_results(key: tuple[str, str, int, str]) -> list[ProductCandidate] | None:
    if settings.search_cache_ttl_seconds <= 0 or settings.search_cache_max_size <= 0:
        return None

    return search_cache.get(key)


def _set_cached_results(key: tuple[str, str, int, str], results: list[ProductCandidate]) -> None:
    search_cache.set(
        key,
        results,
        ttl_seconds=settings.search_cache_ttl_seconds,
        max_size=settings.search_cache_max_size,
    )


def _print_cache_log(status: str, query: str) -> None:
    if settings.search_cache_ttl_seconds <= 0 or settings.search_cache_max_size <= 0:
        return

    print(
        "\n[SyncShopper Search Cache] "
        f"{status} source={GEMINI_GROUNDED_SEARCH_SOURCE} query='{_truncate(query, 120)}'",
        flush=True,
    )


def _error_message(exc: Exception) -> str:
    if isinstance(exc, HTTPException):
        return str(exc.detail or exc)

    return str(exc)


def _truncate(value: str | None, max_length: int = 500) -> str:
    text = value or ""
    if len(text) <= max_length:
        return text
    return f"{text[:max_length]}..."

