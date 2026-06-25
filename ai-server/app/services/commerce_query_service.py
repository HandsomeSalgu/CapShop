import json
import re
from typing import Any, Optional

from fastapi import HTTPException

from app.core.config import settings
from app.schemas.commerce_query_schema import CommerceQueryRequest, CommerceQueryResponse
from app.services.gemini_client import call_chat_completion
from app.services.prompts.query_prompt import COMMERCE_QUERY_SYSTEM_PROMPT, build_commerce_query_user_prompt


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
    if _brand_query_term(request):
        primary_query = _brand_focused_primary_query(request) or primary_query

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
    style_terms = _resolve_style_terms(request)
    style = style_terms[0] if style_terms else _resolve_style_term(request)
    usage = _resolve_usage_term(request)
    english = _resolve_english_query(request, color, style, product)
    visible_texts = _visible_text_candidates(request.logo_text or request.brand)
    brand = _brand_query_term(request)
    model = _model_query_term(request)

    exact_defaults: list[str] = []
    for visible_text in visible_texts:
        exact_defaults.extend([
            f"{visible_text} {product}",
            f"\"{visible_text}\" {product}",
            f"{visible_text} {category}",
            _join_query(visible_text, style, product),
        ])

    visual_defaults = _compact_queries([
        _join_query(color, style, product),
        *[_join_query(color, term, product) for term in style_terms[1:]],
        *[_join_query(term, product) for term in style_terms],
        _join_query(color, "그래픽", product),
        _join_query(color, "프린트", product),
        _join_query(color, usage, product),
    ])
    category_defaults = _compact_queries([
        _join_query(category, style, product),
        _join_query(category, color),
        _join_query(product, color),
        _join_query(style, product),
        _join_query("스포츠", "저지", color) if _looks_sports_item(request) else None,
        _join_query("축구", "유니폼", color) if _looks_sports_item(request) else None,
    ])

    if brand:
        brand_core = _join_distinct_query_parts([brand, model]) or brand
        exact_defaults = _compact_queries([
            _join_distinct_query_parts([brand_core, product]),
            _join_distinct_query_parts([f"\"{brand_core}\"", product]),
            _join_distinct_query_parts([brand_core, color, product]),
            _join_distinct_query_parts([brand_core, style, product]),
            _join_distinct_query_parts([brand_core, category]),
        ])
        visual_defaults = _compact_queries([
            _join_distinct_query_parts([brand_core, color, style, product]),
            _join_distinct_query_parts([brand_core, color, product]),
            _join_distinct_query_parts([brand_core, style, product]),
            _join_distinct_query_parts([brand_core, product]),
        ])
        category_defaults = _compact_queries([
            _join_distinct_query_parts([brand_core, product]),
            _join_distinct_query_parts([brand_core, category]),
            _join_distinct_query_parts([brand_core, color, product]),
        ])

    exact_value = _brand_scoped_query_value(data.get("exact_text_queries"), brand) if brand else data.get("exact_text_queries")
    visual_value = _brand_scoped_query_value(data.get("visual_queries"), brand) if brand else data.get("visual_queries")
    category_value = _brand_scoped_query_value(data.get("category_queries"), brand) if brand else data.get("category_queries")
    shopping_value = _brand_scoped_query_value(data.get("shopping_queries"), brand) if brand else data.get("shopping_queries")
    image_value = _brand_scoped_query_value(data.get("image_queries"), brand) if brand else data.get("image_queries")
    blog_value = _brand_scoped_query_value(data.get("blog_queries"), brand) if brand else data.get("blog_queries")
    cafe_value = _brand_scoped_query_value(data.get("cafe_queries"), brand) if brand else data.get("cafe_queries")
    web_value = _brand_scoped_query_value(data.get("web_queries"), brand) if brand else data.get("web_queries")
    fallback_value = _brand_scoped_query_value(data.get("fallback_queries"), brand) if brand else data.get("fallback_queries")

    exact_text_queries = _merge_query_lists(exact_value, exact_defaults, limit=5, request=request)
    visual_queries = _merge_query_lists(visual_value, visual_defaults, limit=5, request=request)
    category_queries = _merge_query_lists(category_value, category_defaults, limit=5, request=request)

    shopping_queries = _merge_query_lists(
        shopping_value,
        [primary_query, *exact_text_queries, *visual_queries, *category_queries],
        limit=6,
        request=request,
    )
    image_queries = _merge_query_lists(
        image_value,
        [*visual_queries, *exact_text_queries] if brand else [*visual_queries, *exact_text_queries, english],
        limit=6,
        request=request,
    )
    blog_queries = _merge_query_lists(
        blog_value,
        [*_with_suffix(exact_text_queries, "후기"), *_with_suffix(visual_queries, "착용"), *visual_queries],
        limit=5,
        request=request,
    )
    cafe_queries = _merge_query_lists(
        cafe_value,
        [*_with_suffix(exact_text_queries, "정보"), *_with_suffix(visual_queries, "후기"), *visual_queries],
        limit=5,
        request=request,
    )
    web_queries = _merge_query_lists(
        web_value,
        [*exact_text_queries, *category_queries, primary_query] if brand else [*exact_text_queries, *category_queries, english, primary_query],
        limit=6,
        request=request,
    )
    fallback_queries = _merge_query_lists(
        fallback_value,
        [*exact_defaults, *visual_defaults, *category_defaults] if brand else [*visual_defaults, *category_defaults, english, request.target_name, request.category_name],
        limit=5 if brand else 8,
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


def _brand_scoped_query_value(value: Any, brand: str | None) -> list[str]:
    if not brand:
        return _as_query_list(value)

    brand_tokens = []
    brand_words = [
        token.lower()
        for token in re.findall(r"[0-9A-Za-z\uAC00-\uD7A3]+", brand)
        if len(token.strip()) >= 2
    ]
    normalized_brand = re.sub(r"\s+", " ", brand).strip().lower()
    if normalized_brand:
        brand_tokens.append(normalized_brand)
    compact_brand = re.sub(r"[^0-9A-Za-z\uAC00-\uD7A3]+", "", brand).lower()
    if compact_brand:
        brand_tokens.append(compact_brand)
    if len(brand_words) == 1:
        brand_tokens.extend(brand_words)

    scoped: list[str] = []
    for query in _as_query_list(value):
        normalized = query.lower()
        compact_query = re.sub(r"[^0-9A-Za-z\uAC00-\uD7A3]+", "", query).lower()
        if any(token in normalized or token in compact_query for token in brand_tokens):
            scoped.append(query)

    return scoped


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
        (r"\btan\b", "베이지"),
        (r"\bbeige\b", "베이지"),
        (r"\bolive[- ]?green\b", "올리브 그린"),
        (r"\bdark[- ]?green\b", "진녹색"),
        (r"\bkhaki\b", "카키"),
        (r"\brelaxed[- ]?fit\b", "루즈핏"),
        (r"\bloose[- ]?fit\b", "루즈핏"),
        (r"\bover[- ]?fit\b", "오버핏"),
        (r"\boversized\b", "오버핏"),
        (r"\bv[- ]?neck\b", "브이넥"),
        (r"\bsnap[- ]?button\b", "스냅 버튼"),
        (r"\bsnap\b", "스냅"),
        (r"\bbutton\b", "버튼"),
        (r"\bquilted\b", "퀼팅"),
        (r"\bquilting\b", "퀼팅"),
        (r"\bembroidered\b", "자수"),
        (r"\bembroidery\b", "자수"),
        (r"\bouterwear\b", "아우터"),
        (r"\bjacket\b", "자켓"),
        (r"\bjumper\b", "점퍼"),
        (r"\bcoat\b", "코트"),
        (r"\bcardigan\b", "가디건"),
        (r"\bcasual\b", "캐주얼"),
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
    if _contains_any(haystack, ["button-up", "button up", "button-front", "collared", "long sleeve", "long-sleeve", "\uBC84\uD2BC\uC5C5", "\uCE74\uB77C", "\uAE34\uD314"]):
        return "\uAE34\uD314 \uC154\uCE20" if _contains_any(haystack, ["long sleeve", "long-sleeve", "\uAE34\uD314"]) else "\uC154\uCE20"
    if _contains_any(haystack, ["jacket", "outerwear", "jumper", "coat", "\uC7AC\uD0B7", "\uC790\uCF13", "\uC810\uD37C", "\uC544\uC6B0\uD130"]):
        return "\uC7AC\uD0B7"
    if _contains_any(haystack, ["t-shirt", "tee", "short sleeve", "crew neck", "crewneck", "\uBC18\uD314", "\uD2F0\uC154\uCE20"]):
        return "\uD2F0\uC154\uCE20"
    if _contains_any(haystack, ["shirt", "\uC154\uCE20"]):
        return "\uC154\uCE20"
    if _contains_any(haystack, ["jersey", "\uC800\uC9C0", "\uC720\uB2C8\uD3FC"]):
        return "\uC800\uC9C0"
    if _contains_any(haystack, ["sneaker", "shoe", "\uC6B4\uB3D9\uD654", "\uC2E0\uBC1C"]):
        return "\uC6B4\uB3D9\uD654"
    if _contains_any(haystack, ["earbud", "headphone", "\uC774\uC5B4\uD3F0", "\uD5E4\uB4DC\uD3F0"]):
        return "\uC774\uC5B4\uD3F0"
    return request.category_name or request.target_name or "\uC0C1\uD488"


def _resolve_category_term(request: CommerceQueryRequest, product: str) -> str:
    haystack = _request_haystack(request)
    if _looks_sports_item(request):
        return "\uC2A4\uD3EC\uCE20 \uC800\uC9C0"
    if _contains_any(haystack, ["outerwear", "jacket", "jumper", "coat", "\uC544\uC6B0\uD130", "\uC7AC\uD0B7", "\uC790\uCF13", "\uC810\uD37C", "\uCF54\uD2B8"]):
        return "\uC544\uC6B0\uD130"
    if _contains_any(haystack, ["men", "male", "men\'s", "\uB0A8\uC131"]):
        return "\uB0A8\uC131 \uC758\uB958"
    if _contains_any(haystack, ["fashion", "shirt", "tee", "\uC758\uB958", "\uC154\uCE20", "\uD2F0\uC154\uCE20"]):
        return "\uC758\uB958"
    return request.category_name or product


def _resolve_color_term(request: CommerceQueryRequest) -> str | None:
    haystack = _request_haystack(request)
    if _contains_any(haystack, ["tan", "beige", "\uBCA0\uC774\uC9C0"]):
        return "\uBCA0\uC774\uC9C0"
    if _contains_any(haystack, ["olive green", "olive-green", "올리브 그린", "올리브그린"]):
        return "올리브 그린"
    if _contains_any(haystack, ["khaki", "카키"]):
        return "카키"
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
    if _contains_any(haystack, ["green", "초록", "그린"]):
        return "초록색"
    return request.color


def _resolve_style_term(request: CommerceQueryRequest) -> str | None:
    style_terms = _resolve_style_terms(request)
    if style_terms:
        return style_terms[0]

    haystack = _request_haystack(request)
    if _contains_any(haystack, ["plaid", "checkered", "checked", "check pattern", "tartan", "gingham", "\uCCB4\uD06C", "\uACA9\uC790"]):
        return "\uCCB4\uD06C"
    if _contains_any(haystack, ["graphic", "print", "printed", "그래픽", "프린트"]):
        return "그래픽"
    if _contains_any(haystack, ["letter", "text", "logo", "레터링", "문구"]):
        return "레터링"
    return None


def _resolve_style_terms(request: CommerceQueryRequest) -> list[str]:
    haystack = _request_haystack(request)
    return _compact_queries([
        "\uCCB4\uD06C" if _contains_any(haystack, ["plaid", "checkered", "checked", "check pattern", "tartan", "gingham", "\uCCB4\uD06C", "\uACA9\uC790"]) else None,
        "\uC2A4\uD2B8\uB77C\uC774\uD504" if _contains_any(haystack, ["striped", "stripe pattern", "stripes", "\uC2A4\uD2B8\uB77C\uC774\uD504", "\uC904\uBB34\uB2AC"]) else None,
        "\uD558\uC6B0\uC2A4\uD22C\uC2A4" if _contains_any(haystack, ["houndstooth", "\uD558\uC6B0\uC2A4\uD22C\uC2A4"]) else None,
        "퀼팅" if _contains_any(haystack, ["quilted", "quilting", "퀼팅", "누빔"]) else None,
        "브이넥" if _contains_any(haystack, ["v-neck", "v neck", "브이넥", "v넥"]) else None,
        "스냅 버튼" if _contains_any(haystack, ["snap button", "snap-button", "스냅 버튼", "스냅버튼"]) else None,
        "자수" if _contains_any(haystack, ["embroidered", "embroidery", "자수"]) else None,
        "그래픽" if _contains_any(haystack, ["graphic", "print", "printed", "그래픽", "프린트"]) else None,
        "레터링" if _contains_any(haystack, ["letter", "text", "logo", "레터링", "문구"]) else None,
        "캐주얼" if _contains_any(haystack, ["casual", "캐주얼"]) else None,
        "루즈핏" if _contains_any(haystack, ["relaxed fit", "loose fit", "루즈핏"]) else None,
    ])


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

    if _contains_any(haystack, ["olive green", "olive-green", "올리브 그린", "올리브그린"]):
        english_parts.append("olive green")
    elif _contains_any(haystack, ["orange", "주황", "오렌지"]):
        english_parts.append("orange")
    elif color and re.search(r"[A-Za-z]", color):
        english_parts.append(color)

    if _contains_any(haystack, ["quilted", "quilting", "퀼팅", "누빔"]):
        english_parts.append("quilted")
    elif _contains_any(haystack, ["graphic", "print", "그래픽", "프린트"]):
        english_parts.append("graphic")
    elif style and re.search(r"[A-Za-z]", style):
        english_parts.append(style)

    if _looks_sports_item(request):
        english_parts.extend(["sports", "jersey"])
    elif product == "자켓":
        english_parts.append("jacket")
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
        request.user_hint,
        request.subtitle_text,
    ] if part).lower()


