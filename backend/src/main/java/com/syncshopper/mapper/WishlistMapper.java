package com.syncshopper.mapper;

import com.syncshopper.domain.user.Wishlist;
import com.syncshopper.dto.response.WishlistProductResponse;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface WishlistMapper {

    Wishlist findByUserIdAndProductId(
            @Param("userId") Long userId,
            @Param("productId") Long productId
    );

    int insertWishlist(Wishlist wishlist);

    int deleteWishlist(
            @Param("userId") Long userId,
            @Param("productId") Long productId
    );

    List<WishlistProductResponse> findWishlistProducts(
            @Param("userId") Long userId,
            @Param("keyword") String keyword,
            @Param("category") String category,
            @Param("offset") int offset,
            @Param("size") int size
    );

    long countWishlistProducts(
            @Param("userId") Long userId,
            @Param("keyword") String keyword,
            @Param("category") String category
    );
}
