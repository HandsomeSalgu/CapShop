package com.syncshopper.controller;

import com.syncshopper.common.exception.CustomException;
import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.common.response.ApiResponse;
import com.syncshopper.dto.response.PageResponse;
import com.syncshopper.dto.response.WishlistProductResponse;
import com.syncshopper.service.WishlistService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RequiredArgsConstructor
@RestController
@RequestMapping("/api/users/me/wishlist")
@Tag(name = "Wishlist", description = "User wishlist APIs")
public class WishlistController {

    private final WishlistService wishlistService;

    @Operation(summary = "Get my wishlist")
    @GetMapping
    public ApiResponse<PageResponse<WishlistProductResponse>> getMyWishlist(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "12") int size
    ) {
        return ApiResponse.success(
                "Wishlist retrieved successfully.",
                wishlistService.getMyWishlist(currentUserId(), page, size)
        );
    }

    @Operation(summary = "Add product to my wishlist")
    @PostMapping("/{productId}")
    public ApiResponse<Void> addWishlist(
            @PathVariable Long productId,
            @RequestParam(defaultValue = "UNKNOWN") String sourcePage
    ) {
        wishlistService.addWishlist(currentUserId(), productId, sourcePage);
        return ApiResponse.success("Wishlist added successfully.");
    }

    @Operation(summary = "Remove product from my wishlist")
    @DeleteMapping("/{productId}")
    public ApiResponse<Void> removeWishlist(
            @PathVariable Long productId,
            @RequestParam(defaultValue = "UNKNOWN") String sourcePage
    ) {
        wishlistService.removeWishlist(currentUserId(), productId, sourcePage);
        return ApiResponse.success("Wishlist removed successfully.");
    }

    @Operation(summary = "Check if product is in my wishlist")
    @GetMapping("/check/{productId}")
    public ApiResponse<Boolean> checkWishlist(@PathVariable Long productId) {
        return ApiResponse.success(
                "Wishlist status checked successfully.",
                wishlistService.checkWishlist(currentUserId(), productId)
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
