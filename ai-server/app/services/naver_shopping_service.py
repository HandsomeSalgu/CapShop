import html
import re
from typing import Any

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.schemas.analysis_graph_schema import ProductCandidate


HTML_TAG_PATTERN = re.compile(r"<[^>]+>")


def search_naver_shopping(query: str, *, display: int = 30) -> list[ProductCandidate]:
    provider = settings.naver_shopping_provider.lower()

    if provider == "backend":
        return _search_backend(query, display=display)

    if provider == "mock":
        return _search_mock(query, display=display)

    raise HTTPException(
        status_code=500,
        detail=f"Unsupported NAVER_SHOPPING_PROVIDER: {settings.naver_shopping_provider}",
    )


def _search_backend(query: str, *, display: int) -> list[ProductCandidate]:
    url = _backend_search_url()
    params = {
        "query": query,
        "display": max(1, min(display, 100)),
        "start": 1,
        "sort": settings.naver_shopping_sort,
    }

    try:
        with httpx.Client(timeout=settings.gms_openai_timeout_sec) as client:
            response = client.get(url, params=params)
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail="Backend commerce search request timed out",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Backend commerce search request failed: {str(exc)}",
        ) from exc

    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"Backend commerce search API error: {response.status_code} {_truncate(response.text)}",
        )

    try:
        response_json = response.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Backend commerce search API returned non-JSON response: {_truncate(response.text)}",
        ) from exc

    if response_json.get("success") is False:
        raise HTTPException(
            status_code=502,
            detail=f"Backend commerce search failed: {response_json.get('message') or 'unknown error'}",
        )

    items = response_json.get("data") or []
    if not isinstance(items, list):
        raise HTTPException(
            status_code=502,
            detail="Backend commerce search response data must be a list",
        )

    return [_candidate_from_backend_item(item) for item in items if isinstance(item, dict)]


def _candidate_from_backend_item(item: dict[str, Any]) -> ProductCandidate:
    product_id = item.get("productId")
    external_product_id = item.get("externalProductId")

    return ProductCandidate(
        title=_clean_text(item.get("title")) or "",
        link=item.get("affiliateUrl"),
        image=item.get("imageUrl"),
        lprice=_to_int(item.get("price")),
        mall_name=_clean_text(item.get("mallName")),
        product_id=str(product_id) if product_id is not None else None,
        external_product_id=str(external_product_id) if external_product_id is not None else None,
        product_type=_clean_text(item.get("source")),
        brand=_clean_text(item.get("brand")),
        category1=_clean_text(item.get("categoryName")),
    )

def _search_mock(query: str, *, display: int) -> list[ProductCandidate]:
    query_lower = query.lower()

    if "airpods" in query_lower or "에어팟" in query_lower or "apple" in query_lower:
        candidates = [
            ProductCandidate(
                title="Apple 에어팟 프로 2세대 USB-C",
                link="https://shopping.example/mock-airpods-pro-2",
                image="https://shopping.example/images/mock-airpods-pro-2.jpg",
                lprice=289000,
                mall_name="Mock Store",
                product_id="mock-airpods-1",
                brand="Apple",
                maker="Apple",
                category1="디지털/가전",
                category2="음향가전",
                category3="이어폰",
                category4="무선이어폰",
            ),
            ProductCandidate(
                title="에어팟 프로 실리콘 케이스 키링 세트",
                link="https://shopping.example/mock-airpods-case",
                image="https://shopping.example/images/mock-airpods-case.jpg",
                lprice=9900,
                mall_name="Mock Accessory",
                product_id="mock-airpods-case",
                brand=None,
                category1="디지털/가전",
                category2="모바일액세서리",
                category3="케이스",
            ),
            ProductCandidate(
                title="Apple AirPods Pro 2 노이즈캔슬링 무선 이어폰",
                link="https://shopping.example/mock-airpods-pro",
                image="https://shopping.example/images/mock-airpods-pro.jpg",
                lprice=295000,
                mall_name="Mock Mall",
                product_id="mock-airpods-2",
                brand="Apple",
                maker="Apple",
                category1="디지털/가전",
                category2="음향가전",
                category3="이어폰",
                category4="블루투스이어폰",
            ),
        ]
    elif "sony" in query_lower or "wh-1000xm5" in query_lower or "헤드폰" in query_lower:
        candidates = [
            ProductCandidate(
                title="SONY WH-1000XM5 무선 노이즈캔슬링 헤드폰 블랙",
                link="https://shopping.example/mock-sony-xm5",
                image="https://shopping.example/images/mock-sony-xm5.jpg",
                lprice=399000,
                mall_name="Mock Store",
                product_id="mock-sony-1",
                brand="Sony",
                maker="Sony",
                category1="디지털/가전",
                category2="음향가전",
                category3="헤드폰",
            ),
            ProductCandidate(
                title="헤드폰 파우치 케이스 보관 가방",
                link="https://shopping.example/mock-headphone-pouch",
                image="https://shopping.example/images/mock-headphone-pouch.jpg",
                lprice=12900,
                mall_name="Mock Accessory",
                product_id="mock-sony-pouch",
                category1="디지털/가전",
                category2="음향기기액세서리",
                category3="파우치",
            ),
            ProductCandidate(
                title="소니 WH-1000XM5 블루투스 헤드셋 플래티넘 실버",
                link="https://shopping.example/mock-sony-xm5-silver",
                image="https://shopping.example/images/mock-sony-xm5-silver.jpg",
                lprice=405000,
                mall_name="Mock Mall",
                product_id="mock-sony-2",
                brand="Sony",
                maker="Sony",
                category1="디지털/가전",
                category2="음향가전",
                category3="헤드폰",
            ),
        ]
    else:
        candidates = [
            ProductCandidate(
                title=f"{query} 정품 상품",
                link="https://shopping.example/mock-product-1",
                image="https://shopping.example/images/mock-product-1.jpg",
                lprice=89000,
                mall_name="Mock Store",
                product_id="mock-product-1",
                category1="패션의류",
                category2="신발",
            ),
            ProductCandidate(
                title=f"{query} 케이스 보호필름 세트",
                link="https://shopping.example/mock-accessory-1",
                image="https://shopping.example/images/mock-accessory-1.jpg",
                lprice=12000,
                mall_name="Mock Accessory",
                product_id="mock-accessory-1",
                category1="액세서리",
                category2="케이스",
            ),
            ProductCandidate(
                title=f"{query} 프리미엄 모델",
                link="https://shopping.example/mock-product-2",
                image="https://shopping.example/images/mock-product-2.jpg",
                lprice=99000,
                mall_name="Mock Mall",
                product_id="mock-product-2",
                category1="패션잡화",
            ),
        ]

    return candidates[:display]


def _backend_search_url() -> str:
    return (
        settings.backend_base_url.rstrip("/")
        + "/"
        + settings.backend_commerce_search_path.lstrip("/")
    )


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None

    cleaned = HTML_TAG_PATTERN.sub("", str(value))
    cleaned = html.unescape(cleaned).strip()
    return cleaned or None


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _truncate(value: str, max_length: int = 500) -> str:
    if len(value) <= max_length:
        return value

    return f"{value[:max_length]}..."
