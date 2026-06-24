package com.syncshopper.service;

import com.syncshopper.common.exception.CustomException;
import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.domain.search.SearchSource;
import com.syncshopper.dto.response.AiCommerceQueryResponse;
import com.syncshopper.dto.response.CommerceProductResponse;
import com.syncshopper.dto.response.NaverShoppingItemResponse;
import com.syncshopper.dto.response.NaverShoppingSearchResponse;
import com.syncshopper.dto.search.NaverSearchApiResponse;
import com.syncshopper.dto.search.SearchResultItem;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;
import org.springframework.web.util.HtmlUtils;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@RequiredArgsConstructor
@Service
public class CommerceService {

    private static final String NAVER_SOURCE = "NAVER";
    private static final int TOP3_LIMIT = 3;

    private final NaverShoppingClient naverShoppingClient;
    private final NaverSearchClient naverSearchClient;
    private final SearchResultNormalizer searchResultNormalizer;
    private final CommerceProductPersistenceService commerceProductPersistenceService;

    @Cacheable(value = "commerceSearch", key = "#query + '_' + #display + '_' + #start + '_' + #sort")
    public List<CommerceProductResponse> searchProducts(String query, Integer display, Integer start, String sort) {
        validateQuery(query);

        NaverShoppingSearchResponse response = naverShoppingClient.search(query, display, start, sort);
        if (response == null || response.getItems() == null) {
            return List.of();
        }

        return response.getItems().stream()
                .map(this::toCommerceProductResponse)
                .toList();
    }

    @Cacheable(value = "commerceSearch", key = "#source + '_' + #query + '_' + #display + '_' + #start + '_' + #sort")
    public List<CommerceProductResponse> searchProducts(
            String query,
            Integer display,
            Integer start,
            String sort,
            String source
    ) {
        validateQuery(query);

        if (source == null || source.isBlank() || NAVER_SOURCE.equalsIgnoreCase(source)) {
            return searchProducts(query, display, start, sort);
        }

        SearchSource searchSource = parseSearchSource(source);
        NaverSearchApiResponse response = switch (searchSource) {
            case NAVER_SHOPPING -> naverSearchClient.searchShopping(query, normalizeDisplay(display));
            case NAVER_IMAGE -> naverSearchClient.searchImage(query, normalizeDisplay(display));
            case NAVER_BLOG -> naverSearchClient.searchBlog(query, normalizeDisplay(display));
            case NAVER_CAFE -> naverSearchClient.searchCafe(query, normalizeDisplay(display));
            case NAVER_WEB -> naverSearchClient.searchWeb(query, normalizeDisplay(display));
        };

        if (response == null || !response.isSuccess()) {
            log.warn(
                    "Naver source search returned no usable response. source={} query='{}' status={} error={}",
                    searchSource,
                    query,
                    response == null ? null : response.getStatusCode(),
                    response == null ? null : response.getErrorMessage()
            );
            return List.of();
        }

        return searchResultNormalizer.normalize(response, searchSource.name()).stream()
                .map(this::toCommerceProductResponse)
                .toList();
    }

    @Cacheable(value = "commerceTop3", key = "#query")
    public List<CommerceProductResponse> getTop3Products(String query) {
        validateQuery(query);

        NaverShoppingSearchResponse response = naverShoppingClient.search(query, null, null, null);
        if (response == null || response.getItems() == null) {
            return List.of();
        }

        List<CommerceProductResponse> products = response.getItems().stream()
                .limit(TOP3_LIMIT)
                .map(this::toCommerceProductResponse)
                .toList();
        return commerceProductPersistenceService.persistTop3(products);
    }

    public List<CommerceProductResponse> searchTop3(AiCommerceQueryResponse queryResponse) {
        if (queryResponse == null || queryResponse.getPrimaryQuery() == null || queryResponse.getPrimaryQuery().isBlank()) {
            return List.of();
        }

        List<String> queries = new ArrayList<>();
        queries.add(queryResponse.getPrimaryQuery());
        if (queryResponse.getFallbackQueries() != null) {
            queries.addAll(queryResponse.getFallbackQueries());
        }

        log.info("Commerce Top3 query candidates: {}", queries);

        Map<String, CommerceProductResponse> productsByKey = new LinkedHashMap<>();
        for (String query : queries.stream().filter(value -> value != null && !value.isBlank()).distinct().toList()) {
            NaverShoppingSearchResponse response = naverShoppingClient.search(query, null, null, null);
            int itemCount = response == null || response.getItems() == null ? 0 : response.getItems().size();
            log.info("Naver shopping search query='{}' itemCount={}", query, itemCount);
            if (response == null || response.getItems() == null) {
                continue;
            }

            for (NaverShoppingItemResponse item : response.getItems()) {
                CommerceProductResponse product = toCommerceProductResponse(item);
                productsByKey.putIfAbsent(deduplicateKey(product), product);
            }

            if (productsByKey.size() >= TOP3_LIMIT) {
                break;
            }
        }

        List<CommerceProductResponse> products = productsByKey.values().stream()
                .limit(TOP3_LIMIT)
                .filter(product -> product != null)
                .toList();
        List<CommerceProductResponse> persistedProducts = commerceProductPersistenceService.persistProducts(products);
        log.info("Commerce Top3 final productCount={}", persistedProducts.size());
        return persistedProducts;
    }

