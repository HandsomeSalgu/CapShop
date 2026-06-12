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
@Schema(description = "Recommendation history response")
public class RecommendationHistoryResponse {

    private Long recommendationId;
    private Long productId;
    private String title;
    private String brand;
    private String categoryName;
    private Integer price;
    private String imageUrl;
    private Integer rankNo;
    private Double score;
    private String reason;
    private String recommendationType;
    private LocalDateTime createdAt;
}
