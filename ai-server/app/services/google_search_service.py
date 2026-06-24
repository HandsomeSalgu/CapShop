"""Deprecated Google Custom Search fallback.

LangGraph's main Google search path uses Gemini Grounding with Google Search.
This module is kept for compatibility and manual fallback experiments.
"""

from typing import Any

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.schemas.analysis_graph_schema import GoogleSearchResult


def search_google_custom(query: str, *, display: int = 5) -> list[GoogleSearchResult]:
    provider = settings.google_custom_search_provider.lower()

    if provider == "disabled":
        _print_google_search_log(query, [])
        return []

    if provider == "mock":
        results = _search_mock(query, display=display)
        _print_google_search_log(query, results)
        return results

    if provider != "google":
        raise HTTPException(
            status_code=500,
            detail=f"Unsupported GOOGLE_CUSTOM_SEARCH_PROVIDER: {settings.google_custom_search_provider}",
        )

    if not settings.google_custom_search_api_key or not settings.google_custom_search_cx:
        _print_google_search_log(query, [], note="Google Custom Search credentials are not configured")
        return []

    try:
        results = _search_google(query, display=display)
    except HTTPException as exc:
        if settings.google_custom_search_strict_errors:
            raise

        _print_google_search_log(query, [], note=_google_error_note(exc))
        return []

    _print_google_search_log(query, results)
    return results


def _search_google(query: str, *, display: int) -> list[GoogleSearchResult]:
    params = {
        "key": settings.google_custom_search_api_key,
        "cx": settings.google_custom_search_cx,
        "q": query,
        "num": max(1, min(display, 10)),
    }

    try:
        with httpx.Client(timeout=settings.gms_openai_timeout_sec) as client:
            response = client.get(settings.google_custom_search_url, params=params)
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="Google Custom Search request timed out") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Google Custom Search request failed: {str(exc)}") from exc

    if response.status_code >= 400:
        error_detail = _google_api_error_detail(response)
        raise HTTPException(
            status_code=502,
            detail=f"Google Custom Search API error: {response.status_code} {error_detail}",
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Google Custom Search API returned non-JSON response: {_truncate(response.text)}",
        ) from exc

    items = payload.get("items") or []
    if not isinstance(items, list):
        return []

    return [_from_google_item(item, query) for item in items if isinstance(item, dict)]


def _from_google_item(item: dict[str, Any], query: str) -> GoogleSearchResult:
    pagemap = item.get("pagemap") if isinstance(item.get("pagemap"), dict) else {}
    images = pagemap.get("cse_image") if isinstance(pagemap.get("cse_image"), list) else []
    image = None
    if images and isinstance(images[0], dict):
        image = images[0].get("src")

    return GoogleSearchResult(
        title=str(item.get("title") or "").strip(),
        link=item.get("link"),
        display_link=item.get("displayLink"),
        snippet=item.get("snippet"),
        image=image,
        source_query=query,
    )


def _search_mock(query: str, *, display: int) -> list[GoogleSearchResult]:
    return [
        GoogleSearchResult(
            title=f"{query} product reference",
            link="https://www.google.example/search-result-1",
            display_link="google.example",
            snippet=f"Mock Google Custom Search result that describes {query}.",
            source_query=query,
        )
    ][:display]


def _print_google_search_log(
    query: str,
    results: list[GoogleSearchResult],
    *,
    note: str | None = None,
) -> None:
    samples = [_truncate(result.title, 80) for result in results[:3] if result.title]
    suffix = f" note='{_truncate(note, 240)}'" if note else ""
    print(
        "\n[SyncShopper Google Search] "
        f"query='{_truncate(query, 120)}' result_count={len(results)} samples={samples}{suffix}",
        flush=True,
    )


def _truncate(value: str, max_length: int = 500) -> str:
    if len(value) <= max_length:
        return value
    return f"{value[:max_length]}..."


def _google_api_error_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return _truncate(response.text)

    if not isinstance(payload, dict):
        return _truncate(response.text)

    error = payload.get("error")
    if not isinstance(error, dict):
        return _truncate(response.text)

    message = str(error.get("message") or "").strip()
    status = str(error.get("status") or "").strip()
    reason = _google_error_reason(error)
    parts = [part for part in [status, reason, message] if part]
    if not parts:
        return _truncate(response.text)

    return _truncate(" | ".join(parts))


def _google_error_reason(error: dict[str, Any]) -> str | None:
    errors = error.get("errors")
    if not isinstance(errors, list):
        return None

    for item in errors:
        if isinstance(item, dict) and item.get("reason"):
            return str(item["reason"]).strip()

    return None


def _google_error_note(exc: HTTPException) -> str:
    detail = str(exc.detail or exc)
    return f"Google Custom Search skipped: {detail}"
