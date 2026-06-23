package com.syncshopper.service;

import com.syncshopper.domain.search.SearchSource;
import com.syncshopper.dto.search.NaverSearchApiResponse;

import java.util.Optional;

public interface SearchCache {

    Optional<NaverSearchApiResponse> get(SearchSource source, String queryText);

    void put(SearchSource source, String queryText, NaverSearchApiResponse response);
}
