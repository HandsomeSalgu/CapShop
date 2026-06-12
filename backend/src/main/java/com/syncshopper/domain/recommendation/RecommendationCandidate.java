package com.syncshopper.domain.recommendation;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class RecommendationCandidate {

    private Long productId;
    private String title;
    private String brand;
    private String categoryName;
    private Integer price;
    private String imageUrl;
    private Integer reviewCount;
    private Double rating;
    private Double score;
    private String reason;
}
