package com.syncshopper.service;

import com.syncshopper.domain.recommendation.Recommendation;
import com.syncshopper.domain.recommendation.RecommendationCandidate;
import com.syncshopper.domain.recommendation.RecommendationType;
import com.syncshopper.dto.response.RecommendationProductResponse;
import com.syncshopper.mapper.RecommendationMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.Comparator;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

@RequiredArgsConstructor
@Service
public class RuleBasedRecommendationService {

    private static final int DEFAULT_LIMIT = 6;
    private static final int MAX_LIMIT = 20;

    private final RecommendationMapper recommendationMapper;

    @Transactional
    public List<RecommendationProductResponse> generateRuleBasedRecommendations(Long userId, int limit) {
        int normalizedLimit = normalizeLimit(limit);
        List<RecommendationCandidate> candidates = recommendationMapper.findRuleBasedCandidates(userId, normalizedLimit);
        RecommendationType recommendationType = RecommendationType.RULE_BASED;

        if (candidates.isEmpty()) {
            candidates = recommendationMapper.findFallbackCandidates(normalizedLimit);
            recommendationType = RecommendationType.FALLBACK;
        }

        if (candidates.isEmpty()) {
            return List.of();
        }

        RecommendationType finalRecommendationType = recommendationType;
        AtomicInteger rank = new AtomicInteger(1);

        return candidates.stream()
                .sorted(Comparator
                        .comparing((RecommendationCandidate candidate) -> valueOrZero(candidate.getScore())).reversed()
                        .thenComparing(candidate -> valueOrZero(candidate.getReviewCount()), Comparator.reverseOrder())
                        .thenComparing(candidate -> valueOrZero(candidate.getRating()), Comparator.reverseOrder())
                        .thenComparing(RecommendationCandidate::getProductId, Comparator.reverseOrder()))
                .limit(normalizedLimit)
                .map(candidate -> saveRecommendation(userId, candidate, rank.getAndIncrement(), finalRecommendationType))
                .toList();
    }

    private RecommendationProductResponse saveRecommendation(
            Long userId,
            RecommendationCandidate candidate,
            int rankNo,
            RecommendationType recommendationType
    ) {
        Recommendation recommendation = Recommendation.builder()
                .userId(userId)
                .productId(candidate.getProductId())
                .detectionId(null)
                .rankNo(rankNo)
                .score(valueOrZero(candidate.getScore()))
                .reason(candidate.getReason())
                .recommendationType(recommendationType)
                .build();

        recommendationMapper.insertRecommendation(recommendation);

        return RecommendationProductResponse.builder()
                .recommendationId(recommendation.getRecommendationId())
                .productId(candidate.getProductId())
                .title(candidate.getTitle())
                .brand(candidate.getBrand())
                .categoryName(candidate.getCategoryName())
                .price(candidate.getPrice())
                .imageUrl(candidate.getImageUrl())
                .reviewCount(candidate.getReviewCount())
                .rating(candidate.getRating())
                .rankNo(rankNo)
                .score(valueOrZero(candidate.getScore()))
                .reason(candidate.getReason())
                .recommendationType(recommendationType.name())
                .createdAt(LocalDateTime.now())
                .build();
    }

    private int normalizeLimit(int limit) {
        if (limit < 1) {
            return DEFAULT_LIMIT;
        }
        return Math.min(limit, MAX_LIMIT);
    }

    private double valueOrZero(Double value) {
        return value == null ? 0.0 : value;
    }

    private int valueOrZero(Integer value) {
        return value == null ? 0 : value;
    }
}