    public List<CommerceProductResponse> persistProducts(List<CommerceProductResponse> products) {
        if (products == null || products.isEmpty()) {
            return List.of();
        }

        return commerceProductPersistenceService.persistProducts(products);
    }

    private CommerceProductResponse toCommerceProductResponse(NaverShoppingItemResponse item) {
        return CommerceProductResponse.builder()
                .title(cleanHtml(item.getTitle()))
                .brand(resolveBrand(item))
                .mallName(cleanHtml(item.getMallName()))
                .categoryName(resolveCategory(item))
                .price(parsePrice(item.getLprice()))
                .imageUrl(item.getImage())
                .thumbnailUrl(item.getImage())
                .affiliateUrl(item.getLink())
                .source(NAVER_SOURCE)
                .externalProductId(item.getProductId())
                .build();
    }

    private CommerceProductResponse toCommerceProductResponse(SearchResultItem item) {
        return CommerceProductResponse.builder()
                .title(item.getTitle())
                .brand(item.getBrand())
                .mallName(item.getMallName())
                .categoryName(item.getCategory())
                .price(parsePrice(item.getPrice()))
                .imageUrl(firstNonBlank(item.getImageUrl(), item.getThumbnailUrl()))
                .thumbnailUrl(firstNonBlank(item.getThumbnailUrl(), item.getImageUrl()))
                .affiliateUrl(item.getLink())
                .source(item.getSource() == null ? null : item.getSource().name())
                .externalProductId(resolveExternalSearchId(item))
                .snippet(item.getSnippet())
                .queryType(item.getQueryType())
                .queryText(item.getQueryText())
                .build();
    }

    private String deduplicateKey(CommerceProductResponse product) {
        if (product.getAffiliateUrl() != null && !product.getAffiliateUrl().isBlank()) {
            return "link:" + product.getAffiliateUrl();
        }
        if (product.getExternalProductId() != null && !product.getExternalProductId().isBlank()) {
            return "external:" + product.getExternalProductId();
        }
        return "fallback:" + product.getTitle() + "|" + product.getMallName() + "|" + product.getPrice();
    }

    private String resolveCategory(NaverShoppingItemResponse item) {
        String category3 = cleanHtml(item.getCategory3());
        if (category3 != null && !category3.isBlank()) {
            return category3;
        }

        String category2 = cleanHtml(item.getCategory2());
        if (category2 != null && !category2.isBlank()) {
            return category2;
        }

        return cleanHtml(item.getCategory1());
    }

    private SearchSource parseSearchSource(String source) {
        String normalized = source == null ? "" : source.trim().toUpperCase();
        if (NAVER_SOURCE.equals(normalized)) {
            return SearchSource.NAVER_SHOPPING;
        }

        try {
            return SearchSource.valueOf(normalized);
        } catch (IllegalArgumentException e) {
            throw new CustomException(ErrorCode.INVALID_COMMERCE_QUERY);
        }
    }

    private int normalizeDisplay(Integer display) {
        if (display == null || display < 1) {
            return 10;
        }
        return Math.min(display, 100);
    }

    private String resolveExternalSearchId(SearchResultItem item) {
        if (item.getRaw() != null && item.getRaw().get("productId") != null) {
            return String.valueOf(item.getRaw().get("productId"));
        }
        if (item.getLink() != null && !item.getLink().isBlank()) {
            return item.getSource().name() + ":" + item.getLink();
        }
        return item.getSource().name() + ":" + item.getTitle();
    }

    private String firstNonBlank(String first, String second) {
        return first != null && !first.isBlank() ? first : second;
    }

    private void validateQuery(String query) {
        if (query == null || query.isBlank()) {
            throw new CustomException(ErrorCode.INVALID_COMMERCE_QUERY);
        }
    }

    private String resolveBrand(NaverShoppingItemResponse item) {
        String brand = cleanHtml(item.getBrand());
        if (brand != null && !brand.isBlank()) {
            return brand;
        }
        return cleanHtml(item.getMaker());
    }

    private String cleanHtml(String value) {
        if (value == null) {
            return null;
        }

        String withoutTags = value.replaceAll("<[^>]*>", "");
        String decoded = HtmlUtils.htmlUnescape(withoutTags);

        return decoded.replaceAll("\\s+", " ").trim();
    }

    private Integer parsePrice(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }

        try {
            return Integer.parseInt(value);
        } catch (NumberFormatException e) {
            return null;
        }
    }
}
