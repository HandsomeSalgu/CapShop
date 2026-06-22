from typing import List, Optional

from pydantic import BaseModel, Field

from app.core.config import settings
from app.schemas.commerce_query_schema import CommerceQueryResponse
from app.schemas.detection_schema import AnalyzeFrameRequest, AnalyzeFrameResponse


class ShoppingAnalysisRequest(AnalyzeFrameRequest):
    max_candidates: int = Field(
        30,
        ge=20,
        le=50,
        description="Number of product candidates to collect before filtering",
    )
    max_retries: int = Field(
        settings.analysis_max_retries,
        ge=0,
        le=3,
        description="How many times the graph can regenerate queries when quality is low",
    )


class ProductCandidate(BaseModel):
    title: str
    link: Optional[str] = None
    image: Optional[str] = None
    lprice: Optional[int] = None
    hprice: Optional[int] = None
    mall_name: Optional[str] = None
    product_id: Optional[str] = None
    external_product_id: Optional[str] = None
    product_type: Optional[str] = None
    brand: Optional[str] = None
    maker: Optional[str] = None
    category1: Optional[str] = None
    category2: Optional[str] = None
    category3: Optional[str] = None
    category4: Optional[str] = None
    text_score: float = Field(0.0, ge=0.0, le=1.0)
    visual_score: float = Field(0.0, ge=0.0, le=1.0)
    final_score: float = Field(0.0, ge=0.0, le=1.0)
    filter_reason: Optional[str] = None
    visual_reason: Optional[str] = None


class ResultQuality(BaseModel):
    is_good: bool
    score: float = Field(..., ge=0.0, le=1.0)
    enough_similar_count: int = Field(..., ge=0)
    reason: str


class ShoppingAnalysisResponse(BaseModel):
    frame_analysis: AnalyzeFrameResponse
    query: CommerceQueryResponse
    selected_products: List[ProductCandidate] = Field(default_factory=list)
    searched_products_count: int = Field(..., ge=0)
    filtered_products_count: int = Field(..., ge=0)
    quality: ResultQuality
    retry_count: int = Field(..., ge=0)
    tried_queries: List[str] = Field(default_factory=list)
