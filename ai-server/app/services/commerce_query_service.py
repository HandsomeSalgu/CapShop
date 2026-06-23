import json
import re
from typing import Any, Optional

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.schemas.commerce_query_schema import CommerceQueryRequest, CommerceQueryResponse


SYSTEM_PROMPT = """
You are a commerce search query generator for SyncShopper.

Your task is to convert visual product detection results into source-specific Korean search queries for Naver Shopping, Image, Blog, Cafe, and Web search.

The most important goal is to preserve as much information as possible from the detection result and translate it into natural Korean search terms.

Rules:

1. Return only one JSON object.
2. Do not include markdown.
3. Do not include explanations outside JSON.
4. Generate one primary_query, source-specific query groups, and fallback_queries.
5. Build short multi-directional queries instead of one over-specific long query.
6. Preserve all useful visual attributes from the detection result, such as product type, category, color, material, shape, style, size, gender style, usage, brand, and model name.
7. Do not remove useful details just to make the query shorter.
8. Every Naver query must be Korean shopping-friendly. Keep literal English only when it is a brand, model name, or visible logo/text needed to identify the product.
9. If brand and model are known, include both in primary_query.
10. If model is unknown but brand is known, use brand + translated product details + translated category.
11. If brand is unknown, use translated product type, color, material, style, and category as much as possible.
12. Do not invent brand names, model names, colors, materials, or styles that are not present or strongly implied in the detection result.
13. Do not include YouTube UI text, browser UI text, captions UI, comments, or unrelated text.
14. Prefer Korean terms commonly used in Korean shopping searches.
15. Treat logo_text as a visible-text candidate, not as guaranteed truth. Include quoted and unquoted variants when useful.
16. Do not use English common product words such as t-shirt, sports jersey, graphic, orange, short sleeve, or print in Naver queries; translate them to Korean.
17. Include query groups with different directions:

    * exact_text_queries: visible text/logo focused queries such as "MEN MAN 티셔츠" or "\"MEN MAN\" 반팔티"
    * visual_queries: color/style/feature queries such as "주황색 그래픽 반팔티"
    * category_queries: category/use-case queries such as "스포츠 저지 반팔 주황"
    * shopping_queries: purchase-intent queries for Naver Shopping
    * image_queries: visual discovery queries for Naver Image
    * blog_queries: review/context queries for Naver Blog
    * cafe_queries: community/context queries for Naver Cafe
    * web_queries: broad web-document queries
    * fallback_queries: broader Korean fallback queries
18. If detection confidence is high, generate more specific queries.
19. If detection confidence is low, generate broader queries and lower query_confidence.
20. query_confidence must be between 0.0 and 1.0.
21. normalized_brand must be the detected brand if known, otherwise null.
22. normalized_model must be the detected model name if known, otherwise null.
23. normalized_category must be the Korean translated category if possible.
24. reason should briefly explain in Korean how the query was generated from the detection result.

Return JSON with exactly these keys:
{
"primary_query": string,
"exact_text_queries": string[],
"visual_queries": string[],
"category_queries": string[],
"shopping_queries": string[],
"image_queries": string[],
"blog_queries": string[],
"cafe_queries": string[],
"web_queries": string[],
"fallback_queries": string[],
"normalized_brand": string | null,
"normalized_model": string | null,
"normalized_category": string | null,
"query_confidence": number,
"reason": string
}

""".strip()


def _build_user_prompt(request: CommerceQueryRequest) -> str:
    return f"""
Create commerce search queries from the following detection result.

Detection Result:
- target_name: {request.target_name or ""}
- category_name: {request.category_name or ""}
- brand: {request.brand or ""}
- model_name: {request.model_name or ""}
- color: {request.color or ""}
- shape: {request.shape or ""}
- logo_text: {request.logo_text or ""}
- key_features: {", ".join(request.key_features or [])}
- confidence: {request.confidence}

Context:
- subtitle_text: {request.subtitle_text or ""}
- video_id: {request.video_id or ""}
- timestamp_sec: {request.timestamp_sec if request.timestamp_sec is not None else ""}

Generate search queries for Naver Shopping, Image, Blog, Cafe, and Web.
Return only valid JSON.
""".strip()


