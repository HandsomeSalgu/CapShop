package com.syncshopper.controller;

import com.syncshopper.common.response.ApiResponse;
import com.syncshopper.dto.response.CommerceProductResponse;
import com.syncshopper.service.CommerceService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RequiredArgsConstructor
@RestController
@RequestMapping("/api/commerce")
@Tag(name = "Commerce", description = "External commerce product search APIs")
public class CommerceController {

    private final CommerceService commerceService;

    @Operation(summary = "Search commerce products", description = "Searches products with the Naver Shopping API.")
    @GetMapping("/search")
    public ApiResponse<List<CommerceProductResponse>> searchProducts(
            @RequestParam String query,
            @RequestParam(required = false) Integer display,
            @RequestParam(required = false, defaultValue = "1") Integer start,
            @RequestParam(required = false) String sort
    ) {
        return ApiResponse.success(
                "Commerce product search succeeded.",
                commerceService.searchProducts(query, display, start, sort)
        );
    }

    @Operation(summary = "Get commerce product Top 3", description = "Returns the top 3 products from Naver Shopping search.")
    @GetMapping("/top3")
    public ApiResponse<List<CommerceProductResponse>> getTop3Products(
            @RequestParam String query
    ) {
        return ApiResponse.success(
                "Commerce product Top 3 lookup succeeded.",
                commerceService.getTop3Products(query)
        );
    }
}
