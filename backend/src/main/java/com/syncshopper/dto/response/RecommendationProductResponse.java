package com.syncshopper.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
@Schema(description = "Recommendation product response")
public class RecommendationProductResponse {

    private Long recommendationId;
    private Long productId;
    private String externalProductId;
    private String title;
    private String brand;
    private String categoryName;
    private Integer price;
    private String imageUrl;
    private String link;
    private Integer reviewCount;
    private Double rating;
    private Integer rankNo;
    private Double score;
    private String reason;
    private String recommendationType;
    private LocalDateTime createdAt;
}
