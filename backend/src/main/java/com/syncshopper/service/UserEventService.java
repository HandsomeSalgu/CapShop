package com.syncshopper.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.syncshopper.common.exception.CustomException;
import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.domain.product.Product;
import com.syncshopper.domain.user.UserEvent;
import com.syncshopper.domain.user.UserEventType;
import com.syncshopper.dto.request.UserEventCreateRequest;
import com.syncshopper.dto.request.ProductDetailViewEventRequest;
import com.syncshopper.dto.request.ProductClickEventRequest;
import com.syncshopper.dto.response.UserEventResponse;
import com.syncshopper.mapper.ProductMapper;
import com.syncshopper.mapper.UserEventMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Map;

@RequiredArgsConstructor
@Service
public class UserEventService {

    private final UserEventMapper userEventMapper;
    private final ProductMapper productMapper;
    private final ProductUpsertService productUpsertService;
    private final ObjectMapper objectMapper;
    private final org.springframework.data.redis.core.RedisTemplate<String, Object> redisTemplate;

    @Transactional
    public UserEventResponse createUserEvent(Long userId, UserEventCreateRequest request) {
        UserEventType eventType = parseEventType(request.getEventType());
        Product product = validateProductForEvent(eventType, request.getProductId());

        UserEvent userEvent = createInternalEvent(
                userId,
                request.getProductId(),
                request.getRecommendationId(),
                eventType,
                request.getSourcePage(),
                request.getVideoId(),
                firstNonBlank(request.getCategoryName(), product == null ? null : product.getCategoryName()),
                firstNonBlank(request.getBrand(), product == null ? null : product.getBrand()),
                request.getTargetUrl(),
                request.getMetadataJson()
        );

        UserEvent savedEvent = userEventMapper.findById(userEvent.getEventId());
        return UserEventResponse.from(savedEvent);
    }

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
        return createInternalEvent(
                userId,
                productId,
                recommendationId,
                eventType,
                sourcePage,
                videoId,
                categoryName,
                brand,
                targetUrl,
                null
        );
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
            String targetUrl,
            Map<String, Object> metadataJson
    ) {
        UserEvent userEvent = UserEvent.builder()
                .userId(userId)
                .productId(productId)
                .recommendationId(recommendationId)
                .eventType(eventType)
                .sourcePage(sourcePage)
                .videoId(videoId)
                .categoryName(categoryName)
                .brand(brand)
                .targetUrl(targetUrl)
                .metadataJson(toMetadataJson(metadataJson))
                .build();

        userEventMapper.insertUserEvent(userEvent);
        
        // 새로운 활동(로그)이 생기면 기존 AI 추천 캐시를 삭제하여 즉시 업데이트되도록 만듦
        try {
            String redisKey = "user:" + userId + ":recommend_keywords";
            redisTemplate.delete(redisKey);
        } catch (Exception e) {
            System.err.println("Failed to delete redis cache for user: " + userId);
        }
        
        return userEvent;
    }

    private Product validateProductForEvent(UserEventType eventType, Long productId) {
        if (productId == null) {
            if (requiresProduct(eventType)) {
                throw new CustomException(ErrorCode.INVALID_INPUT_VALUE, "Product ID is required for this event type.");
            }
            return null;
        }

        Product product = productMapper.findById(productId);
        if (product == null) {
            throw new CustomException(ErrorCode.PRODUCT_NOT_FOUND);
        }
        return product;
    }

    private boolean requiresProduct(UserEventType eventType) {
        return eventType == UserEventType.PRODUCT_DETAIL_VIEW
                || eventType == UserEventType.PRODUCT_CLICK
                || eventType == UserEventType.AFFILIATE_CLICK
                || eventType == UserEventType.WISHLIST_ADD
                || eventType == UserEventType.WISHLIST_REMOVE
                || eventType == UserEventType.PRODUCT_IGNORE
                || eventType == UserEventType.PRODUCT_SAVE;
    }

    private UserEventType parseEventType(String value) {
        if (value == null || value.isBlank()) {
            throw new CustomException(ErrorCode.INVALID_INPUT_VALUE, "Event type is required.");
        }

        try {
            return UserEventType.valueOf(value.trim());
        } catch (IllegalArgumentException e) {
            throw new CustomException(ErrorCode.INVALID_INPUT_VALUE, "Unsupported event type: " + value);
        }
    }

    private String toMetadataJson(Map<String, Object> metadata) {
        if (metadata == null || metadata.isEmpty()) {
            return null;
        }

        try {
            return objectMapper.writeValueAsString(metadata);
        } catch (JsonProcessingException e) {
            throw new CustomException(ErrorCode.INTERNAL_SERVER_ERROR);
        }
    }

    private String firstNonBlank(String first, String second) {
        if (first != null && !first.isBlank()) {
            return first;
        }
        return second;
    }
}
