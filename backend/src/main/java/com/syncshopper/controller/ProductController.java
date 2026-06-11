package com.syncshopper.controller;

import com.syncshopper.common.response.ApiResponse;
import com.syncshopper.dto.request.ProductSearchCondition;
import com.syncshopper.dto.response.PageResponse;
import com.syncshopper.dto.response.ProductDetailResponse;
import com.syncshopper.dto.response.ProductListResponse;
import com.syncshopper.service.ProductService;
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

import java.util.List;

@RequiredArgsConstructor
@RestController
@RequestMapping("/api/products")
@Tag(name = "Product", description = "User product read APIs")
public class ProductController {

    private final ProductService productService;

    @Operation(summary = "Get product list")
    @GetMapping
    public ApiResponse<PageResponse<ProductListResponse>> getProducts(
            @ParameterObject @ModelAttribute ProductSearchCondition condition
    ) {
        return ApiResponse.success(productService.getProducts(condition));
    }

    @Operation(summary = "Get best products")
    @GetMapping("/best")
    public ApiResponse<List<ProductListResponse>> getBestProducts(
            @Parameter(description = "Maximum item count", example = "10")
            @RequestParam(defaultValue = "10") int limit
    ) {
        return ApiResponse.success(productService.getBestProducts(limit));
    }

    @Operation(summary = "Get hot products")
    @GetMapping("/hot")
    public ApiResponse<List<ProductListResponse>> getHotProducts(
            @Parameter(description = "Maximum item count", example = "10")
            @RequestParam(defaultValue = "10") int limit
    ) {
        return ApiResponse.success(productService.getHotProducts(limit));
    }

    @Operation(summary = "Get product detail")
    @GetMapping("/{productId}")
    public ApiResponse<ProductDetailResponse> getProductDetail(
            @Parameter(description = "Product ID", example = "1")
            @PathVariable Long productId
    ) {
        return ApiResponse.success(productService.getProductDetail(productId));
    }

    @Operation(summary = "Get related products")
    @GetMapping("/{productId}/related")
    public ApiResponse<List<ProductListResponse>> getRelatedProducts(
            @Parameter(description = "Product ID", example = "1")
            @PathVariable Long productId,
            @Parameter(description = "Maximum item count", example = "10")
            @RequestParam(defaultValue = "10") int limit
    ) {
        return ApiResponse.success(productService.getRelatedProducts(productId, limit));
    }
}
