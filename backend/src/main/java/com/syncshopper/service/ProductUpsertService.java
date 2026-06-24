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
        Product existingProduct = productMapper.findBySourceAndExternalProductId(
                response.getSource(),
                response.getExternalProductId()
        );
        if (existingProduct != null) {
            Product product = toProduct(response);
            product.setProductId(existingProduct.getProductId());
            productMapper.updateCommerceProduct(product);
            return existingProduct.getProductId();
        }

        Product product = toProduct(response);
        productMapper.insertCommerceProduct(product);
        return product.getProductId();
    }

    private Product toProduct(CommerceProductResponse response) {
        return Product.builder()
                .title(response.getTitle())
                .brand(response.getBrand())
                .categoryName(response.getCategoryName())
                .category1Name(response.getCategory1Name())
                .category2Name(response.getCategory2Name())
                .category3Name(response.getCategory3Name())
                .category4Name(response.getCategory4Name())
                .price(response.getPrice())
                .imageUrl(response.getImageUrl())
                .affiliateUrl(response.getAffiliateUrl())
                .mallName(response.getMallName())
                .description(COMMERCE_PRODUCT_DESCRIPTION)
                .source(response.getSource())
                .externalProductId(response.getExternalProductId())
                .reviewCount(0)
                .rating(null)
                .visibleYn("Y")
                .build();
    }
}