def _contains_any(value: str, terms: list[str]) -> bool:
    if not value:
        return False

    normalized = value.lower()
    for term in terms:
        needle = term.lower().strip()
        if not needle:
            continue
        if re.search(r"[a-z0-9]", needle):
            pattern = r"(?<![a-z0-9])" + re.escape(needle) + r"(?![a-z0-9])"
            if re.search(pattern, normalized):
                return True
        elif needle in normalized:
            return True

    return False


def _clean_query_text(value: str | None) -> str | None:
    if not value:
        return None

    cleaned = re.sub(r"\s+", " ", str(value)).strip()
    return cleaned[:160] or None


def _build_fallback_primary_query(request: CommerceQueryRequest) -> str:
    return _build_rule_based_primary_query(request)


def _build_rule_based_primary_query(request: CommerceQueryRequest) -> str:
    brand = _brand_query_term(request)
    model = _model_query_term(request)
    color = _resolve_color_term(request)
    product = _resolve_product_term(request)
    style_terms = _resolve_style_terms(request)

    if brand:
        brand_primary = _brand_focused_primary_query(request)
        if brand_primary:
            return brand_primary

    parts: list[str] = []

    if brand:
        parts.append(brand)

    if model:
        parts.append(model)

    if color:
        parts.append(color)

    parts.extend(style_terms[:2])

    if product:
        parts.append(product)

    if not parts and request.target_name and request.target_name.lower() != "unknown product":
        parts.append(request.target_name)

    if not parts:
        parts.append(request.category_name or "상품")

    return _join_distinct_query_parts(parts) or "상품"


