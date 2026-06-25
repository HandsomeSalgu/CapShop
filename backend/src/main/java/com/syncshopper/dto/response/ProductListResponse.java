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
@Schema(description = "Product list response")
public class ProductListResponse {

    private Long productId;
    private String title;
    private String brand;
    private String categoryName;
    private Integer price;
    private String imageUrl;
    private Integer reviewCount;
    private Double rating;
    private String affiliateUrl;
    private String mallName;
    private String externalProductId;
    private String source;

    public static ProductListResponse from(Product product) {
        return ProductListResponse.builder()
                .productId(product.getProductId())
                .title(product.getTitle())
                .brand(product.getBrand())
                .categoryName(product.getCategoryName())
                .price(product.getPrice())
                .imageUrl(product.getImageUrl())
                .reviewCount(product.getReviewCount())
                .rating(product.getRating())
                .affiliateUrl(product.getAffiliateUrl())
                .mallName(product.getMallName())
                .externalProductId(product.getExternalProductId())
                .source(product.getSource())
                .build();
    }
}
