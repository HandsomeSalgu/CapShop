package com.syncshopper.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
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
@Schema(description = "AI analysis result")
public class AiAnalysisResult {

    private String targetName;
    private String categoryName;
    private String brand;
    private String modelName;
    private Double confidence;
    private String rawResponseJson;
}