def _build_rule_based_query_data(request: CommerceQueryRequest) -> dict[str, Any]:
    brand = _brand_query_term(request)
    model = _model_query_term(request)
    color = _resolve_color_term(request)
    product = _resolve_product_term(request)
    category = _resolve_category_term(request, product)
    style_terms = _resolve_style_terms(request)
    primary_query = _build_rule_based_primary_query(request)
    exact_base = _join_distinct_query_parts([brand, model]) or brand or model
    key_style = style_terms[0] if style_terms else None

    exact_text_queries = _compact_queries([
        _join_distinct_query_parts([exact_base, product]),
        _join_distinct_query_parts([f"\"{exact_base}\"" if exact_base else None, product]),
        _join_distinct_query_parts([exact_base, key_style, product]),
        _join_distinct_query_parts([brand, color, product]),
        _join_distinct_query_parts([brand, category]),
    ])
    visual_queries = _compact_queries([
        _join_distinct_query_parts([color, *style_terms[:2], product]),
        _join_distinct_query_parts([color, key_style, product]),
        _join_distinct_query_parts([color, "그래픽", product]),
        _join_distinct_query_parts([color, "자수", product]),
        _join_distinct_query_parts([color, "스냅 버튼", product]),
        _join_distinct_query_parts([color, request.shape, product]),
    ])
    category_queries = _compact_queries([
        _join_distinct_query_parts([category, key_style, product]),
        _join_distinct_query_parts([product, color]),
        _join_distinct_query_parts([key_style, product]),
        _join_distinct_query_parts([category, color]),
    ])
    shopping_queries = _compact_queries([
        primary_query,
        _join_distinct_query_parts([primary_query, "구매"]),
        _join_distinct_query_parts([primary_query, "가격"]),
        *exact_text_queries,
        *visual_queries,
    ])
    image_queries = _compact_queries([
        _join_distinct_query_parts([primary_query, "이미지"]),
        _join_distinct_query_parts([color, key_style, product, "사진"]),
        _join_distinct_query_parts([color, product, "코디"]),
        *visual_queries,
        *exact_text_queries,
    ])
    blog_queries = _compact_queries([
        *_with_suffix(exact_text_queries, "후기"),
        *_with_suffix(visual_queries, "코디"),
        *_with_suffix(category_queries, "추천"),
    ])
    cafe_queries = _compact_queries([
        *_with_suffix(exact_text_queries, "정보"),
        *_with_suffix(visual_queries, "어디서 사나요"),
        *_with_suffix(category_queries, "커뮤니티"),
    ])
    web_queries = _compact_queries([
        primary_query,
        *exact_text_queries,
        *visual_queries,
        *category_queries,
    ])
    fallback_queries = _compact_queries([
        _join_distinct_query_parts([brand, product]),
        _join_distinct_query_parts([brand, category]),
        _join_distinct_query_parts([color, key_style, product]),
        _join_distinct_query_parts([key_style, product]),
        _join_distinct_query_parts([category, product]),
        request.target_name,
        request.category_name,
    ])

    return {
        "primary_query": primary_query,
        "exact_text_queries": exact_text_queries,
        "visual_queries": visual_queries,
        "category_queries": category_queries,
        "shopping_queries": shopping_queries,
        "image_queries": image_queries,
        "blog_queries": blog_queries,
        "cafe_queries": cafe_queries,
        "web_queries": web_queries,
        "fallback_queries": fallback_queries,
        "normalized_brand": request.brand or request.logo_text,
        "normalized_model": request.model_name,
        "normalized_category": category,
        "query_confidence": max(0.0, min(request.confidence or 0.7, 1.0)),
        "reason": "Rule-based commerce query generated from detection result.",
    }


