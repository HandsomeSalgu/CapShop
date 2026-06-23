package com.syncshopper.dto.search;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ScoredSearchCandidate {

    private int index;
    private Long resultId;
    private SearchResultItem result;
    private Double visualScore;
    private Double textScore;
    private Double finalScore;
    private String reason;
}
