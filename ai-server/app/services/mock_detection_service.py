from app.schemas.detection_schema import AnalyzeFrameRequest, AnalyzeFrameResponse


def analyze_frame_mock(request: AnalyzeFrameRequest) -> AnalyzeFrameResponse:
    text = f"{request.video_id} {request.subtitle_text or ''}".lower()

    if "nike" in text:
        return AnalyzeFrameResponse(
            target_name="Nike sneakers",
            category_name="패션",
            brand="Nike",
            model_name="Air Force 1",
            confidence=0.91,
        )

    if "airpods" in text or "apple" in text:
        return AnalyzeFrameResponse(
            target_name="Apple AirPods Pro",
            category_name="전자기기",
            brand="Apple",
            model_name="AirPods Pro",
            confidence=0.89,
        )

    if "sony" in text or "headphone" in text:
        return AnalyzeFrameResponse(
            target_name="Sony wireless headphones",
            category_name="전자기기",
            brand="Sony",
            model_name="WH-1000XM5",
            confidence=0.87,
        )

    return AnalyzeFrameResponse(
        target_name="Unknown product",
        category_name="기타",
        brand=None,
        model_name=None,
        confidence=0.55,
    )
