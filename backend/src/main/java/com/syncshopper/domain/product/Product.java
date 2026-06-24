package com.syncshopper.domain.product;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Product {

    private Long productId;
    private String title;
    private String brand;
    private String categoryName;
    private String category1Name;
    private String category2Name;
    private String category3Name;
    private String category4Name;
    private Integer price;
    private String imageUrl;
    private String affiliateUrl;
    private String mallName;
    private String description;
    private String source;
    private String externalProductId;
    private Integer reviewCount;
    private Double rating;
    private String visibleYn;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
