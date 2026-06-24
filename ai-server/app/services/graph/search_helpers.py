from app.schemas.analysis_graph_schema import GoogleSearchResult, ProductCandidate
from app.services.scoring.category_rules import NAVER_SEARCH_SOURCES


def _source_counts(
    candidates: list[ProductCandidate],
    fallback_counts: dict[str, int] | None = None,
) -> dict[str, int]:
    counts = {source: 0 for source in NAVER_SEARCH_SOURCES}
    if fallback_counts:
        counts.update({source: 0 for source in fallback_counts})

    for candidate in candidates:
        source = candidate.product_type or "UNKNOWN"
        counts[source] = counts.get(source, 0) + 1

    return counts


def _google_result_key(result: GoogleSearchResult) -> str:
    return (result.link or f"{result.title}:{result.display_link or ''}").lower()
