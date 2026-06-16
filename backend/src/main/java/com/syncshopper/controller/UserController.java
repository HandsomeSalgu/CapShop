package com.syncshopper.controller;

import com.syncshopper.common.exception.CustomException;
import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.common.response.ApiResponse;
import com.syncshopper.dto.request.PasswordChangeRequest;
import com.syncshopper.dto.request.PasswordVerifyRequest;
import com.syncshopper.dto.request.UserProfileUpdateRequest;
import com.syncshopper.dto.response.UserProfileResponse;
import com.syncshopper.service.UserProfileService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RequiredArgsConstructor
@RestController
@RequestMapping("/api/users")
@Tag(name = "User Profile", description = "User my page profile APIs")
public class UserController {

    private final UserProfileService userProfileService;

    @Operation(summary = "Get my profile")
    @GetMapping("/me")
    public ApiResponse<UserProfileResponse> getMyProfile() {
        return ApiResponse.success("Profile fetched.", userProfileService.getMyProfile(currentUserId()));
    }

    @Operation(summary = "Update my profile")
    @PatchMapping("/me")
    public ApiResponse<UserProfileResponse> updateMyProfile(
            @Valid @RequestBody UserProfileUpdateRequest request
    ) {
        return ApiResponse.success("Profile updated.", userProfileService.updateMyProfile(currentUserId(), request));
    }

    @Operation(summary = "Change my password")
    @PatchMapping("/me/password")
    public ApiResponse<Void> changePassword(@Valid @RequestBody PasswordChangeRequest request) {
        userProfileService.changePassword(currentUserId(), request);
        return ApiResponse.success("Password changed.");
    }

    @Operation(summary = "Verify my password")
    @PostMapping("/me/password/verify")
    public ApiResponse<Boolean> verifyPassword(@Valid @RequestBody PasswordVerifyRequest request) {
        boolean isMatch = userProfileService.verifyPassword(currentUserId(), request.getPassword());
        if (!isMatch) {
            return ApiResponse.success("Password does not match.", false);
        }
        return ApiResponse.success("Password verified.", true);
    }

    private Long currentUserId() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication == null || !authentication.isAuthenticated()) {
            throw new CustomException(ErrorCode.UNAUTHORIZED);
        }
        return Long.valueOf(authentication.getName());
    }
}