def _extract_json_content(content: str) -> dict[str, Any]:
    cleaned = content.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to parse commerce query response as JSON: {_truncate(content)}",
        ) from exc

    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=502,
            detail="Commerce query response JSON must be an object",
        )

    return parsed


def _normalize_response(data: dict[str, Any], request: CommerceQueryRequest) -> CommerceQueryResponse:
    primary_query = str(data.get("primary_query") or _build_fallback_primary_query(request)).strip()
    if not primary_query:
        primary_query = "상품"
    primary_query = _koreanize_search_query(primary_query, request)

    query_groups = _build_query_groups(data, request, primary_query)

    try:
        query_confidence = float(data.get("query_confidence", request.confidence))
    except (TypeError, ValueError):
        query_confidence = request.confidence

    query_confidence = max(0.0, min(query_confidence, 1.0))

    reason = data.get("reason") or "Detection 결과를 기반으로 Commerce 검색어를 생성했습니다."

    return CommerceQueryResponse(
        primary_query=primary_query,
        exact_text_queries=query_groups["exact_text_queries"],
        visual_queries=query_groups["visual_queries"],
        category_queries=query_groups["category_queries"],
        shopping_queries=query_groups["shopping_queries"],
        image_queries=query_groups["image_queries"],
        blog_queries=query_groups["blog_queries"],
        cafe_queries=query_groups["cafe_queries"],
        web_queries=query_groups["web_queries"],
        fallback_queries=query_groups["fallback_queries"],
        normalized_brand=data.get("normalized_brand"),
        normalized_model=data.get("normalized_model"),
        normalized_category=data.get("normalized_category"),
        query_confidence=query_confidence,
        reason=str(reason).strip(),
    )


def _build_query_groups(
    data: dict[str, Any],
    request: CommerceQueryRequest,
    primary_query: str,
) -> dict[str, list[str]]:
    product = _resolve_product_term(request)
    category = _resolve_category_term(request, product)
    color = _resolve_color_term(request)
    style = _resolve_style_term(request)
    usage = _resolve_usage_term(request)
    english = _resolve_english_query(request, color, style, product)
    visible_texts = _visible_text_candidates(request.logo_text)

    exact_defaults: list[str] = []
    for visible_text in visible_texts:
        exact_defaults.extend([
            f"{visible_text} {product}",
            f"\"{visible_text}\" {product}",
            f"{visible_text} {category}",
        ])

    visual_defaults = _compact_queries([
        _join_query(color, style, product),
        _join_query(color, "그래픽", product),
        _join_query(color, "프린트", product),
        _join_query(color, usage, product),
    ])
    category_defaults = _compact_queries([
        _join_query(category, color),
        _join_query("스포츠", "저지", color) if _looks_sports_item(request) else None,
        _join_query("축구", "유니폼", color) if _looks_sports_item(request) else None,
    ])

    exact_text_queries = _merge_query_lists(data.get("exact_text_queries"), exact_defaults, limit=5, request=request)
    visual_queries = _merge_query_lists(data.get("visual_queries"), visual_defaults, limit=5, request=request)
    category_queries = _merge_query_lists(data.get("category_queries"), category_defaults, limit=5, request=request)

    shopping_queries = _merge_query_lists(
        data.get("shopping_queries"),
        [primary_query, *exact_text_queries, *visual_queries, *category_queries],
        limit=6,
        request=request,
    )
    image_queries = _merge_query_lists(
        data.get("image_queries"),
        [*visual_queries, *exact_text_queries, english],
        limit=6,
        request=request,
    )
    blog_queries = _merge_query_lists(
        data.get("blog_queries"),
        [*_with_suffix(exact_text_queries, "후기"), *_with_suffix(visual_queries, "착용"), *visual_queries],
        limit=5,
        request=request,
    )
    cafe_queries = _merge_query_lists(
        data.get("cafe_queries"),
        [*_with_suffix(exact_text_queries, "정보"), *_with_suffix(visual_queries, "후기"), *visual_queries],
        limit=5,
        request=request,
    )
    web_queries = _merge_query_lists(
        data.get("web_queries"),
        [*exact_text_queries, *category_queries, english, primary_query],
        limit=6,
        request=request,
    )
    fallback_queries = _merge_query_lists(
        data.get("fallback_queries"),
        [*visual_defaults, *category_defaults, english, request.target_name, request.category_name],
        limit=8,
        request=request,
    )

    return {
        "exact_text_queries": exact_text_queries,
        "visual_queries": visual_queries,
        "category_queries": category_queries,
        "shopping_queries": shopping_queries,
        "image_queries": image_queries,
        "blog_queries": blog_queries,
        "cafe_queries": cafe_queries,
        "web_queries": web_queries,
        "fallback_queries": fallback_queries,
    }


