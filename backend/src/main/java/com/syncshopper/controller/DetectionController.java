package com.syncshopper.controller;

import com.syncshopper.common.exception.CustomException;
import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.common.response.ApiResponse;
import com.syncshopper.dto.request.DetectionAnalyzeRequest;
import com.syncshopper.dto.response.DetectionAnalyzeResponse;
import com.syncshopper.dto.response.DetectionDetailResponse;
import com.syncshopper.service.DetectionService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RequiredArgsConstructor
@RestController
@RequestMapping("/api/detections")
@Tag(name = "Detection", description = "Video frame AI detection APIs")
public class DetectionController {

    private final DetectionService detectionService;

    @Operation(summary = "Analyze a video frame")
    @PostMapping("/analyze")
    public ApiResponse<DetectionAnalyzeResponse> analyzeFrame(
            @Valid @RequestBody DetectionAnalyzeRequest request
    ) {
        return ApiResponse.success(
                "Video frame analysis completed successfully.",
                detectionService.analyzeFrame(currentUserId(), request)
        );
    }

    @Operation(summary = "Get detection detail")
    @GetMapping("/{detectionId}")
    public ApiResponse<DetectionDetailResponse> getDetectionDetail(@PathVariable Long detectionId) {
        return ApiResponse.success(
                "Detection result retrieved successfully.",
                detectionService.getDetectionDetail(currentUserId(), detectionId)
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
