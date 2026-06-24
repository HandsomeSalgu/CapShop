import json
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


def build_candidate_judge_messages(
    *,
    detected_product: dict[str, Any],
    ocr_analysis: dict[str, Any] | None,
    visual_analysis: dict[str, Any] | None,
    query: dict[str, Any],
    candidates: list[dict[str, Any]],
    google_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    payload = {
        "detected_product": detected_product,
        "ocr_analysis": ocr_analysis,
        "visual_analysis": visual_analysis,
        "query": query,
        "candidates": candidates,
        "google_results": google_results,
    }
    return [
        {
            "role": "developer",
            "content": (
                "You judge product identity and candidate quality for SyncShopper. "
                "Be conservative. Do not invent exact models. Return JSON only."
            ),
        },
        {
            "role": "user",
            "content": (
                "Resolve identity and judge candidates. Good means at least 3 candidates "
                "match the detected product by brand/model or key visual features.\n"
                f"Input JSON: {json.dumps(payload, ensure_ascii=False, separators=(',', ':'))}\n"
                "Return JSON with exactly these top-level keys: "
                "{\"identification\": {\"target_name\": string, \"category_name\": string, "
                "\"brand\": string | null, \"model_name\": string | null, \"color\": string | null, "
                "\"shape\": string | null, \"logo_text\": string | null, \"key_features\": string[], "
                "\"confidence\": number, \"evidence\": string[], \"reason\": string}, "
                "\"quality\": {\"is_good\": boolean, \"score\": number, "
                "\"enough_similar_count\": number, \"reason\": string}}"
            ),
        },
    ]
