package com.syncshopper.domain.recommendation;

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
public class Recommendation {

    private Long recommendationId;
    private Long userId;
    private Long productId;
    private Long detectionId;
    private Integer rankNo;
    private Double score;
    private String reason;
    private RecommendationType recommendationType;
    private LocalDateTime createdAt;
}
