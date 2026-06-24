package com.syncshopper.service;

import com.syncshopper.dto.response.CommerceProductResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Objects;

@RequiredArgsConstructor
@Service
public class CommerceProductPersistenceService {

    private static final int TOP3_LIMIT = 3;

    private final ProductUpsertService productUpsertService;

    @Transactional
    public List<CommerceProductResponse> persistTop3(List<CommerceProductResponse> products) {
        if (products == null || products.isEmpty()) {
            return List.of();
        }

        return products.stream()
                .filter(Objects::nonNull)
                .limit(TOP3_LIMIT)
                .map(this::ensurePersistedCommerceProduct)
                .toList();
    }

    @Transactional
    public List<CommerceProductResponse> persistProducts(List<CommerceProductResponse> products) {
        if (products == null || products.isEmpty()) {
            return List.of();
        }

        return products.stream()
                .filter(Objects::nonNull)
                .map(this::ensurePersistedCommerceProduct)
                .toList();
    }

    private CommerceProductResponse ensurePersistedCommerceProduct(CommerceProductResponse product) {
        if (product.getProductId() != null) {
            return product;
        }

        product.setProductId(productUpsertService.upsertCommerceProduct(product));
        return product;
    }
}
