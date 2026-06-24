package com.syncshopper.service;

import com.syncshopper.dto.response.PageResponse;
import com.syncshopper.dto.response.RecommendationHistoryResponse;
import com.syncshopper.dto.response.RecommendationProductResponse;
import com.syncshopper.mapper.RecommendationMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@RequiredArgsConstructor
@Service
public class RecommendationService {

    private static final int DEFAULT_LIMIT = 6;
    private static final int MAX_LIMIT = 20;
    private static final int DEFAULT_PAGE = 1;
    private static final int DEFAULT_SIZE = 12;
    private static final int MAX_SIZE = 50;

    private final RecommendationMapper recommendationMapper;
    private final RuleBasedRecommendationService ruleBasedRecommendationService;
    private final org.springframework.data.redis.core.RedisTemplate<String, Object> redisTemplate;
    private final NaverShoppingClient naverShoppingClient;

    public List<RecommendationProductResponse> getMyRecommendations(Long userId, int limit) {
        int normalizedLimit = normalizeLimit(limit);
        
        // 1. Redis에서 유저의 상위 키워드 문자열 조회
        String redisKey = "user:" + userId + ":recommend_keywords";
        String cachedKeywords = (String) redisTemplate.opsForValue().get(redisKey);
        List<String> keywords = null;
        
        if (cachedKeywords != null && !cachedKeywords.trim().isEmpty()) {
            keywords = java.util.Arrays.asList(cachedKeywords.split(","));
        }
        
        // 2. Redis에 없으면 실시간 1회 조회 (Fallback)
        if (keywords == null || keywords.isEmpty()) {
            List<com.syncshopper.domain.recommendation.UserKeywordScore> topKeywords = 
                    recommendationMapper.findTopKeywordsByUserId(userId, 3);
            if (topKeywords != null && !topKeywords.isEmpty()) {
                keywords = topKeywords.stream()
                        .map(com.syncshopper.domain.recommendation.UserKeywordScore::getKeyword)
                        .toList();
                // Redis에 캐싱 (Jackson 제네릭 에러 방지용 단일 String 변환)
                String joinedKeywords = String.join(",", keywords);
                redisTemplate.opsForValue().set(redisKey, joinedKeywords, 2, java.util.concurrent.TimeUnit.HOURS);
            }
        }

        // 3. 네이버 API 호출하여 실시간 상품 반환
        if (keywords != null && !keywords.isEmpty()) {
            List<RecommendationProductResponse> results = new java.util.ArrayList<>();
            int countPerKeyword = Math.max(1, normalizedLimit / keywords.size());
            
            for (String keyword : keywords) {
                com.syncshopper.dto.response.NaverShoppingSearchResponse searchResponse = 
                        naverShoppingClient.search(keyword, countPerKeyword, 1, "sim");
                
                if (searchResponse != null && searchResponse.getItems() != null) {
                    for (com.syncshopper.dto.response.NaverShoppingItemResponse item : searchResponse.getItems()) {
                        results.add(RecommendationProductResponse.builder()
                                .externalProductId(item.getProductId())
                                .title(item.getTitle())
                                .brand(item.getBrand())
                                .categoryName(item.getCategory3() != null ? item.getCategory3() : item.getCategory2())
                                .price(item.getLprice() != null ? Integer.parseInt(item.getLprice()) : 0)
                                .imageUrl(item.getImage())
                                .link(item.getLink())
                                .recommendationType("AI_SEARCH")
                                .reason("사용자 최근 관심 키워드 '" + keyword + "' 기반 실시간 추천입니다.")
                                .build());
                    }
                }
            }
            if (!results.isEmpty()) {
                // 필요하다면 limit 개수만큼 자르기
                return results.size() > normalizedLimit ? results.subList(0, normalizedLimit) : results;
            }
        }

        // 4. 모든 방법 실패 시 (콜드 스타트조차 없는 극단적 경우) Rule-based Fallback
        return ruleBasedRecommendationService.generateRuleBasedRecommendations(userId, normalizedLimit);
    }

    public List<RecommendationProductResponse> generateRuleBasedRecommendations(Long userId, int limit) {
        return ruleBasedRecommendationService.generateRuleBasedRecommendations(userId, limit);
    }

    public PageResponse<RecommendationHistoryResponse> getMyRecommendationHistory(Long userId, int page, int size) {
        PageRequest pageRequest = normalizePage(page, size);
        long totalCount = recommendationMapper.countRecommendationHistory(userId);
        List<RecommendationHistoryResponse> recommendations = recommendationMapper.findRecommendationHistory(
                userId,
                pageRequest.offset(),
                pageRequest.size()
        );

        return PageResponse.of(recommendations, pageRequest.page(), pageRequest.size(), totalCount);
    }

    private int normalizeLimit(int limit) {
        if (limit < 1) {
            return DEFAULT_LIMIT;
        }
        return Math.min(limit, MAX_LIMIT);
    }

    private PageRequest normalizePage(int page, int size) {
        int normalizedPage = page < 1 ? DEFAULT_PAGE : page;
        int normalizedSize = size < 1 ? DEFAULT_SIZE : Math.min(size, MAX_SIZE);
        return new PageRequest(normalizedPage, normalizedSize, (normalizedPage - 1) * normalizedSize);
    }

    private record PageRequest(int page, int size, int offset) {
    }
}
