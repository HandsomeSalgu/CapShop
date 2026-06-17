package com.syncshopper.service;

import com.syncshopper.common.exception.CustomException;
import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.dto.response.CommerceProductResponse;
import com.syncshopper.dto.response.NaverShoppingItemResponse;
import com.syncshopper.dto.response.NaverShoppingSearchResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.util.HtmlUtils;

import java.util.List;
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
                .categoryName(cleanHtml(item.getCategory1()))
                .price(parsePrice(item.getLprice()))
                .imageUrl(item.getImage())
                .affiliateUrl(item.getLink())
                .source(NAVER_SOURCE)
                .externalProductId(item.getProductId())
                .build();
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