def _brand_query_term(request: CommerceQueryRequest) -> str | None:
    return _first_non_empty(request.brand, request.logo_text)


def _brand_focused_primary_query(request: CommerceQueryRequest) -> str | None:
    brand = _brand_query_term(request)
    if not brand:
        return None

    model = _model_query_term(request)
    color = _resolve_color_term(request)
    product = _resolve_product_term(request)
    style_terms = _resolve_style_terms(request)
    key_style = style_terms[0] if style_terms else None

    if model:
        return _join_distinct_query_parts([brand, model, product])

    return _join_distinct_query_parts([brand, color, key_style, product]) or brand


def _model_query_term(request: CommerceQueryRequest) -> str | None:
    model = request.model_name
    brand = _brand_query_term(request)
    if not model:
        return None
    if brand and model.strip().lower() == brand.strip().lower():
        return None
    return model.strip()


def _first_non_empty(*values: str | None) -> str | None:
    for value in values:
        if value and value.strip():
            return value.strip()
    return None


def _join_distinct_query_parts(parts: list[str | None]) -> str | None:
    values: list[str] = []
    seen: set[str] = set()
    for part in parts:
        if not part:
            continue

        normalized = re.sub(r"\s+", " ", str(part)).strip()
        if not normalized:
            continue

        key = normalized.strip("\"'").lower()
        if key in seen:
            continue

        values.append(normalized)
        seen.add(key)

    return " ".join(values).strip() or None


