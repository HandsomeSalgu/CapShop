package com.syncshopper.dto.response;

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
public class CommerceProductResponse {

    private Long productId;
    private String title;
    private String brand;
    private String mallName;
    private String categoryName;
    private String category1Name;
    private String category2Name;
    private String category3Name;
    private String category4Name;
    private Integer price;
    private String imageUrl;
    private String thumbnailUrl;
    private String affiliateUrl;
    private String source;
    private String externalProductId;
    private String snippet;
    private String queryType;
    private String queryText;
}
