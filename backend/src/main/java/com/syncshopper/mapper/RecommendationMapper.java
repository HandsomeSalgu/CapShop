package com.syncshopper.mapper;

import com.syncshopper.domain.recommendation.Recommendation;
import com.syncshopper.domain.recommendation.RecommendationCandidate;
import com.syncshopper.dto.response.RecommendationHistoryResponse;
import com.syncshopper.dto.response.RecommendationProductResponse;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface RecommendationMapper {

    int insertRecommendation(Recommendation recommendation);

    List<RecommendationProductResponse> findLatestRecommendations(
            @Param("userId") Long userId,
            @Param("limit") int limit
    );

    List<RecommendationHistoryResponse> findRecommendationHistory(
            @Param("userId") Long userId,
            @Param("offset") int offset,
            @Param("size") int size
    );

    long countRecommendationHistory(@Param("userId") Long userId);

    List<RecommendationCandidate> findRuleBasedCandidates(
            @Param("userId") Long userId,
            @Param("limit") int limit
    );

    List<RecommendationCandidate> findFallbackCandidates(@Param("limit") int limit);
}
