from app.schemas.detection_schema import AnalyzeFrameRequest, AnalyzeFrameResponse


def _response_to_dict(response: AnalyzeFrameResponse) -> dict:
    if hasattr(response, "model_dump"):
        return response.model_dump()

    return response.dict()


def _debug_response(request: AnalyzeFrameRequest, response: AnalyzeFrameResponse) -> AnalyzeFrameResponse:
    print(
        "\n[SyncShopper AI Detection Result]\n"
        f"provider=mock video_id={request.video_id} timestamp_sec={request.timestamp_sec} "
        f"subtitle_text={(request.subtitle_text or '')[:300]!r} "
        f"result={_response_to_dict(response)}",
        flush=True,
    )
    return response


def analyze_frame_mock(request: AnalyzeFrameRequest) -> AnalyzeFrameResponse:
    text = f"{request.video_id} {request.subtitle_text or ''}".lower()

    if "nike" in text:
        return _debug_response(request, AnalyzeFrameResponse(
            target_name="Nike sneakers",
            category_name="패션",
            brand="Nike",
            model_name="Air Force 1",
            color="white",
            shape="low-top sneakers",
            logo_text="Nike",
            key_features=["low-top silhouette", "white leather upper", "swoosh logo"],
            confidence=0.91,
        ))

    if "airpods" in text or "apple" in text:
        return _debug_response(request, AnalyzeFrameResponse(
            target_name="Apple AirPods Pro",
            category_name="전자기기",
            brand="Apple",
            model_name="AirPods Pro",
            color="white",
            shape="wireless earbuds case",
            logo_text="Apple",
            key_features=["rounded charging case", "small earbuds", "glossy white finish"],
            confidence=0.89,
        ))

    if "sony" in text or "headphone" in text:
        return _debug_response(request, AnalyzeFrameResponse(
            target_name="Sony wireless headphones",
            category_name="전자기기",
            brand="Sony",
            model_name="WH-1000XM5",
            color="black",
            shape="over-ear headphones",
            logo_text="Sony",
            key_features=["over-ear cups", "padded headband", "minimal matte finish"],
            confidence=0.87,
        ))

    return _debug_response(request, AnalyzeFrameResponse(
        target_name="Unknown product",
        category_name="기타",
        brand=None,
        model_name=None,
        color=None,
        shape=None,
        logo_text=None,
        key_features=[],
        confidence=0.55,
    ))
