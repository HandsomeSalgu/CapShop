package com.syncshopper.service;

import com.syncshopper.domain.product.Product;
import com.syncshopper.dto.response.CommerceProductResponse;
import com.syncshopper.mapper.ProductMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@RequiredArgsConstructor
@Service
public class ProductUpsertService {

    private static final String COMMERCE_PRODUCT_DESCRIPTION = "Naver Shopping search result product.";

    private final ProductMapper productMapper;

    @Transactional
    public Long upsertCommerceProduct(CommerceProductResponse response) {
        Product existingProduct = productMapper.findBySourceAndAffiliateUrl(
                response.getSource(),
                response.getAffiliateUrl()
        );
        if (existingProduct != null) {
            return existingProduct.getProductId();
        }

        Product product = Product.builder()
                .title(response.getTitle())
                .brand(response.getBrand())
                .categoryName(response.getCategoryName())
                .price(response.getPrice())
                .imageUrl(response.getImageUrl())
                .affiliateUrl(response.getAffiliateUrl())
                .description(COMMERCE_PRODUCT_DESCRIPTION)
                .source(response.getSource())
                .reviewCount(0)
                .rating(null)
                .visibleYn("Y")
                .build();

        productMapper.insertCommerceProduct(product);
        return product.getProductId();
    }
}
