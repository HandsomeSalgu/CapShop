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
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AiVerificationResponse {

    @JsonProperty("best_candidate_index")
    private Integer bestCandidateIndex;

    @JsonProperty("match_level")
    private String matchLevel;

    private Double confidence;

    @JsonProperty("identified_name")
    private String identifiedName;

    private String reason;
    private List<String> evidence;
    private List<Alternative> alternatives;

    @Getter
    @Setter
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class Alternative {

        @JsonProperty("candidate_index")
        private Integer candidateIndex;

        @JsonProperty("match_level")
        private String matchLevel;

        private String reason;
    }
}
