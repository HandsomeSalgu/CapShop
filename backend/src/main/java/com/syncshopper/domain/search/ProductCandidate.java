package com.syncshopper.domain.search;

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
public class ProductCandidate {

    private Long candidateId;
    private Long jobId;
    private Long resultId;
    private String productName;
    private String brand;
    private String category;
    private String imageUrl;
    private String productUrl;
    private String price;
    private Double visualScore;
    private Double textScore;
    private Double finalScore;
    private String reason;
    private LocalDateTime createdAt;
}
