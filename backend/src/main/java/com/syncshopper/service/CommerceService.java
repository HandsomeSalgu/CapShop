package com.syncshopper.service;

import com.syncshopper.common.exception.CustomException;
import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.dto.response.AiCommerceQueryResponse;
import com.syncshopper.dto.response.CommerceProductResponse;
import com.syncshopper.dto.response.NaverShoppingItemResponse;
import com.syncshopper.dto.response.NaverShoppingSearchResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.util.HtmlUtils;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.cache.annotation.Cacheable;

@RequiredArgsConstructor
@Service
public class CommerceService {

    private static final String NAVER_SOURCE = "NAVER";
    private static final int TOP3_LIMIT = 3;

    private final NaverShoppingClient naverShoppingClient;
    private final ProductUpsertService productUpsertService;

    @Cacheable(value = "commerceSearch", key = "#query + '_' + #display + '_' + #start + '_' + #sort")
    @Transactional
    public List<CommerceProductResponse> searchProducts(String query, Integer display, Integer start, String sort) {
        validateQuery(query);

        NaverShoppingSearchResponse response = naverShoppingClient.search(query, display, start, sort);
        return mapAndUpsert(response).stream()
                .toList();
    }

    @Cacheable(value = "commerceTop3", key = "#query")
    @Transactional
    public List<CommerceProductResponse> getTop3Products(String query) {
        validateQuery(query);

        NaverShoppingSearchResponse response = naverShoppingClient.search(query, null, null, null);
        if (response == null || response.getItems() == null) {
            return List.of();
        }

        return response.getItems().stream()
                .limit(TOP3_LIMIT)
                .map(this::toCommerceProductResponse)
                .peek(product -> product.setProductId(productUpsertService.upsertCommerceProduct(product)))
                .toList();
    }

    @Transactional
    public List<CommerceProductResponse> searchTop3(AiCommerceQueryResponse queryResponse) {
        if (queryResponse == null || queryResponse.getPrimaryQuery() == null || queryResponse.getPrimaryQuery().isBlank()) {
            return List.of();
        }

        List<String> queries = new ArrayList<>();
        queries.add(queryResponse.getPrimaryQuery());
        if (queryResponse.getFallbackQueries() != null) {
            queries.addAll(queryResponse.getFallbackQueries());
        }

        Map<String, CommerceProductResponse> productsByKey = new LinkedHashMap<>();
        for (String query : queries.stream().filter(value -> value != null && !value.isBlank()).distinct().toList()) {
            NaverShoppingSearchResponse response = naverShoppingClient.search(query, null, null, null);
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

        return productsByKey.values().stream()
                .limit(TOP3_LIMIT)
                .map(this::upsertSafely)
                .filter(product -> product != null)
                .toList();
    }

    private List<CommerceProductResponse> mapAndUpsert(NaverShoppingSearchResponse response) {
        if (response == null || response.getItems() == null) {
            return List.of();
        }

        return response.getItems().stream()
                .map(this::toCommerceProductResponse)
                .peek(product -> product.setProductId(productUpsertService.upsertCommerceProduct(product)))
                .toList();
    }

    private CommerceProductResponse toCommerceProductResponse(NaverShoppingItemResponse item) {
        return CommerceProductResponse.builder()
                .title(cleanHtml(item.getTitle()))
                .brand(resolveBrand(item))
                .mallName(cleanHtml(item.getMallName()))
                .categoryName(resolveCategory(item))
                .price(parsePrice(item.getLprice()))
                .imageUrl(item.getImage())
                .affiliateUrl(item.getLink())
                .source(NAVER_SOURCE)
                .externalProductId(item.getProductId())
                .build();
    }

    private CommerceProductResponse upsertSafely(CommerceProductResponse product) {
        try {
            product.setProductId(productUpsertService.upsertCommerceProduct(product));
            return product;
        } catch (RuntimeException e) {
            return null;
        }
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
