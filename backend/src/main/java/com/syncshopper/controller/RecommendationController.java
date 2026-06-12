package com.syncshopper.controller;

import com.syncshopper.common.exception.CustomException;
import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.common.response.ApiResponse;
import com.syncshopper.dto.response.PageResponse;
import com.syncshopper.dto.response.RecommendationHistoryResponse;
import com.syncshopper.dto.response.RecommendationProductResponse;
import com.syncshopper.service.RecommendationService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RequiredArgsConstructor
@RestController
@RequestMapping("/api/recommendations")
@Tag(name = "Recommendation", description = "User recommendation product APIs")
public class RecommendationController {

    private final RecommendationService recommendationService;

    @Operation(summary = "Get my recommendation products")
    @GetMapping("/me")
    public ApiResponse<List<RecommendationProductResponse>> getMyRecommendations(
            @Parameter(description = "Maximum item count", example = "6")
            @RequestParam(defaultValue = "6") int limit
    ) {
        return ApiResponse.success(
                "Recommendations retrieved successfully.",
                recommendationService.getMyRecommendations(currentUserId(), limit)
        );
    }

    @Operation(summary = "Generate rule-based recommendations")
    @PostMapping("/me/rule-based")
    public ApiResponse<List<RecommendationProductResponse>> generateRuleBasedRecommendations(
            @Parameter(description = "Maximum item count", example = "6")
            @RequestParam(defaultValue = "6") int limit
    ) {
        return ApiResponse.success(
                "Rule-based recommendations generated successfully.",
                recommendationService.generateRuleBasedRecommendations(currentUserId(), limit)
        );
    }

    @Operation(summary = "Get my recommendation history")
    @GetMapping("/me/history")
    public ApiResponse<PageResponse<RecommendationHistoryResponse>> getMyRecommendationHistory(
            @Parameter(description = "Page number", example = "1")
            @RequestParam(defaultValue = "1") int page,
            @Parameter(description = "Page size", example = "12")
            @RequestParam(defaultValue = "12") int size
    ) {
        return ApiResponse.success(
                "Recommendation history retrieved successfully.",
                recommendationService.getMyRecommendationHistory(currentUserId(), page, size)
        );
    }

    private Long currentUserId() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication == null || !authentication.isAuthenticated()) {
            throw new CustomException(ErrorCode.UNAUTHORIZED);
        }
        return Long.valueOf(authentication.getName());
    }
}
