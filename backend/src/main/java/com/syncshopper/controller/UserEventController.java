package com.syncshopper.controller;

import com.syncshopper.common.exception.CustomException;
import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.common.response.ApiResponse;
import com.syncshopper.dto.request.ProductDetailViewEventRequest;
import com.syncshopper.dto.response.UserEventResponse;
import com.syncshopper.service.UserEventService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RequiredArgsConstructor
@RestController
@RequestMapping("/api/user-events")
@Tag(name = "User Event", description = "User behavior log APIs")
public class UserEventController {

    private final UserEventService userEventService;

    @Operation(summary = "Save product detail view event")
    @PostMapping("/product-detail-view")
    public ApiResponse<UserEventResponse> createProductDetailViewEvent(
            @Valid @RequestBody ProductDetailViewEventRequest request
    ) {
        return ApiResponse.success(
                "Product detail view event saved.",
                userEventService.createProductDetailViewEvent(currentUserId(), request)
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
