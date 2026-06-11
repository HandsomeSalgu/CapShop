package com.syncshopper.dto.response;

import com.syncshopper.domain.product.Product;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "Product detail response")
public class ProductDetailResponse {

    private Long productId;
    private String title;
    private String brand;
    private Long categoryId;
    private String categoryName;
    private Integer price;
    private String imageUrl;
    private String affiliateUrl;
    private String description;
    private String source;
    private Integer reviewCount;
    private Double rating;

    public static ProductDetailResponse from(Product product) {
        return ProductDetailResponse.builder()
                .productId(product.getProductId())
                .title(product.getTitle())
                .brand(product.getBrand())
                .categoryId(product.getCategoryId())
                .categoryName(product.getCategoryName())
                .price(product.getPrice())
                .imageUrl(product.getImageUrl())
                .affiliateUrl(product.getAffiliateUrl())
                .description(product.getDescription())
                .source(product.getSource())
                .reviewCount(product.getReviewCount())
                .rating(product.getRating())
                .build();
    }
}
