from typing import List, Optional

from pydantic import BaseModel, Field


class CommerceQueryRequest(BaseModel):
    target_name: Optional[str] = Field(
        None,
        description="Detected product name",
        examples=["Nike sneakers"],
    )
    category_name: Optional[str] = Field(
        None,
        description="Detected product category",
        examples=["패션"],
    )
    brand: Optional[str] = Field(
        None,
        description="Detected brand",
        examples=["Nike"],
    )
    model_name: Optional[str] = Field(
        None,
        description="Detected model name",
        examples=["Air Force 1"],
    )
    color: Optional[str] = Field(None, description="Detected dominant product color")
    shape: Optional[str] = Field(None, description="Detected product shape or silhouette")
    logo_text: Optional[str] = Field(None, description="Visible logo or text on the product")
    key_features: List[str] = Field(
        default_factory=list,
        description="Important visual features detected from the frame",
    )
    confidence: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Detection confidence",
        examples=[0.91],
    )
    subtitle_text: Optional[str] = Field(None, description="Subtitle or surrounding text")
    video_id: Optional[str] = Field(None, description="YouTube video ID")
    timestamp_sec: Optional[int] = Field(None, ge=0, description="Timestamp in seconds")


class CommerceQueryResponse(BaseModel):
    primary_query: str = Field(..., description="Primary search query for commerce API")
    fallback_queries: List[str] = Field(
        default_factory=list,
        description="Fallback search queries",
    )
    normalized_brand: Optional[str] = Field(None, description="Normalized brand name")
    normalized_model: Optional[str] = Field(None, description="Normalized model name")
    normalized_category: Optional[str] = Field(None, description="Normalized product category")
    query_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Query generation confidence",
    )
    reason: str = Field(..., description="Reason for generated query")
