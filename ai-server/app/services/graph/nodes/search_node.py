import math
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

from app.core.config import settings
from app.schemas.analysis_graph_schema import GoogleSearchResult, ProductCandidate
from app.services.gemini_grounded_search_service import (
    GEMINI_GROUNDED_SEARCH_SOURCE,
    search_gemini_grounded_products,
)
from app.services.graph.candidate_utils import _candidate_key, _copy_candidate, _unique
from app.services.graph.query_helpers import _flatten_source_queries, _google_query_candidates, _query_candidates_by_source
from app.services.graph.search_helpers import _google_result_key, _source_counts
from app.services.graph.state import ShoppingAnalysisState
from app.services.naver_shopping_service import search_naver_source
from app.services.scoring.category_rules import NAVER_SEARCH_SOURCES
from app.services.split_frame_analysis_service import apply_identification_to_frame, identify_from_search


@dataclass(frozen=True)
class _NaverSearchTask:
    source: str
    query: str
    display: int


def _naver_search_node(state: ShoppingAnalysisState) -> dict[str, Any]:
    request = state["request"]
    source_queries = state.get("source_queries") or _query_candidates_by_source(state["query"], state["frame_analysis"])
    active_queries = _flatten_source_queries(source_queries)
    limit = request.max_candidates
    tried_queries = _unique([*(state.get("tried_queries") or []), *active_queries])
    active_sources = [source for source in NAVER_SEARCH_SOURCES if source_queries.get(source)]
    per_source_limit = max(3, math.ceil(limit / max(1, len(active_sources))))

    search_tasks: list[_NaverSearchTask] = []
    for source in active_sources:
        queries = source_queries.get(source) or []
        per_query_display = max(2, min(settings.naver_shopping_display, math.ceil(per_source_limit / len(queries))))

        for query in queries:
            search_tasks.append(_NaverSearchTask(source=source, query=query, display=per_query_display))

    task_results = _run_naver_search_tasks(search_tasks)

    candidates_by_key: dict[str, ProductCandidate] = {}
    source_counts = {source: 0 for source in NAVER_SEARCH_SOURCES}
    for task in search_tasks:
        if len(candidates_by_key) >= limit:
            break

        if source_counts[task.source] >= per_source_limit:
            continue

        for candidate in task_results.get(task, []):
            if len(candidates_by_key) >= limit:
                break

            if source_counts[task.source] >= per_source_limit:
                break

            enriched_candidate = _copy_candidate(
                candidate,
                product_type=candidate.product_type or task.source,
                source_query=candidate.source_query or task.query,
                query_type=candidate.query_type or task.source.replace("NAVER_", ""),
            )
            key = _candidate_key(enriched_candidate)
            if key in candidates_by_key:
                continue

            candidates_by_key[key] = enriched_candidate
            source_counts[task.source] += 1

    candidates = list(candidates_by_key.values())[:limit]

    return {
        "search_candidates": candidates,
        "tried_queries": tried_queries,
        "source_counts": _source_counts(candidates, source_counts),
    }


def _run_naver_search_tasks(search_tasks: list[_NaverSearchTask]) -> dict[_NaverSearchTask, list[ProductCandidate]]:
    if not search_tasks:
        return {}

    max_workers = max(1, settings.naver_search_max_workers)
    results: dict[_NaverSearchTask, list[ProductCandidate]] = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            task: executor.submit(search_naver_source, task.source, task.query, display=task.display)
            for task in search_tasks
        }

        for task, future in futures.items():
            try:
                results[task] = future.result()
            except Exception as exc:
                results[task] = []
                print(
                    "\n[SyncShopper Naver Search] "
                    f"failed source={task.source} query='{task.query}' "
                    f"error_type={exc.__class__.__name__} message={str(exc)}",
                    flush=True,
                )

    return results


def _google_search_node(state: ShoppingAnalysisState) -> dict[str, Any]:
    existing_candidates = state.get("search_candidates") or []
    if len(existing_candidates) >= settings.skip_gemini_min_candidates:
        print(
            "\n[SyncShopper Gemini Grounded Search] "
            "skipped because Naver candidates are enough "
            f"count={len(existing_candidates)} threshold={settings.skip_gemini_min_candidates}",
            flush=True,
        )
        return {
            "search_candidates": existing_candidates,
            "google_search_results": [],
            "source_counts": state.get("source_counts") or {},
            "google_source_counts": {GEMINI_GROUNDED_SEARCH_SOURCE: 0},
        }

    request = state["request"]
    queries = _google_query_candidates(state)
    if not queries:
        return {
            "search_candidates": existing_candidates,
            "google_search_results": [],
            "source_counts": state.get("source_counts") or {},
            "google_source_counts": {GEMINI_GROUNDED_SEARCH_SOURCE: 0},
        }

    limit = min(12, request.max_candidates)
    per_query_display = max(1, min(settings.google_custom_search_display, math.ceil(limit / len(queries))))
    candidates_by_key: dict[str, ProductCandidate] = {
        _candidate_key(candidate): candidate
        for candidate in existing_candidates
    }
    gemini_candidates: list[ProductCandidate] = []
    results_by_key: dict[str, GoogleSearchResult] = {}

    for query in queries:
        if len(gemini_candidates) >= limit:
            break

        for candidate in search_gemini_grounded_products(query, display=per_query_display):
            key = _candidate_key(candidate)
            if key in candidates_by_key:
                continue

            candidates_by_key[key] = candidate
            gemini_candidates.append(candidate)

            result = _gemini_candidate_to_google_result(candidate)
            result_key = _google_result_key(result)
            if result_key not in results_by_key:
                results_by_key[result_key] = result

            if len(gemini_candidates) >= limit:
                break

    results = list(results_by_key.values())
    source_counts = dict(state.get("source_counts") or {})
    source_counts[GEMINI_GROUNDED_SEARCH_SOURCE] = len(gemini_candidates)

    return {
        "search_candidates": list(candidates_by_key.values()),
        "google_search_results": results,
        "source_counts": source_counts,
        "google_source_counts": {GEMINI_GROUNDED_SEARCH_SOURCE: len(gemini_candidates)},
    }


def _gemini_candidate_to_google_result(candidate: ProductCandidate) -> GoogleSearchResult:
    return GoogleSearchResult(
        title=candidate.title,
        link=candidate.link,
        display_link=_display_link(candidate.link),
        snippet=candidate.snippet or candidate.reason,
        image=candidate.image or candidate.thumbnail,
        source_query=candidate.source_query,
    )


def _display_link(url: str | None) -> str | None:
    if not url:
        return None

    from urllib.parse import urlparse

    parsed = urlparse(url)
    return parsed.netloc or None


def _search_identifier_node(state: ShoppingAnalysisState) -> dict[str, Any]:
    identification = identify_from_search(
        state["frame_analysis"],
        state.get("ocr_analysis"),
        state.get("visual_analysis"),
        state.get("search_candidates") or [],
        state.get("google_search_results") or [],
    )
    refined_frame_analysis = apply_identification_to_frame(state["frame_analysis"], identification)
    return {
        "search_identification": identification,
        "frame_analysis": refined_frame_analysis,
    }
