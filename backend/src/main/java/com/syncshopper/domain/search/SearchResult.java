package com.syncshopper.domain.search;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SearchResult {

    private Long resultId;
    private Long jobId;
    private Long queryId;
    private String source;
    private String title;
    private String url;
    private String imageUrl;
    private String snippet;
    private String price;
    private String mallName;
    private String rawJson;
    private LocalDateTime createdAt;
}
