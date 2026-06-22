package com.syncshopper.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.syncshopper.common.exception.CustomException;
import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.domain.product.Product;
import com.syncshopper.domain.user.UserEvent;
import com.syncshopper.domain.user.UserEventType;
import com.syncshopper.dto.request.ProductDetailViewEventRequest;
import com.syncshopper.dto.request.ProductClickEventRequest;
import com.syncshopper.dto.response.UserEventResponse;
import com.syncshopper.mapper.ProductMapper;
import com.syncshopper.mapper.UserEventMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.LinkedHashMap;
import java.util.Map;

@RequiredArgsConstructor
@Service
public class UserEventService {

    private final UserEventMapper userEventMapper;
    private final ProductMapper productMapper;
    private final ProductUpsertService productUpsertService;
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Transactional
    public UserEventResponse createProductDetailViewEvent(Long userId, ProductDetailViewEventRequest request) {
        Long productId = request.getProductId();

        if (request.getProduct() != null) {
            productId = productUpsertService.upsertCommerceProduct(request.getProduct());
        }

        if (productId == null) {
            throw new CustomException(ErrorCode.PRODUCT_NOT_FOUND);
        }

        Product product = productMapper.findById(productId);
        if (product == null) {
            throw new CustomException(ErrorCode.PRODUCT_NOT_FOUND);
        }

        UserEvent userEvent = createInternalEvent(
                userId,
                productId,
                null,
                UserEventType.PRODUCT_DETAIL_VIEW,
                request.getSourcePage(),
                null,
                product.getCategoryName(),
                product.getBrand(),
                product.getAffiliateUrl()
        );

        UserEvent savedEvent = userEventMapper.findById(userEvent.getEventId());
        return UserEventResponse.from(savedEvent);
    }

    @Transactional
    public UserEventResponse createProductClickEvent(Long userId, ProductClickEventRequest request) {
        Product product = productMapper.findById(request.getProductId());
        if (product == null) {
            throw new CustomException(ErrorCode.PRODUCT_NOT_FOUND);
        }

        UserEvent userEvent = createInternalEvent(
                userId,
                request.getProductId(),
                request.getRecommendationId(),
                UserEventType.PRODUCT_CLICK,
                request.getSourcePage(),
                request.getVideoId(),
                request.getCategoryName(),
                request.getBrand(),
                product.getAffiliateUrl()
        );

        UserEvent savedEvent = userEventMapper.findById(userEvent.getEventId());
        return UserEventResponse.from(savedEvent);
    }

    public UserEvent createInternalEvent(
            Long userId,
            Long productId,
            Long recommendationId,
            UserEventType eventType,
            String sourcePage,
            String videoId,
            String categoryName,
            String brand,
            String targetUrl
    ) {
        UserEvent userEvent = UserEvent.builder()
                .userId(userId)
                .productId(productId)
                .eventType(eventType)
                .sourcePage(sourcePage)
                .targetUrl(targetUrl)
                .metadataJson(toMetadataJson(recommendationId, videoId, categoryName, brand))
                .build();

        userEventMapper.insertUserEvent(userEvent);
        return userEvent;
    }

    private String toMetadataJson(Long recommendationId, String videoId, String categoryName, String brand) {
        Map<String, Object> metadata = new LinkedHashMap<>();
        putIfNotNull(metadata, "recommendationId", recommendationId);
        putIfNotBlank(metadata, "videoId", videoId);
        putIfNotBlank(metadata, "categoryName", categoryName);
        putIfNotBlank(metadata, "brand", brand);

        if (metadata.isEmpty()) {
            return null;
        }

        try {
            return objectMapper.writeValueAsString(metadata);
        } catch (JsonProcessingException e) {
            throw new CustomException(ErrorCode.INTERNAL_SERVER_ERROR);
        }
    }

    private void putIfNotNull(Map<String, Object> metadata, String key, Object value) {
        if (value != null) {
            metadata.put(key, value);
        }
    }

    private void putIfNotBlank(Map<String, Object> metadata, String key, String value) {
        if (value != null && !value.isBlank()) {
            metadata.put(key, value);
        }
    }
}
