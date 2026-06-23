package com.syncshopper.mapper;

import com.syncshopper.domain.search.ProductCandidate;
import com.syncshopper.domain.search.SearchQuery;
import com.syncshopper.domain.search.SearchResult;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface DetectionSearchMapper {

    int insertSearchQuery(SearchQuery searchQuery);

    int insertSearchResult(SearchResult searchResult);

    int insertProductCandidate(ProductCandidate productCandidate);
}
