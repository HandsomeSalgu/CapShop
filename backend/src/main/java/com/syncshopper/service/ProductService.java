package com.syncshopper.service;

import com.syncshopper.common.exception.CustomException;
import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.domain.product.Product;
import com.syncshopper.dto.request.ProductSearchCondition;
import com.syncshopper.dto.response.PageResponse;
import com.syncshopper.dto.response.ProductDetailResponse;
import com.syncshopper.dto.response.ProductListResponse;
import com.syncshopper.mapper.ProductMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Set;

@RequiredArgsConstructor
@Service
public class ProductService {

    private static final int DEFAULT_PAGE = 1;
    private static final int DEFAULT_SIZE = 12;
    private static final int MAX_SIZE = 50;
    private static final int DEFAULT_LIMIT = 10;
    private static final String DEFAULT_SORT = "latest";
    private static final Set<String> SORT_TYPES = Set.of("latest", "priceAsc", "priceDesc", "rating", "popular");

    private final ProductMapper productMapper;

    public PageResponse<ProductListResponse> getProducts(ProductSearchCondition condition) {
        ProductSearchCondition normalizedCondition = normalizeCondition(condition);

        long totalCount = productMapper.countProducts(normalizedCondition);
        List<ProductListResponse> products = productMapper.findProducts(normalizedCondition).stream()
                .map(ProductListResponse::from)
                .toList();

        return PageResponse.of(
                products,
                normalizedCondition.getPage(),
                normalizedCondition.getSize(),
                totalCount
        );
    }

    public ProductDetailResponse getProductDetail(Long productId) {
        return ProductDetailResponse.from(findVisibleProduct(productId));
    }

    public List<ProductListResponse> getBestProducts(int limit) {
        return productMapper.findBestProducts(normalizeLimit(limit)).stream()
                .map(ProductListResponse::from)
                .toList();
    }

    public List<ProductListResponse> getHotProducts(int limit) {
        return productMapper.findHotProducts(normalizeLimit(limit)).stream()
                .map(ProductListResponse::from)
                .toList();
    }

    public List<ProductListResponse> getRelatedProducts(Long productId, int limit) {
        Product product = findVisibleProduct(productId);
        if (product.getCategoryName() == null) {
            return List.of();
        }

        return productMapper.findRelatedProducts(productId, product.getCategoryName(), normalizeLimit(limit)).stream()
                .map(ProductListResponse::from)
                .toList();
    }

    private ProductSearchCondition normalizeCondition(ProductSearchCondition condition) {
        ProductSearchCondition normalizedCondition = condition == null ? new ProductSearchCondition() : condition;

        int page = normalizedCondition.getPage() == null || normalizedCondition.getPage() < 1
                ? DEFAULT_PAGE
                : normalizedCondition.getPage();
        int size = normalizedCondition.getSize() == null || normalizedCondition.getSize() < 1
                ? DEFAULT_SIZE
                : Math.min(normalizedCondition.getSize(), MAX_SIZE);
        String sort = normalizedCondition.getSort() == null || normalizedCondition.getSort().isBlank()
                ? DEFAULT_SORT
                : normalizedCondition.getSort();

        if (!SORT_TYPES.contains(sort)) {
            sort = DEFAULT_SORT;
        }

        normalizedCondition.setPage(page);
        normalizedCondition.setSize(size);
        normalizedCondition.setSort(sort);
        normalizedCondition.setOffset((page - 1) * size);

        return normalizedCondition;
    }

    private int normalizeLimit(int limit) {
        if (limit < 1) {
            return DEFAULT_LIMIT;
        }
        return Math.min(limit, MAX_SIZE);
    }

    private Product findVisibleProduct(Long productId) {
        Product product = productMapper.findById(productId);
        if (product == null) {
            throw new CustomException(ErrorCode.PRODUCT_NOT_FOUND);
        }
        return product;
    }
}
