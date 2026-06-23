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
public class SearchQueryBundleResponse {

    @JsonProperty("primary_queries")
    private List<String> primaryQueries;

    @JsonProperty("shopping_queries")
    private List<String> shoppingQueries;

    @JsonProperty("image_queries")
    private List<String> imageQueries;

    @JsonProperty("blog_queries")
    private List<String> blogQueries;

    @JsonProperty("cafe_queries")
    private List<String> cafeQueries;

    @JsonProperty("web_queries")
    private List<String> webQueries;

    @JsonProperty("fallback_queries")
    private List<String> fallbackQueries;
}
