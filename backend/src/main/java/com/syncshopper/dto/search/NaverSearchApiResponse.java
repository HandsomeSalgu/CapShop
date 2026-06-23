package com.syncshopper.dto.search;

import com.syncshopper.domain.search.SearchSource;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NaverSearchApiResponse {

    private SearchSource source;
    private String queryText;
    private boolean success;
    private boolean cached;
    private Integer statusCode;
    private String errorMessage;
    private Map<String, Object> raw;
    private List<Map<String, Object>> items;
    private LocalDateTime searchedAt;

    public NaverSearchApiResponse asCached() {
        return NaverSearchApiResponse.builder()
                .source(source)
                .queryText(queryText)
                .success(success)
                .cached(true)
                .statusCode(statusCode)
                .errorMessage(errorMessage)
                .raw(raw)
                .items(items)
                .searchedAt(LocalDateTime.now())
                .build();
    }
}
