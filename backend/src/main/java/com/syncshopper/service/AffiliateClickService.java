package com.syncshopper.service;

import com.syncshopper.common.exception.CustomException;
import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.domain.product.Product;
import com.syncshopper.domain.user.AffiliateClick;
import com.syncshopper.domain.user.UserEventType;
import com.syncshopper.dto.request.AffiliateClickRequest;
import com.syncshopper.dto.response.AffiliateClickResponse;
import com.syncshopper.mapper.AffiliateClickMapper;
import com.syncshopper.mapper.ProductMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;

@RequiredArgsConstructor
@Service
public class AffiliateClickService {

    private final AffiliateClickMapper affiliateClickMapper;
    private final ProductMapper productMapper;
    private final UserEventService userEventService;

    @Transactional
    public AffiliateClickResponse createAffiliateClick(Long userId, AffiliateClickRequest request) {
        Product product = productMapper.findById(request.getProductId());
        if (product == null) {
            throw new CustomException(ErrorCode.PRODUCT_NOT_FOUND);
        }

        AffiliateClick affiliateClick = AffiliateClick.builder()
                .userId(userId)
                .productId(request.getProductId())
                .recommendationId(request.getRecommendationId())
                .source(request.getSource())
                .clickedAt(LocalDateTime.now())
                .build();

        affiliateClickMapper.insertAffiliateClick(affiliateClick);
        userEventService.createInternalEvent(
                userId,
                request.getProductId(),
                request.getRecommendationId(),
                UserEventType.AFFILIATE_CLICK,
                request.getSource(),
                request.getVideoId(),
                request.getCategoryName(),
                request.getBrand(),
                request.getTargetUrl()
        );

        return AffiliateClickResponse.from(affiliateClick);
    }
}
