package com.syncshopper.controller;

import com.syncshopper.common.exception.CustomException;
import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.common.response.ApiResponse;
import com.syncshopper.dto.response.DetectionWebSearchResponse;
import com.syncshopper.service.DetectionWebSearchService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RequiredArgsConstructor
@RestController
@RequestMapping("/api/detection/jobs")
@Tag(name = "Detection Web Search", description = "Detection-based web search APIs")
public class DetectionJobWebSearchController {

    private final DetectionWebSearchService detectionWebSearchService;

    @Operation(summary = "Run web search for a detection job")
    @PostMapping("/{jobId}/web-search")
    public ApiResponse<DetectionWebSearchResponse> searchDetectionJobWeb(@PathVariable Long jobId) {
        return ApiResponse.success(
                "Detection web search completed successfully.",
                detectionWebSearchService.search(currentUserId(), jobId)
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
