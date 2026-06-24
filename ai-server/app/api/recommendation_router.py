from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from app.db.session import get_db
from app.db.repository import get_user_events_with_products
from app.recommendation.keyword_extractor import extract_keywords_for_user

router = APIRouter()

class KeywordRecommendationResponse(BaseModel):
    user_id: int
    keywords: List[str]
    reason: str

@router.get("/recommendations/{user_id}", response_model=KeywordRecommendationResponse)
def get_recommendations(user_id: int, db: Session = Depends(get_db)):
    """
    Fetches the user's recent interactions and returns personalized search keywords using TF-IDF.
    """
    try:
        df = get_user_events_with_products(db, user_id)
        
        if df.empty:
            return KeywordRecommendationResponse(
                user_id=user_id,
                keywords=["스마트기기", "패션", "가전"], # Default fallback keywords
                reason="추천을 위한 최근 활동 데이터가 부족하여 기본 인기 키워드를 추천합니다."
            )
            
        keywords = extract_keywords_for_user(df, top_n=3)
        
        if not keywords:
            return KeywordRecommendationResponse(
                user_id=user_id,
                keywords=["스마트기기", "패션", "가전"],
                reason="키워드 추출에 실패하여 기본 인기 키워드를 추천합니다."
            )
            
        return KeywordRecommendationResponse(
            user_id=user_id,
            keywords=keywords,
            reason=f"최근 조회하신 상품들을 분석하여 '{', '.join(keywords)}' 관련 상품을 추천합니다."
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