def generate_rule_based_commerce_query(request: CommerceQueryRequest) -> CommerceQueryResponse:
    data = _build_rule_based_query_data(request)
    normalized = _normalize_response(data, request)
    return _debug_response(request, normalized, provider="rule_based")


def _generate_mock_commerce_query(request: CommerceQueryRequest) -> CommerceQueryResponse:
    primary_query = _koreanize_search_query(_build_fallback_primary_query(request) or "상품", request)
    fallback_candidates = [
        request.user_hint,
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


def _build_messages(request: CommerceQueryRequest) -> list[dict[str, Any]]:
    return [
        {
            "role": "developer",
            "content": COMMERCE_QUERY_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": build_commerce_query_user_prompt(request),
        },
    ]


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
            "user_hint": request.user_hint,
            "subtitle_text": _truncate(request.subtitle_text or "", 300),
            "video_id": request.video_id,
            "timestamp_sec": request.timestamp_sec,
        },
        "provider": provider or settings.ai_commerce_query_provider,
        "model": settings.gemini_query_model,
        "ai_raw_content": _truncate(raw_content, 2000) if raw_content is not None else None,
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

    if provider != "gemini":
        raise HTTPException(
            status_code=500,
            detail=f"Unsupported AI_COMMERCE_QUERY_PROVIDER: {settings.ai_commerce_query_provider}",
        )

    content = call_chat_completion(
        _build_messages(request),
        model=settings.gemini_query_model,
        temperature=0.2,
    )

    parsed = _extract_json_content(content)
    normalized = _normalize_response(parsed, request)
    _print_query_debug(request, normalized, raw_content=content, parsed=parsed)
    return normalized
