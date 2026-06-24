from typing import Any

from app.schemas.analysis_graph_schema import ProductCandidate


def _candidate_key(candidate: ProductCandidate) -> str:
    return (
        candidate.external_product_id
        or candidate.product_id
        or candidate.link
        or f"{candidate.title}:{candidate.mall_name or ''}"
    ).lower()


def _candidate_prompt_id(index: int, candidate: ProductCandidate) -> str:
    return candidate.product_id or f"candidate-{index + 1}"


def _copy_candidate(candidate: ProductCandidate, **updates: Any) -> ProductCandidate:
    if hasattr(candidate, "model_copy"):
        return candidate.model_copy(update=updates)

    return candidate.copy(update=updates)


def _merge_best_candidates(
    existing: list[ProductCandidate],
    new_candidates: list[ProductCandidate],
    *,
    limit: int = 30,
) -> list[ProductCandidate]:
    by_key = {_candidate_key(candidate): candidate for candidate in existing}

    for candidate in new_candidates:
        key = _candidate_key(candidate)
        previous = by_key.get(key)
        if previous is None or candidate.final_score > previous.final_score:
            by_key[key] = candidate

    return sorted(by_key.values(), key=lambda item: item.final_score, reverse=True)[:limit]


def _unique(values: list[str | None]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        if not value:
            continue

        normalized = str(value).strip()
        key = normalized.lower()
        if normalized and key not in seen:
            result.append(normalized)
            seen.add(key)

    return result


def _is_recommendable_product(candidate: ProductCandidate) -> bool:
    return candidate.product_type == "NAVER_SHOPPING" and bool(candidate.link)
