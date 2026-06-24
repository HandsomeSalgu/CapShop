import math
from typing import Any

from app.core.config import settings
from app.schemas.analysis_graph_schema import GoogleSearchResult, ProductCandidate
from app.services.google_search_service import search_google_custom
from app.services.graph.candidate_utils import _candidate_key, _copy_candidate, _unique
from app.services.graph.query_helpers import _flatten_source_queries, _google_query_candidates, _query_candidates_by_source
from app.services.graph.search_helpers import _google_result_key, _source_counts
from app.services.graph.state import ShoppingAnalysisState
from app.services.naver_shopping_service import search_naver_source
from app.services.scoring.category_rules import NAVER_SEARCH_SOURCES
from app.services.split_frame_analysis_service import apply_identification_to_frame, identify_from_search


def _naver_search_node(state: ShoppingAnalysisState) -> dict[str, Any]:
    request = state["request"]
    source_queries = state.get("source_queries") or _query_candidates_by_source(state["query"], state["frame_analysis"])
    active_queries = _flatten_source_queries(source_queries)
    limit = request.max_candidates
    tried_queries = _unique([*(state.get("tried_queries") or []), *active_queries])
    active_sources = [source for source in NAVER_SEARCH_SOURCES if source_queries.get(source)]
    per_source_limit = max(3, math.ceil(limit / max(1, len(active_sources))))

    candidates_by_key: dict[str, ProductCandidate] = {}
    source_counts = {source: 0 for source in NAVER_SEARCH_SOURCES}
    for source in active_sources:
        queries = source_queries.get(source) or []
        per_query_display = max(2, min(settings.naver_shopping_display, math.ceil(per_source_limit / len(queries))))

        for query in queries:
            if source_counts[source] >= per_source_limit:
                break

            for candidate in search_naver_source(source, query, display=per_query_display):
                if source_counts[source] >= per_source_limit:
                    break

                enriched_candidate = _copy_candidate(
                    candidate,
                    product_type=candidate.product_type or source,
                    source_query=candidate.source_query or query,
                    query_type=candidate.query_type or source.replace("NAVER_", ""),
                )
                key = _candidate_key(enriched_candidate)
                if key in candidates_by_key:
                    continue

                candidates_by_key[key] = enriched_candidate
                source_counts[source] += 1

    candidates = list(candidates_by_key.values())[:limit]

    return {
        "search_candidates": candidates,
        "tried_queries": tried_queries,
        "source_counts": _source_counts(candidates, source_counts),
    }

def _google_search_node(state: ShoppingAnalysisState) -> dict[str, Any]:
    request = state["request"]
    queries = _google_query_candidates(state)
    if not queries:
        return {
            "google_search_results": [],
            "google_source_counts": {"GOOGLE_CUSTOM_SEARCH": 0},
        }

    limit = min(12, request.max_candidates)
    per_query_display = max(1, min(settings.google_custom_search_display, math.ceil(limit / len(queries))))
    results_by_key: dict[str, GoogleSearchResult] = {}

    for query in queries:
        if len(results_by_key) >= limit:
            break

        for result in search_google_custom(query, display=per_query_display):
            key = _google_result_key(result)
            if key not in results_by_key:
                results_by_key[key] = result
            if len(results_by_key) >= limit:
                break

    results = list(results_by_key.values())
    return {
        "google_search_results": results,
        "google_source_counts": {"GOOGLE_CUSTOM_SEARCH": len(results)},
    }

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
