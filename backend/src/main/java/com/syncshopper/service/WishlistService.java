package com.syncshopper.service;

import com.syncshopper.common.exception.CustomException;
import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.domain.product.Product;
import com.syncshopper.domain.user.UserEventType;
import com.syncshopper.domain.user.Wishlist;
import com.syncshopper.dto.response.PageResponse;
import com.syncshopper.dto.response.WishlistProductResponse;
import com.syncshopper.mapper.ProductMapper;
import com.syncshopper.mapper.WishlistMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@RequiredArgsConstructor
@Service
public class WishlistService {

    private static final int DEFAULT_PAGE = 1;
    private static final int DEFAULT_SIZE = 12;
    private static final int MAX_SIZE = 50;

    private final WishlistMapper wishlistMapper;
    private final ProductMapper productMapper;
    private final UserEventService userEventService;

    public PageResponse<WishlistProductResponse> getMyWishlist(Long userId, int page, int size) {
        PageRequest pageRequest = normalizePage(page, size);

        long totalCount = wishlistMapper.countWishlistProducts(userId);
        List<WishlistProductResponse> products = wishlistMapper.findWishlistProducts(
                userId,
                pageRequest.offset(),
                pageRequest.size()
        );

        return PageResponse.of(products, pageRequest.page(), pageRequest.size(), totalCount);
    }

    public boolean checkWishlist(Long userId, Long productId) {
        return wishlistMapper.findByUserIdAndProductId(userId, productId) != null;
    }

    @Transactional
    public void addWishlist(Long userId, Long productId, String sourcePage) {
        Product product = ensureVisibleProduct(productId);

        Wishlist existingWishlist = wishlistMapper.findByUserIdAndProductId(userId, productId);
        if (existingWishlist != null) {
            return;
        }

        wishlistMapper.insertWishlist(Wishlist.builder()
                .userId(userId)
                .productId(productId)
                .build());
        userEventService.createInternalEvent(
                userId,
                productId,
                null,
                UserEventType.WISHLIST_ADD,
                sourcePage,
                null,
                product.getCategoryName(),
                product.getBrand(),
                product.getAffiliateUrl()
        );
    }

    @Transactional
    public void removeWishlist(Long userId, Long productId, String sourcePage) {
        Product product = ensureVisibleProduct(productId);

        int deletedCount = wishlistMapper.deleteWishlist(userId, productId);
        if (deletedCount < 1) {
            return;
        }

        userEventService.createInternalEvent(
                userId,
                productId,
                null,
                UserEventType.WISHLIST_REMOVE,
                sourcePage,
                null,
                product.getCategoryName(),
                product.getBrand(),
                product.getAffiliateUrl()
        );
    }

    private Product ensureVisibleProduct(Long productId) {
        Product product = productMapper.findById(productId);
        if (product == null) {
            throw new CustomException(ErrorCode.PRODUCT_NOT_FOUND);
        }
        return product;
    }

    private PageRequest normalizePage(int page, int size) {
        int normalizedPage = page < 1 ? DEFAULT_PAGE : page;
        int normalizedSize = size < 1 ? DEFAULT_SIZE : Math.min(size, MAX_SIZE);
        return new PageRequest(normalizedPage, normalizedSize, (normalizedPage - 1) * normalizedSize);
    }

    private record PageRequest(int page, int size, int offset) {
    }
}