def _merge_query_lists(
    value: Any,
    defaults: list[str | None],
    *,
    limit: int,
    request: CommerceQueryRequest | None = None,
) -> list[str]:
    return _compact_queries([
        _koreanize_search_query(query, request)
        for query in [*_as_query_list(value), *defaults]
    ])[:limit]


def _as_query_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    return [str(item).strip() for item in value if item and str(item).strip()]


def _compact_queries(values: list[str | None]) -> list[str]:
    queries: list[str] = []
    seen: set[str] = set()

    for value in values:
        if not value:
            continue

        normalized = re.sub(r"\s+", " ", str(value)).strip()
        if len(normalized) < 2:
            continue

        key = normalized.lower()
        if key in seen:
            continue

        queries.append(normalized)
        seen.add(key)

    return queries


def _join_query(*parts: str | None) -> str | None:
    return " ".join(part.strip() for part in parts if part and part.strip()) or None


def _with_suffix(queries: list[str], suffix: str) -> list[str]:
    return [f"{query} {suffix}" for query in queries if query]


def _koreanize_search_query(
    query: str | None,
    request: CommerceQueryRequest | None = None,
) -> str | None:
    if not query:
        return query

    normalized = re.sub(r"\s+", " ", str(query)).strip()
    if not normalized:
        return None

    replacements = [
        (r"\bshort[- ]?sleeve\b", "반팔"),
        (r"\bt[- ]?shirt\b", "반팔티"),
        (r"\btee\b", "티셔츠"),
        (r"\bshirt\b", "티셔츠"),
        (r"\bsportswear\b", "스포츠웨어"),
        (r"\bsports\b", "스포츠"),
        (r"\bsport\b", "스포츠"),
        (r"\bjersey\b", "저지"),
        (r"\buniform\b", "유니폼"),
        (r"\bsoccer\b", "축구"),
        (r"\bfootball\b", "축구"),
        (r"\bgraphic\b", "그래픽"),
        (r"\bprinted\b", "프린트"),
        (r"\bprint\b", "프린트"),
        (r"\blettering\b", "레터링"),
        (r"\bletter\b", "레터링"),
        (r"\blogo\b", "로고"),
        (r"\breviews?\b", "후기"),
        (r"\binformation\b", "정보"),
        (r"\binfo\b", "정보"),
        (r"\bwearing\b", "착용"),
        (r"\boutfit\b", "코디"),
        (r"\bstyling\b", "코디"),
        (r"\bfashion\b", "패션"),
        (r"\bcrewneck\b", "크루넥"),
        (r"\bcrew neck\b", "크루넥"),
        (r"\bpolyester\b", "폴리에스터"),
        (r"\bfabric\b", "원단"),
        (r"\bmaterial\b", "소재"),
        (r"\borange\b", "주황색"),
        (r"\bred\b", "빨간색"),
        (r"\bblack\b", "검정색"),
        (r"\bwhite\b", "흰색"),
        (r"\bblue\b", "파란색"),
        (r"\bgreen\b", "초록색"),
        (r"\byellow\b", "노란색"),
        (r"\bmen'?s\b", "남성"),
        (r"\bman\b", "남성"),
        (r"\bmale\b", "남성"),
        (r"\bwomen'?s\b", "여성"),
        (r"\bwoman\b", "여성"),
        (r"\bfemale\b", "여성"),
        (r"\bproduct\b", "상품"),
    ]
    for pattern, replacement in replacements:
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)

    normalized = _remove_generic_english_tokens(normalized, request)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if not normalized:
        return "상품"

    return _ensure_korean_query_marker(normalized)


