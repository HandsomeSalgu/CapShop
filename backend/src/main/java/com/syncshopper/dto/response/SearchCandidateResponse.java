package com.syncshopper.dto.response;

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
public class SearchCandidateResponse {

    private Integer index;
    private String source;
    private String sourceLabel;
    private String queryType;
    private String queryText;
    private String title;
    private String url;
    private String imageUrl;
    private String thumbnailUrl;
    private String snippet;
    private String price;
    private String mallName;
    private Double score;
    private String matchLevel;
    private String reason;
}
