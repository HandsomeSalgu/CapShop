from typing import Any


SEARCH_IDENTIFICATION_PROMPT = """
You are SyncShopper's product identity resolver.

Use OCR candidates, visual features, Naver search snippets, and Google Custom Search snippets to infer what the product most likely is.
Treat OCR text as candidates, not guaranteed truth. Prefer conservative identification over inventing a brand or exact model.
Return JSON only.

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
"confidence": number,
"evidence": string[],
"reason": string
}
""".strip()


def build_result_judge_messages(
    *,
    detected_product: dict[str, Any],
    query: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "role": "developer",
            "content": (
                "You are a product search result quality judge. "
                "Decide whether the current result set is good enough. Return JSON only."
            ),
        },
        {
            "role": "user",
            "content": (
                "Judge these Naver search candidates for the detected product.\n"
                "Good means at least 3 candidates are visually/textually similar enough "
                "and the scores are not weak.\n\n"
                f"Detected product: {detected_product}\n"
                f"Query: {query}\n"
                f"Candidates: {candidates}\n\n"
                "Return JSON with exactly these keys: "
                "{\"is_good\": boolean, \"score\": number, "
                "\"enough_similar_count\": number, \"reason\": string}"
            ),
        },
    ]
