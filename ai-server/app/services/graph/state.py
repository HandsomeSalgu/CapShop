from typing import TypedDict

from app.schemas.analysis_graph_schema import (
    GoogleSearchResult,
    OcrAnalysisResult,
    ProductCandidate,
    ResultQuality,
    SearchIdentificationResult,
    ShoppingAnalysisRequest,
    ShoppingAnalysisResponse,
    VisualFeatureAnalysisResult,
)
from app.schemas.commerce_query_schema import CommerceQueryResponse
from app.schemas.detection_schema import AnalyzeFrameResponse


class ShoppingAnalysisState(TypedDict, total=False):
    request: ShoppingAnalysisRequest
    ocr_analysis: OcrAnalysisResult
    visual_analysis: VisualFeatureAnalysisResult
    frame_analysis: AnalyzeFrameResponse
    query: CommerceQueryResponse
    active_queries: list[str]
    source_queries: dict[str, list[str]]
    tried_queries: list[str]
    source_counts: dict[str, int]
    google_search_results: list[GoogleSearchResult]
    google_source_counts: dict[str, int]
    search_identification: SearchIdentificationResult
    search_candidates: list[ProductCandidate]
    filtered_candidates: list[ProductCandidate]
    reranked_candidates: list[ProductCandidate]
    best_candidates: list[ProductCandidate]
    quality: ResultQuality
    retry_count: int
    response: ShoppingAnalysisResponse
