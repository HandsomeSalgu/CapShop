package com.syncshopper.service;

import com.syncshopper.common.exception.CustomException;
import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.config.NaverShoppingProperties;
import com.syncshopper.dto.response.NaverShoppingSearchResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

@RequiredArgsConstructor
@Component
public class NaverShoppingClient {

    private static final int MAX_DISPLAY = 100;

    private final RestClient.Builder restClientBuilder;
    private final NaverShoppingProperties properties;

    public NaverShoppingSearchResponse search(String query, Integer display, Integer start, String sort) {
        if (query == null || query.isBlank()) {
            throw new CustomException(ErrorCode.INVALID_COMMERCE_QUERY);
        }

        int normalizedDisplay = normalizeDisplay(display);
        int normalizedStart = normalizeStart(start);
        String normalizedSort = sort == null || sort.isBlank() ? properties.getSort() : sort;

        try {
            return restClientBuilder.clone()
                    .baseUrl(properties.getBaseUrl())
                    .build()
                    .get()
                    .uri(uriBuilder -> uriBuilder
                            .path(properties.getSearchPath())
                            .queryParam("query", query)
                            .queryParam("display", normalizedDisplay)
                            .queryParam("start", normalizedStart)
                            .queryParam("sort", normalizedSort)
                            .queryParam("exclude", properties.getExclude())
                            .build())
                    .header("X-Naver-Client-Id", properties.getClientId())
                    .header("X-Naver-Client-Secret", properties.getClientSecret())
                    .retrieve()
                    .body(NaverShoppingSearchResponse.class);
        } catch (RestClientException e) {
            throw new CustomException(ErrorCode.NAVER_SHOPPING_API_FAILED);
        }
    }

    private int normalizeDisplay(Integer display) {
        Integer normalizedDisplay = display == null ? properties.getDisplay() : display;
        if (normalizedDisplay == null || normalizedDisplay < 1) {
            return 1;
        }
        return Math.min(normalizedDisplay, MAX_DISPLAY);
    }

    private int normalizeStart(Integer start) {
        if (start == null || start < 1) {
            return properties.getStart();
        }
        return Math.min(start, 1000);
    }
}
