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
@Schema(description = "Detection history response")
public class DetectionHistoryResponse {

    private Long detectionId;
    private String videoId;
    private Integer timestampSec;
    private String targetName;
    private String categoryName;
    private String brand;
    private Double confidence;
    private String status;
    private LocalDateTime createdAt;
}
