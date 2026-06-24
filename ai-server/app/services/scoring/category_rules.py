import re
from typing import Any

ACCESSORY_HARD_TERMS = [
    "보호필름",
    "강화유리",
    "액정보호",
    "파우치",
    "키링",
    "스트랩",
    "스티커",
    "스킨",
    "거치대",
    "홀더",
    "필름",
    "pouch",
    "film",
    "protector",
    "strap",
    "sticker",
    "holder",
]

ACCESSORY_SOFT_TERMS = ["케이스", "커버", "case", "cover"]

ACCESSORY_TARGET_TERMS = ACCESSORY_HARD_TERMS + ACCESSORY_SOFT_TERMS

CATEGORY_GROUPS = {
    "electronics": [
        "전자",
        "디지털",
        "가전",
        "이어폰",
        "헤드폰",
        "헤드셋",
        "스마트폰",
        "노트북",
        "태블릿",
        "카메라",
        "음향",
        "충전",
        "airpods",
        "headphone",
        "earbuds",
        "laptop",
        "phone",
        "camera",
    ],
    "fashion": [
        "패션",
        "의류",
        "신발",
        "운동화",
        "스니커즈",
        "가방",
        "잡화",
        "모자",
        "지갑",
        "시계",
        "sneakers",
        "shoes",
        "bag",
        "watch",
        "wallet",
    ],
    "beauty": [
        "뷰티",
        "화장품",
        "향수",
        "스킨케어",
        "메이크업",
        "립스틱",
        "쿠션",
        "cosmetics",
        "perfume",
    ],
    "home": [
        "가구",
        "인테리어",
        "생활",
        "주방",
        "침구",
        "조명",
        "의자",
        "테이블",
        "furniture",
        "kitchen",
        "chair",
        "table",
    ],
}

NAVER_SEARCH_SOURCES = [
    "NAVER_SHOPPING",
    "NAVER_IMAGE",
    "NAVER_BLOG",
    "NAVER_CAFE",
    "NAVER_WEB",
]

TEXT_NEGATIVE_TERMS = ["카라", "폴로", "무지", "기본티", "레이어드"]

COLOR_MATCH_TERMS = ["주황", "오렌지", "orange"]

GRAPHIC_MATCH_TERMS = ["그래픽", "프린트", "레터링", "문구", "graphic", "print", "lettering"]

SPORTS_MATCH_TERMS = ["저지", "스포츠", "유니폼", "축구", "jersey", "sports", "uniform", "soccer", "football"]

def _infer_category_group(text: str | None) -> str | None:
    if not text:
        return None

    normalized = text.lower()
    for group, keywords in CATEGORY_GROUPS.items():
        if any(keyword.lower() in normalized for keyword in keywords):
            return group

    return None

def _contains_any(text: str | None, terms: list[str]) -> bool:
    if not text:
        return False

    normalized = text.lower()
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

def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+|[가-힣]+", text.lower())

def _clamp(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0

    return max(0.0, min(number, 1.0))
