package com.syncshopper.service;

import com.syncshopper.common.exception.CustomException;
import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.domain.product.Product;
import com.syncshopper.domain.user.UserEvent;
import com.syncshopper.domain.user.UserEventType;
import com.syncshopper.dto.request.ProductDetailViewEventRequest;
import com.syncshopper.dto.response.UserEventResponse;
import com.syncshopper.mapper.ProductMapper;
import com.syncshopper.mapper.UserEventMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@RequiredArgsConstructor
@Service
public class UserEventService {

    private final UserEventMapper userEventMapper;
    private final ProductMapper productMapper;

    public UserEventResponse createProductDetailViewEvent(Long userId, ProductDetailViewEventRequest request) {
        Product product = productMapper.findById(request.getProductId());
        if (product == null) {
            throw new CustomException(ErrorCode.PRODUCT_NOT_FOUND);
        }

        UserEvent userEvent = UserEvent.builder()
                .userId(userId)
                .productId(request.getProductId())
                .eventType(UserEventType.PRODUCT_DETAIL_VIEW)
                .sourcePage(request.getSourcePage())
                .targetUrl(null)
                .metadataJson(null)
                .build();

        userEventMapper.insertUserEvent(userEvent);

        UserEvent savedEvent = userEventMapper.findById(userEvent.getEventId());
        return UserEventResponse.from(savedEvent);
    }
}