def _ensure_korean_query_marker(query: str) -> str:
    if re.search(r"[가-힣]", query):
        return query

    if re.search(r"[A-Za-z0-9]", query):
        return f"{query} 상품"

    return query


def _remove_generic_english_tokens(
    query: str,
    request: CommerceQueryRequest | None,
) -> str:
    allowed_tokens = _allowed_english_tokens(request)
    tokens = query.split(" ")
    filtered: list[str] = []

    for token in tokens:
        bare = token.strip("\"'.,()[]{}")
        if not re.search(r"[A-Za-z]", bare):
            filtered.append(token)
            continue

        if bare.lower() in allowed_tokens or _looks_like_brand_token(bare):
            filtered.append(token)

    return " ".join(filtered)


def _allowed_english_tokens(request: CommerceQueryRequest | None) -> set[str]:
    values = []
    if request:
        values.extend([
            request.brand,
            request.model_name,
            request.logo_text,
        ])

    allowed: set[str] = set()
    for value in values:
        if not value:
            continue
        allowed.update(token.lower() for token in re.findall(r"[A-Za-z0-9]+", value))
        compact = re.sub(r"[^A-Za-z0-9]+", "", value)
        if compact:
            allowed.add(compact.lower())

    return allowed


def _looks_like_brand_token(token: str) -> bool:
    if len(token) < 2:
        return False
    return token.isupper() or any(char.isdigit() for char in token)


def _visible_text_candidates(value: str | None) -> list[str]:
    if not value:
        return []

    normalized = re.sub(r"\s+", " ", value).strip()
    without_symbols = re.sub(r"[^0-9A-Za-z가-힣 ]+", " ", normalized)
    without_symbols = re.sub(r"\s+", " ", without_symbols).strip()
    compact = without_symbols.replace(" ", "")
    tokens = [token for token in without_symbols.split(" ") if len(token) >= 3]

    return _compact_queries([normalized, without_symbols, compact, *tokens])[:4]


def _resolve_product_term(request: CommerceQueryRequest) -> str:
    haystack = _request_haystack(request)
    if _contains_any(haystack, ["t-shirt", "tee", "shirt", "short sleeve", "반팔", "티셔츠"]):
        return "반팔티"
    if _contains_any(haystack, ["jersey", "저지", "유니폼"]):
        return "저지"
    if _contains_any(haystack, ["sneaker", "shoe", "운동화", "신발"]):
        return "운동화"
    if _contains_any(haystack, ["earbud", "headphone", "이어폰", "헤드폰"]):
        return "이어폰"
    return request.category_name or request.target_name or "상품"


def _resolve_category_term(request: CommerceQueryRequest, product: str) -> str:
    haystack = _request_haystack(request)
    if _looks_sports_item(request):
        return "스포츠 저지"
    if _contains_any(haystack, ["fashion", "shirt", "tee", "의류", "상의"]):
        return "티셔츠"
    return request.category_name or product


def _resolve_color_term(request: CommerceQueryRequest) -> str | None:
    haystack = _request_haystack(request)
    if _contains_any(haystack, ["orange", "주황", "오렌지"]):
        return "주황색"
    if _contains_any(haystack, ["black", "검정", "블랙"]):
        return "검정색"
    if _contains_any(haystack, ["white", "흰색", "화이트"]):
        return "흰색"
    if _contains_any(haystack, ["red", "빨간", "레드"]):
        return "빨간색"
    if _contains_any(haystack, ["blue", "파랑", "블루"]):
        return "파란색"
    return request.color


