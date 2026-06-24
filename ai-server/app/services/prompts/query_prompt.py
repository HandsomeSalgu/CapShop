from typing import Any

from app.schemas.commerce_query_schema import CommerceQueryRequest


COMMERCE_QUERY_SYSTEM_PROMPT = """
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


def build_commerce_query_user_prompt(request: CommerceQueryRequest) -> str:
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


def build_retry_query_messages(
    *,
    detected_product: dict[str, Any],
    previous_query: dict[str, Any],
    tried_queries: list[str],
    quality: dict[str, Any],
    top_candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "role": "developer",
            "content": (
                "You are a source-specific Naver retry query generator. "
                "Generate better Shopping/Image/Blog/Cafe/Web queries when the previous result set was weak. "
                "Return JSON only."
            ),
        },
        {
            "role": "user",
            "content": (
                "Create a new search query for the same detected product.\n"
                "Avoid queries that were already tried. Avoid accessory-focused terms unless "
                "the target product itself is an accessory.\n\n"
                f"Detected product: {detected_product}\n"
                f"Previous query: {previous_query}\n"
                f"Tried queries: {tried_queries}\n"
                f"Quality judgement: {quality}\n"
                f"Top candidates: {top_candidates}\n\n"
                "Return JSON with exactly these keys: "
                "{\"primary_query\": string, \"exact_text_queries\": string[], "
                "\"visual_queries\": string[], \"category_queries\": string[], "
                "\"shopping_queries\": string[], \"image_queries\": string[], "
                "\"blog_queries\": string[], \"cafe_queries\": string[], "
                "\"web_queries\": string[], \"fallback_queries\": string[], "
                "\"normalized_brand\": string | null, \"normalized_model\": string | null, "
                "\"normalized_category\": string | null, \"query_confidence\": number, \"reason\": string}"
            ),
        },
    ]
