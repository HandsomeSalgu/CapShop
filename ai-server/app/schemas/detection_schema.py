from typing import List, Optional

from pydantic import BaseModel, Field


class AnalyzeFrameRequest(BaseModel):
    video_id: str = Field(
        ...,
        description="YouTube video ID",
        examples=["youtube-video-id-123"],
    )
    timestamp_sec: int = Field(
        ...,
        ge=0,
        description="Timestamp in seconds",
        examples=[135],
    )
    image_base64: str = Field(
        ...,
        description="Captured image as base64 data URL",
        examples=["data:image/png;base64,iVBORw0KGgoAAA..."],
    )
    subtitle_text: Optional[str] = Field(
        None,
        description="Subtitle or surrounding text",
        examples=["오늘은 Nike 운동화를 소개합니다."],
    )


class AnalyzeFrameResponse(BaseModel):
    target_name: str
    category_name: str
    brand: Optional[str] = None
    model_name: Optional[str] = None
    color: Optional[str] = None
    shape: Optional[str] = None
    logo_text: Optional[str] = None
    key_features: List[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)
