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
public class SearchQuery {

    private Long queryId;
    private Long jobId;
    private String queryText;
    private String queryType;
    private String sourceTarget;
    private LocalDateTime createdAt;
}