def _resolve_style_term(request: CommerceQueryRequest) -> str | None:
    haystack = _request_haystack(request)
    if _contains_any(haystack, ["graphic", "print", "printed", "그래픽", "프린트"]):
        return "그래픽"
    if _contains_any(haystack, ["letter", "text", "logo", "레터링", "문구"]):
        return "레터링"
    return None


def _resolve_usage_term(request: CommerceQueryRequest) -> str | None:
    haystack = _request_haystack(request)
    if _looks_sports_item(request):
        return "스포츠"
    if _contains_any(haystack, ["men", "male", "남성"]):
        return "남성용"
    return None


def _resolve_english_query(
    request: CommerceQueryRequest,
    color: str | None,
    style: str | None,
    product: str,
) -> str | None:
    haystack = _request_haystack(request)
    english_parts: list[str] = []

    if _contains_any(haystack, ["orange", "주황", "오렌지"]):
        english_parts.append("orange")
    elif color and re.search(r"[A-Za-z]", color):
        english_parts.append(color)

    if _contains_any(haystack, ["graphic", "print", "그래픽", "프린트"]):
        english_parts.append("graphic")
    elif style and re.search(r"[A-Za-z]", style):
        english_parts.append(style)

    if _looks_sports_item(request):
        english_parts.extend(["sports", "jersey"])
    elif product in {"반팔티", "티셔츠"}:
        english_parts.append("t-shirt")
    elif re.search(r"[A-Za-z]", product):
        english_parts.append(product)

    return _join_query(*english_parts)


def _looks_sports_item(request: CommerceQueryRequest) -> bool:
    return _contains_any(_request_haystack(request), ["sports", "jersey", "soccer", "football", "스포츠", "저지", "유니폼", "축구"])


def _request_haystack(request: CommerceQueryRequest) -> str:
    return " ".join(str(part) for part in [
        request.target_name,
        request.category_name,
        request.brand,
        request.model_name,
        request.color,
        request.shape,
        request.logo_text,
        " ".join(request.key_features or []),
        request.subtitle_text,
    ] if part).lower()


def _contains_any(value: str, terms: list[str]) -> bool:
    return any(term.lower() in value for term in terms)


def _build_fallback_primary_query(request: CommerceQueryRequest) -> str:
    parts: list[str] = []

    if request.brand:
        parts.append(request.brand)

    if request.model_name:
        parts.append(request.model_name)
    elif request.target_name and request.target_name.lower() != "unknown product":
        parts.append(request.target_name)
    elif request.category_name:
        parts.append(request.category_name)
    else:
        parts.append("상품")

    return " ".join(parts).strip()


def _generate_mock_commerce_query(request: CommerceQueryRequest) -> CommerceQueryResponse:
    primary_query = _koreanize_search_query(_build_fallback_primary_query(request) or "상품", request)
    fallback_candidates = [
        request.target_name,
        " ".join(part for part in [request.brand, request.target_name] if part),
        " ".join(part for part in [request.brand, request.category_name] if part),
        request.category_name,
    ]

    fallback_queries = []
    for query in fallback_candidates:
        if query and query.strip() and query.strip() != primary_query and query.strip() not in fallback_queries:
            fallback_queries.append(query.strip())

    query_groups = _build_query_groups(
        {"fallback_queries": fallback_queries},
        request,
        primary_query,
    )

    return _debug_response(request, CommerceQueryResponse(
        primary_query=primary_query,
        exact_text_queries=query_groups["exact_text_queries"],
        visual_queries=query_groups["visual_queries"],
        category_queries=query_groups["category_queries"],
        shopping_queries=query_groups["shopping_queries"],
        image_queries=query_groups["image_queries"],
        blog_queries=query_groups["blog_queries"],
        cafe_queries=query_groups["cafe_queries"],
        web_queries=query_groups["web_queries"],
        fallback_queries=query_groups["fallback_queries"],
        normalized_brand=request.brand,
        normalized_model=request.model_name,
        normalized_category=request.category_name,
        query_confidence=max(0.0, min(request.confidence or 0.7, 1.0)),
        reason="Mock commerce query generated from detection result.",
    ), provider="mock")


