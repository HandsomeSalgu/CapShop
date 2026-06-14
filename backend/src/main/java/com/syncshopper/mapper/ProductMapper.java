package com.syncshopper.mapper;

import com.syncshopper.domain.product.Product;
import com.syncshopper.dto.request.ProductSearchCondition;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface ProductMapper {

    List<Product> findProducts(ProductSearchCondition condition);

    long countProducts(ProductSearchCondition condition);

    Product findById(@Param("productId") Long productId);

    Product findBySourceAndAffiliateUrl(@Param("source") String source,
                                        @Param("affiliateUrl") String affiliateUrl);

    int insertCommerceProduct(Product product);

    List<Product> findBestProducts(@Param("limit") int limit);

    List<Product> findHotProducts(@Param("limit") int limit);

    List<Product> findRelatedProducts(
            @Param("productId") Long productId,
            @Param("categoryId") Long categoryId,
            @Param("limit") int limit
    );
}
