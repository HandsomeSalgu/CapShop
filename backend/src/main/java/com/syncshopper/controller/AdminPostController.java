package com.syncshopper.controller;

import com.syncshopper.common.exception.CustomException;
import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.common.response.ApiResponse;
import com.syncshopper.dto.request.PostCreateRequest;
import com.syncshopper.dto.request.PostUpdateRequest;
import com.syncshopper.dto.response.PostDetailResponse;
import com.syncshopper.service.PostService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

@RequiredArgsConstructor
@RestController
@RequestMapping("/api/admin/posts")
@Tag(name = "Admin Post", description = "Admin post management APIs")
public class AdminPostController {

    private final PostService postService;

    @Operation(summary = "Get all posts (Admin)")
    @GetMapping
    public ApiResponse<com.syncshopper.dto.response.PageResponse<com.syncshopper.dto.response.PostListResponse>> getAllPosts(
            @ModelAttribute com.syncshopper.dto.request.PostSearchCondition condition
    ) {
        return ApiResponse.success("Posts fetched.", postService.getAllPosts(condition));
    }

    @Operation(summary = "Get post detail (Admin)")
    @GetMapping("/{postId}")
    public ApiResponse<PostDetailResponse> getAdminPostDetail(
            @PathVariable Long postId
    ) {
        return ApiResponse.success("Post detail fetched.", postService.getAdminPostDetail(postId));
    }

    @Operation(summary = "Create post")
    @PostMapping
    public ApiResponse<PostDetailResponse> createPost(
            @Valid @RequestBody PostCreateRequest request
    ) {
        return ApiResponse.success("Post created.", postService.createPost(currentUserId(), request));
    }

    @Operation(summary = "Update post")
    @PutMapping("/{postId}")
    public ApiResponse<PostDetailResponse> updatePost(
            @PathVariable Long postId,
            @Valid @RequestBody PostUpdateRequest request
    ) {
        return ApiResponse.success("Post updated.", postService.updatePost(currentUserId(), postId, request));
    }

    @Operation(summary = "Delete post (Soft Delete)")
    @DeleteMapping("/{postId}")
    public ApiResponse<Void> deletePost(
            @PathVariable Long postId
    ) {
        postService.deletePost(currentUserId(), postId);
        return ApiResponse.success("Post deleted.");
    }

    @Operation(summary = "Restore post")
    @PatchMapping("/{postId}/restore")
    public ApiResponse<Void> restorePost(
            @PathVariable Long postId
    ) {
        postService.restorePost(currentUserId(), postId);
        return ApiResponse.success("Post restored.");
    }

    private Long currentUserId() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication == null || !authentication.isAuthenticated()) {
            throw new CustomException(ErrorCode.UNAUTHORIZED);
        }
        return Long.valueOf(authentication.getName());
    }
}
