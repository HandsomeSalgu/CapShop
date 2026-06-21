package com.syncshopper.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AiCommerceQueryResponse {

    @JsonProperty("primary_query")
    private String primaryQuery;

    @JsonProperty("fallback_queries")
    private List<String> fallbackQueries;

    @JsonProperty("normalized_brand")
    private String normalizedBrand;

    @JsonProperty("normalized_model")
    private String normalizedModel;

    @JsonProperty("normalized_category")
    private String normalizedCategory;

    @JsonProperty("query_confidence")
    private Double queryConfidence;

    private String reason;
}
