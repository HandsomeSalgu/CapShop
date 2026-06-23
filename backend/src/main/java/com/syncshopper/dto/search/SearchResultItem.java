package com.syncshopper.dto.search;

import com.syncshopper.domain.search.SearchSource;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;
import java.util.Map;

@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SearchResultItem {

    private SearchSource source;
    private String queryType;
    private String queryText;
    private String title;
    private String link;
    private String imageUrl;
    private String thumbnailUrl;
    private String snippet;
    private String price;
    private String mallName;
    private String brand;
    private String category;
    private LocalDateTime searchedAt;
    private Map<String, Object> raw;
}
