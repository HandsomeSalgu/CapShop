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

    public List<RecommendationProductResponse> getMyRecommendations(Long userId, int limit) {
        int normalizedLimit = normalizeLimit(limit);
        List<RecommendationProductResponse> recommendations =
                recommendationMapper.findLatestRecommendations(userId, normalizedLimit);

        if (!recommendations.isEmpty()) {
            return recommendations;
        }

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
