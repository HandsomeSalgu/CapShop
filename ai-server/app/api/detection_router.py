from typing import Any

from fastapi import APIRouter, HTTPException

from app.schemas.analysis_graph_schema import ProductCandidate, ShoppingAnalysisRequest, ShoppingAnalysisResponse
from app.schemas.detection_schema import AnalyzeFrameRequest


router = APIRouter()


@router.post("/analyze-frame")
def analyze_frame_endpoint(request: AnalyzeFrameRequest):
    try:
        from app.services.langgraph_analysis_service import analyze_shopping
    except ModuleNotFoundError as exc:
        if exc.name == "langgraph":
            raise HTTPException(
                status_code=500,
                detail="langgraph dependency is not installed. Run pip install -r requirements.txt.",
            ) from exc
        raise

    request_data = request.model_dump() if hasattr(request, "model_dump") else request.dict()
    graph_request = ShoppingAnalysisRequest(**request_data)
    return _to_integrated_response(analyze_shopping(graph_request))


def _to_integrated_response(graph_response: ShoppingAnalysisResponse) -> dict[str, Any]:
    frame_analysis = graph_response.frame_analysis
    frame_payload = frame_analysis.model_dump() if hasattr(frame_analysis, "model_dump") else frame_analysis.dict()

    return {
        **frame_payload,
        "commerce_query": _model_to_dict(graph_response.query),
        "products": [
            _to_commerce_product_payload(product)
            for product in graph_response.selected_products
        ],
        "selected_products": [
            _model_to_dict(product)
            for product in graph_response.selected_products
        ],
        "quality": _model_to_dict(graph_response.quality),
        "searched_products_count": graph_response.searched_products_count,
        "filtered_products_count": graph_response.filtered_products_count,
        "retry_count": graph_response.retry_count,
        "tried_queries": graph_response.tried_queries,
    }


def _to_commerce_product_payload(product: ProductCandidate) -> dict[str, Any]:
    return {
        "productId": _to_int_or_none(product.product_id),
        "title": product.title,
        "brand": product.brand,
        "mallName": product.mall_name,
        "categoryName": _resolve_category_name(product),
        "price": product.lprice,
        "imageUrl": product.image,
        "affiliateUrl": product.link,
        "source": product.product_type or "NAVER",
        "externalProductId": product.external_product_id or product.product_id,
    }


def _resolve_category_name(product: ProductCandidate) -> str | None:
    return product.category4 or product.category3 or product.category2 or product.category1


def _to_int_or_none(value: str | None) -> int | None:
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


def _model_to_dict(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()

    if hasattr(model, "dict"):
        return model.dict()

    return dict(model)
