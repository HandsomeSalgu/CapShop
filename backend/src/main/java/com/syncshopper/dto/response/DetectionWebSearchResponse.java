package com.syncshopper.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;
import java.util.Map;

@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DetectionWebSearchResponse {

    private Long jobId;
    private DetectionAnalyzeResponse.DetectionSummary detection;
    private SearchQueryBundleResponse queries;
    private List<SearchCandidateResponse> candidates;

    @JsonProperty("ai_verification")
    private AiVerificationResponse aiVerification;

    private Map<String, Object> metadata;
    private String message;
}
