package com.syncshopper.dto.search;

import com.syncshopper.dto.response.DetectionAnalyzeResponse;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AiVerificationRequest {

    private DetectionAnalyzeResponse.DetectionSummary detection;
    private List<ScoredSearchCandidate> candidates;
}
