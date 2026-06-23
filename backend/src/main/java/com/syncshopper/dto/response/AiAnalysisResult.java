package com.syncshopper.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;
import java.util.Map;

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
    private String color;
    private String shape;
    private String logoText;
    private List<String> keyFeatures;
    private Double confidence;
    private Map<String, Object> ocrAnalysis;
    private Map<String, Object> visualAnalysis;
    private Map<String, Object> searchIdentification;
    private List<Map<String, Object>> googleSearchResults;
    private Map<String, Object> googleSourceCounts;
    private AiCommerceQueryResponse commerceQuery;
    private List<CommerceProductResponse> products;
    private String rawResponseJson;
}
