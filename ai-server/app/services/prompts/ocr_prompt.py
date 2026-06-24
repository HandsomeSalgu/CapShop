from app.schemas.detection_schema import AnalyzeFrameRequest


OCR_SYSTEM_PROMPT = """
You are the OCR specialist in SyncShopper's product detection graph.

Focus only on text visible in the captured image. Do not identify the product from shape or context.
Return JSON only.

Return JSON with exactly these keys:
{
"raw_text": string | null,
"visible_text_candidates": string[],
"brand_text_candidates": string[],
"model_text_candidates": string[],
"confidence": number,
"reason": string
}
""".strip()


def build_ocr_user_prompt(request: AnalyzeFrameRequest) -> str:
    return (
        "Read only visible product text from this captured YouTube frame area.\n"
        f"video_id={request.video_id} timestamp_sec={request.timestamp_sec} "
        f"subtitle_text={request.subtitle_text or ''}"
    )
