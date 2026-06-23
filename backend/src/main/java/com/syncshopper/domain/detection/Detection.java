package com.syncshopper.domain.detection;

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
public class Detection {

    private Long detectionId;
    private Long userId;
    private String videoId;
    private Integer timestampSec;
    private String imageHash;
    private String subtitleSummary;
    private String targetName;
    private String categoryName;
    private String brand;
    private String modelName;
    private String color;
    private String shape;
    private String logoText;
    private String keyFeaturesJson;
    private Double confidence;
    private DetectionStatus status;
    private LocalDateTime createdAt;
}