def _build_payload(request: CommerceQueryRequest) -> dict[str, Any]:
    return {
        "model": settings.gms_openai_query_model,
        "messages": [
            {
                "role": "developer",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": _build_user_prompt(request),
            },
        ],
        "temperature": 0.2,
    }


def _truncate(value: str, max_length: int = 500) -> str:
    if len(value) <= max_length:
        return value

    return f"{value[:max_length]}..."


def _response_to_dict(response: CommerceQueryResponse) -> dict[str, Any]:
    if hasattr(response, "model_dump"):
        return response.model_dump()

    return response.dict()


def _print_query_debug(
    request: CommerceQueryRequest,
    response: CommerceQueryResponse,
    raw_content: Optional[str] = None,
    parsed: Optional[dict[str, Any]] = None,
    provider: Optional[str] = None,
) -> None:
    debug_payload = {
        "request_detection": {
            "target_name": request.target_name,
            "category_name": request.category_name,
            "brand": request.brand,
            "model_name": request.model_name,
            "confidence": request.confidence,
            "subtitle_text": _truncate(request.subtitle_text or "", 300),
            "video_id": request.video_id,
            "timestamp_sec": request.timestamp_sec,
        },
        "provider": provider or settings.ai_commerce_query_provider,
        "model": settings.gms_openai_query_model,
        "gpt_raw_content": _truncate(raw_content, 2000) if raw_content is not None else None,
        "parsed_query": parsed,
        "normalized_query": _response_to_dict(response),
    }
    print(
        "\n[SyncShopper AI Commerce Query Result]\n"
        + json.dumps(debug_payload, ensure_ascii=False, indent=2),
        flush=True,
    )


def _debug_response(
    request: CommerceQueryRequest,
    response: CommerceQueryResponse,
    provider: Optional[str] = None,
) -> CommerceQueryResponse:
    _print_query_debug(request, response, provider=provider)
    return response


def generate_commerce_query(request: CommerceQueryRequest) -> CommerceQueryResponse:
    provider = settings.ai_commerce_query_provider.lower()

    if provider == "mock":
        return _generate_mock_commerce_query(request)

    if provider != "gpt":
        raise HTTPException(
            status_code=500,
            detail=f"Unsupported AI_COMMERCE_QUERY_PROVIDER: {settings.ai_commerce_query_provider}",
        )

    if not settings.gms_openai_api_key:
        raise HTTPException(
            status_code=500,
            detail="GMS_OPENAI_API_KEY is not configured",
        )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.gms_openai_api_key}",
    }

    try:
        with httpx.Client(timeout=settings.gms_openai_timeout_sec) as client:
            response = client.post(
                settings.gms_openai_chat_completions_url,
                headers=headers,
                json=_build_payload(request),
            )
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail="Commerce query generation request timed out",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Commerce query generation request failed: {str(exc)}",
        ) from exc

    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Commerce query generation API error: {response.status_code} "
                f"url={settings.gms_openai_chat_completions_url} "
                f"model={settings.gms_openai_query_model} {_truncate(response.text)}"
            ),
        )

    try:
        response_json = response.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Commerce query generation API returned non-JSON response: {_truncate(response.text)}",
        ) from exc

    try:
        content = response_json["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unexpected commerce query response format: {_truncate(json.dumps(response_json, ensure_ascii=False))}",
        ) from exc

    parsed = _extract_json_content(content)
    normalized = _normalize_response(parsed, request)
    _print_query_debug(request, normalized, raw_content=content, parsed=parsed)
    return normalized
