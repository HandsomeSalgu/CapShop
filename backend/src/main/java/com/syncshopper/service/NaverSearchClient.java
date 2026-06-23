package com.syncshopper.service;

import com.syncshopper.config.NaverSearchProperties;
import com.syncshopper.domain.search.SearchSource;
import com.syncshopper.dto.search.NaverSearchApiResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestClientResponseException;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Slf4j
@RequiredArgsConstructor
@Component
public class NaverSearchClient {

    private static final int MAX_DISPLAY = 100;
    private static final ParameterizedTypeReference<Map<String, Object>> MAP_RESPONSE =
            new ParameterizedTypeReference<>() {
            };

    private final RestClient.Builder restClientBuilder;
    private final NaverSearchProperties properties;
    private final SearchCache searchCache;

    public NaverSearchApiResponse searchShopping(String query, int display) {
        return search(SearchSource.NAVER_SHOPPING, query, display);
    }

    public NaverSearchApiResponse searchImage(String query, int display) {
        return search(SearchSource.NAVER_IMAGE, query, display);
    }

    public NaverSearchApiResponse searchBlog(String query, int display) {
        return search(SearchSource.NAVER_BLOG, query, display);
    }

    public NaverSearchApiResponse searchCafe(String query, int display) {
        return search(SearchSource.NAVER_CAFE, query, display);
    }

    public NaverSearchApiResponse searchWeb(String query, int display) {
        return search(SearchSource.NAVER_WEB, query, display);
    }

    private NaverSearchApiResponse search(SearchSource source, String query, int display) {
        if (query == null || query.isBlank()) {
            return failure(source, query, null, "Search query is blank.");
        }

        if (properties.getClientId() == null || properties.getClientId().isBlank()
                || properties.getClientSecret() == null || properties.getClientSecret().isBlank()) {
            log.warn("Naver search credentials are not configured. source={} query='{}'", source, query);
            return failure(source, query, null, "Naver search credentials are not configured.");
        }

        return searchCache.get(source, query)
                .orElseGet(() -> fetch(source, query, normalizeDisplay(display)));
    }

    private NaverSearchApiResponse fetch(SearchSource source, String query, int display) {
        String endpoint = endpoint(source);
        if (endpoint == null || endpoint.isBlank()) {
            return failure(source, query, null, "Naver search endpoint is not configured.");
        }

        try {
            Map<String, Object> raw = restClientBuilder.clone()
                    .baseUrl(endpoint)
                    .build()
                    .get()
                    .uri(uriBuilder -> {
                        uriBuilder
                                .queryParam("query", query)
                                .queryParam("display", display)
                                .queryParam("start", normalizeStart(properties.getSearch().getStart()))
                                .queryParam("sort", normalizeSort(properties.getSearch().getSort()));
                        if (source == SearchSource.NAVER_SHOPPING && hasText(properties.getSearch().getExclude())) {
                            uriBuilder.queryParam("exclude", properties.getSearch().getExclude());
                        }
                        return uriBuilder.build();
                    })
                    .header("X-Naver-Client-Id", properties.getClientId())
                    .header("X-Naver-Client-Secret", properties.getClientSecret())
                    .retrieve()
                    .body(MAP_RESPONSE);

            NaverSearchApiResponse response = NaverSearchApiResponse.builder()
                    .source(source)
                    .queryText(query)
                    .success(true)
                    .cached(false)
                    .statusCode(200)
                    .raw(raw)
                    .items(extractItems(raw))
                    .searchedAt(LocalDateTime.now())
                    .build();
            searchCache.put(source, query, response);
            return response;
        } catch (RestClientResponseException e) {
            int statusCode = e.getStatusCode().value();
            log.warn("Naver search API failed. source={} query='{}' status={}", source, query, statusCode);
            return failure(source, query, statusCode, "Naver search API failed with status " + statusCode + ".");
        } catch (RestClientException e) {
            log.warn("Naver search API request error. source={} query='{}' error={}", source, query, e.getClass().getSimpleName());
            return failure(source, query, null, "Naver search API request failed.");
        }
    }

    private String endpoint(SearchSource source) {
        NaverSearchProperties.Search search = properties.getSearch();
        return switch (source) {
            case NAVER_SHOPPING -> search.getShoppingUrl();
            case NAVER_IMAGE -> search.getImageUrl();
            case NAVER_BLOG -> search.getBlogUrl();
            case NAVER_CAFE -> search.getCafeUrl();
            case NAVER_WEB -> search.getWebUrl();
        };
    }

    @SuppressWarnings("unchecked")
    private List<Map<String, Object>> extractItems(Map<String, Object> raw) {
        if (raw == null || !(raw.get("items") instanceof List<?> items)) {
            return List.of();
        }

        return items.stream()
                .filter(Map.class::isInstance)
                .map(item -> (Map<String, Object>) item)
                .toList();
    }

    private NaverSearchApiResponse failure(SearchSource source, String query, Integer statusCode, String message) {
        return NaverSearchApiResponse.builder()
                .source(source)
                .queryText(query)
                .success(false)
                .cached(false)
                .statusCode(statusCode)
                .errorMessage(message)
                .items(List.of())
                .searchedAt(LocalDateTime.now())
                .build();
    }

    private int normalizeDisplay(int display) {
        if (display < 1) {
            return 1;
        }
        return Math.min(display, MAX_DISPLAY);
    }

    private int normalizeStart(Integer start) {
        if (start == null || start < 1) {
            return 1;
        }
        return Math.min(start, 1000);
    }

    private String normalizeSort(String sort) {
        return hasText(sort) ? sort : "sim";
    }

    private boolean hasText(String value) {
        return value != null && !value.isBlank();
    }
}
