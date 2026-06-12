package com.syncshopper.controller;

import com.syncshopper.common.exception.CustomException;
import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.common.response.ApiResponse;
import com.syncshopper.dto.response.PageResponse;
import com.syncshopper.dto.response.ViewHistoryResponse;
import com.syncshopper.service.ViewHistoryService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RequiredArgsConstructor
@RestController
@RequestMapping("/api/users/me/view-history")
@Tag(name = "View History", description = "Recently viewed product APIs")
public class ViewHistoryController {

    private final ViewHistoryService viewHistoryService;

    @Operation(summary = "Get my recently viewed products")
    @GetMapping
    public ApiResponse<PageResponse<ViewHistoryResponse>> getMyViewHistory(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "12") int size
    ) {
        return ApiResponse.success(
                "View history retrieved successfully.",
                viewHistoryService.getMyViewHistory(currentUserId(), page, size)
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
