package com.syncshopper.service;

import com.syncshopper.config.NaverSearchProperties;
import com.syncshopper.domain.search.SearchSource;
import com.syncshopper.dto.search.NaverSearchApiResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.time.Instant;
import java.util.Locale;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;

@RequiredArgsConstructor
@Component
public class InMemorySearchCache implements SearchCache {

    private final NaverSearchProperties properties;
    private final ConcurrentMap<String, CacheEntry> cache = new ConcurrentHashMap<>();

    @Override
    public Optional<NaverSearchApiResponse> get(SearchSource source, String queryText) {
        String key = cacheKey(source, queryText);
        CacheEntry entry = cache.get(key);
        if (entry == null) {
            return Optional.empty();
        }

        if (Instant.now().isAfter(entry.expiresAt())) {
            cache.remove(key);
            return Optional.empty();
        }

        return Optional.of(entry.response().asCached());
    }

    @Override
    public void put(SearchSource source, String queryText, NaverSearchApiResponse response) {
        if (response == null || !response.isSuccess()) {
            return;
        }

        cache.put(
                cacheKey(source, queryText),
                new CacheEntry(response, Instant.now().plus(cacheTtl()))
        );
    }

    private Duration cacheTtl() {
        Long hours = properties.getSearch() == null ? null : properties.getSearch().getCacheTtlHours();
        return Duration.ofHours(hours == null || hours < 1 ? 24 : hours);
    }

    private String cacheKey(SearchSource source, String queryText) {
        return source.name() + ":" + normalize(queryText);
    }

    private String normalize(String queryText) {
        return queryText == null ? "" : queryText.trim().toLowerCase(Locale.ROOT);
    }

    private record CacheEntry(NaverSearchApiResponse response, Instant expiresAt) {
    }
}
