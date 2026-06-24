from typing import Any

from app.schemas.detection_schema import AnalyzeFrameRequest


VISUAL_SYSTEM_PROMPT = """
You are the visual feature specialist in SyncShopper's product detection graph.

Focus only on the object's visual appearance: product type, category, color, shape, material, style, and distinctive visual features.
Do not trust or transcribe visible text. Do not infer a brand unless it is visually unmistakable from a logo shape.
Return JSON only.

Return JSON with exactly these keys:
{
"product_type": string | null,
"category_name": string | null,
"color": string | null,
"shape": string | null,
"material": string | null,
"style": string | null,
"key_features": string[],
"confidence": number,
"reason": string
}
""".strip()


def build_visual_user_prompt(request: AnalyzeFrameRequest) -> str:
    return (
        "Describe only the purchasable product's visual features in this captured frame area.\n"
        f"video_id={request.video_id} timestamp_sec={request.timestamp_sec} "
        f"subtitle_text={request.subtitle_text or ''}"
    )


def _visual_rerank_messages(content: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "role": "developer",
            "content": (
                "You are a visual product reranker for Naver search results. "
                "Use the reference image and available candidate thumbnails to score similarity from 0.0 to 1.0. "
                "If a candidate image is not attached, estimate conservatively from text metadata. "
                "Return JSON only."
            ),
        },
        {
            "role": "user",
            "content": content,
        },
    ]
