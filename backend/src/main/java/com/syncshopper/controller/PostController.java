package com.syncshopper.controller;

import com.syncshopper.common.response.ApiResponse;
import com.syncshopper.dto.request.PostSearchCondition;
import com.syncshopper.dto.response.PageResponse;
import com.syncshopper.dto.response.PostDetailResponse;
import com.syncshopper.dto.response.PostListResponse;
import com.syncshopper.service.PostService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springdoc.core.annotations.ParameterObject;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RequiredArgsConstructor
@RestController
@RequestMapping("/api/posts")
@Tag(name = "User Post", description = "User post read APIs")
public class PostController {

    private final PostService postService;

    @Operation(summary = "Get post list")
    @GetMapping
    public ApiResponse<PageResponse<PostListResponse>> getPosts(
            @ParameterObject @ModelAttribute PostSearchCondition condition
    ) {
        return ApiResponse.success(postService.getPosts(condition));
    }

    @Operation(summary = "Get notices")
    @GetMapping("/notices")
    public ApiResponse<PageResponse<PostListResponse>> getNotices(
            @Parameter(description = "Page number, starts at 1", example = "1")
            @RequestParam(defaultValue = "1") int page,
            @Parameter(description = "Page size", example = "10")
            @RequestParam(defaultValue = "10") int size
    ) {
        return ApiResponse.success(postService.getNotices(page, size));
    }

    @Operation(summary = "Get FAQs")
    @GetMapping("/faqs")
    public ApiResponse<PageResponse<PostListResponse>> getFaqs(
            @Parameter(description = "Page number, starts at 1", example = "1")
            @RequestParam(defaultValue = "1") int page,
            @Parameter(description = "Page size", example = "10")
            @RequestParam(defaultValue = "10") int size
    ) {
        return ApiResponse.success(postService.getFaqs(page, size));
    }

    @Operation(summary = "Get events")
    @GetMapping("/events")
    public ApiResponse<PageResponse<PostListResponse>> getEvents(
            @Parameter(description = "Page number, starts at 1", example = "1")
            @RequestParam(defaultValue = "1") int page,
            @Parameter(description = "Page size", example = "10")
            @RequestParam(defaultValue = "10") int size
    ) {
        return ApiResponse.success(postService.getEvents(page, size));
    }

    @Operation(summary = "Get post detail")
    @GetMapping("/{postId}")
    public ApiResponse<PostDetailResponse> getPostDetail(
            @Parameter(description = "Post ID", example = "1")
            @PathVariable Long postId
    ) {
        return ApiResponse.success(postService.getPostDetail(postId));
    }
}
