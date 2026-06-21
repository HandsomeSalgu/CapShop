package com.syncshopper.controller;

import com.syncshopper.common.response.ApiResponse;
import com.syncshopper.dto.request.AdminUserSearchCondition;
import com.syncshopper.dto.request.UserRoleUpdateRequest;
import com.syncshopper.dto.request.UserStatusUpdateRequest;
import com.syncshopper.dto.response.AdminUserListResponse;
import com.syncshopper.dto.response.PageResponse;
import com.syncshopper.service.AdminUserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springdoc.core.annotations.ParameterObject;
import org.springframework.web.bind.annotation.*;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/admin/users")
@Tag(name = "Admin User", description = "Admin User Management APIs")
// 필요하다면 @PreAuthorize("hasRole('ADMIN')") 등을 추가할 수 있습니다.
// SecurityConfig 설정에 따름
public class AdminUserController {

    private final AdminUserService adminUserService;

    @Operation(summary = "Get user list for admin")
    @GetMapping
    public ApiResponse<PageResponse<AdminUserListResponse>> getUsers(
            @ParameterObject @ModelAttribute AdminUserSearchCondition condition) {
        return ApiResponse.success(adminUserService.getUsers(condition));
    }

    @Operation(summary = "Update user status (ACTIVE, INACTIVE)")
    @PatchMapping("/{userId}/status")
    public ApiResponse<Void> updateUserStatus(
            @PathVariable Long userId,
            @Valid @RequestBody UserStatusUpdateRequest request) {
        adminUserService.updateUserStatus(userId, request.getStatus());
        return ApiResponse.success("User status updated successfully.");
    }

    @Operation(summary = "Update user role (USER, ADMIN)")
    @PatchMapping("/{userId}/role")
    public ApiResponse<Void> updateUserRole(
            @PathVariable Long userId,
            @Valid @RequestBody UserRoleUpdateRequest request) {
        adminUserService.updateUserRole(userId, request.getRole());
        return ApiResponse.success("User role updated successfully.");
    }
}
