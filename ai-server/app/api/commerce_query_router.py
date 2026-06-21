from fastapi import APIRouter

from app.schemas.commerce_query_schema import CommerceQueryRequest, CommerceQueryResponse
from app.services.commerce_query_service import generate_commerce_query


router = APIRouter()


@router.post("/generate-commerce-query", response_model=CommerceQueryResponse)
def generate_commerce_query_endpoint(request: CommerceQueryRequest):
    return generate_commerce_query(request)
