import json
from typing import Any

from fastapi import HTTPException


def _print_graph_debug(node_name: str, payload: dict[str, Any]) -> None:
    try:
        print(
            f"\n[SyncShopper LangGraph] {node_name} returned\n"
            + json.dumps(_debug_value(payload), ensure_ascii=False, indent=2),
            flush=True,
        )
    except Exception as exc:
        print(
            f"\n[SyncShopper LangGraph] {node_name} returned "
            f"(debug serialization failed: {exc})\n{payload}",
            flush=True,
        )


def _print_graph_error(node_name: str, exc: Exception) -> None:
    payload: dict[str, Any] = {
        "error_type": exc.__class__.__name__,
        "message": str(exc),
    }

    if isinstance(exc, HTTPException):
        payload.update({
            "status_code": exc.status_code,
            "detail": exc.detail,
        })

    print(
        f"\n[SyncShopper LangGraph] {node_name} failed\n"
        + json.dumps(_debug_value(payload), ensure_ascii=False, indent=2),
        flush=True,
    )


def _debug_value(value: Any, *, key: str | None = None) -> Any:
    if key:
        normalized_key = key.lower()

        if "api_key" in normalized_key or "secret" in normalized_key:
            return "<redacted>"

        if normalized_key == "image_base64":
            return f"<base64 image chars={len(value or '')}>"

        if normalized_key in {
            "search_candidates",
            "filtered_candidates",
            "reranked_candidates",
            "best_candidates",
            "selected_products",
            "google_search_results",
        } and isinstance(value, list):
            return _debug_candidate_titles(value)

    if hasattr(value, "model_dump"):
        return _debug_value(value.model_dump())

    if hasattr(value, "dict"):
        return _debug_value(value.dict())

    if isinstance(value, dict):
        return {
            str(item_key): _debug_value(item_value, key=str(item_key))
            for item_key, item_value in value.items()
        }

    if isinstance(value, list):
        max_items = 12
        items = [_debug_value(item) for item in value[:max_items]]
        if len(value) <= max_items:
            return items

        return {
            "count": len(value),
            "items": items,
            "truncated_count": len(value) - max_items,
        }

    if isinstance(value, str):
        return _truncate_for_debug(value)

    if isinstance(value, (int, float, bool)) or value is None:
        return value

    return str(value)


def _debug_candidate_titles(candidates: list[Any]) -> dict[str, Any]:
    titles: list[str] = []

    for candidate in candidates:
        if isinstance(candidate, dict):
            title = candidate.get("title")
        else:
            title = getattr(candidate, "title", None)

        if title:
            titles.append(_truncate_for_debug(str(title), max_length=200))

    return {
        "count": len(candidates),
        "titles": titles,
    }


def _truncate_for_debug(value: str, max_length: int = 1000) -> str:
    if len(value) <= max_length:
        return value

    return f"{value[:max_length]}...<truncated chars={len(value) - max_length}>"


def _model_to_dict(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()

    if hasattr(model, "dict"):
        return model.dict()

    return dict(model)
