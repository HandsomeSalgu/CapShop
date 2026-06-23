package com.syncshopper.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.syncshopper.common.exception.CustomException;
import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.domain.detection.AiAnalysisLog;
import com.syncshopper.domain.detection.AiProvider;
import com.syncshopper.domain.detection.Detection;
import com.syncshopper.domain.detection.DetectionStatus;
import com.syncshopper.dto.request.AiCommerceQueryRequest;
import com.syncshopper.dto.request.DetectionAnalyzeRequest;
import com.syncshopper.dto.response.AiAnalysisResult;
import com.syncshopper.dto.response.AiCommerceQueryResponse;
import com.syncshopper.dto.response.CommerceProductResponse;
import com.syncshopper.dto.response.DetectionAnalyzeResponse;
import com.syncshopper.dto.response.DetectionDetailResponse;
import com.syncshopper.dto.response.DetectionHistoryResponse;
import com.syncshopper.dto.response.PageResponse;
import com.syncshopper.mapper.AiAnalysisLogMapper;
import com.syncshopper.mapper.DetectionMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@RequiredArgsConstructor
@Service
public class DetectionService {

    private static final int DEFAULT_PAGE = 1;
    private static final int DEFAULT_SIZE = 12;
    private static final int MAX_SIZE = 50;
    private static final int SUBTITLE_SUMMARY_MAX_LENGTH = 500;

    private final DetectionMapper detectionMapper;
    private final AiAnalysisLogMapper aiAnalysisLogMapper;
    private final AiAnalysisService aiAnalysisService;
    private final CommerceService commerceService;
    private final ObjectMapper objectMapper;

    public DetectionAnalyzeResponse analyzeFrame(Long userId, DetectionAnalyzeRequest request) {
        String imageHash = sha256(request.getImageBase64());
        Detection detection = Detection.builder()
                .userId(userId)
                .videoId(request.getVideoId())
                .timestampSec(request.getTimestampSec())
                .imageHash(imageHash)
                .subtitleSummary(summarizeSubtitle(request.getSubtitleText()))
                .status(DetectionStatus.PENDING)
                .build();

        detectionMapper.insertDetection(detection);

        long startedAt = System.currentTimeMillis();
        AiProvider provider = aiAnalysisService.getCurrentProvider();
        String requestPayload = toJson(sanitizedRequestPayload(request, imageHash));

        try {
            AiAnalysisResult aiResult = aiAnalysisService.analyze(request);
            log.info(
                    "[SyncShopper AI Detection Result] detectionId={} videoId={} timestampSec={} targetName='{}' categoryName='{}' brand='{}' modelName='{}' color='{}' shape='{}' logoText='{}' keyFeatures={} confidence={} rawResponse={}",
                    detection.getDetectionId(),
                    request.getVideoId(),
                    request.getTimestampSec(),
                    aiResult.getTargetName(),
                    aiResult.getCategoryName(),
                    aiResult.getBrand(),
                    aiResult.getModelName(),
                    aiResult.getColor(),
                    aiResult.getShape(),
                    aiResult.getLogoText(),
                    aiResult.getKeyFeatures(),
                    aiResult.getConfidence(),
                    aiResult.getRawResponseJson()
            );

            detection.setTargetName(aiResult.getTargetName());
            detection.setCategoryName(aiResult.getCategoryName());
            detection.setBrand(aiResult.getBrand());
            detection.setModelName(aiResult.getModelName());
            detection.setColor(aiResult.getColor());
            detection.setShape(aiResult.getShape());
            detection.setLogoText(aiResult.getLogoText());
            detection.setKeyFeaturesJson(toJson(aiResult.getKeyFeatures() == null ? List.of() : aiResult.getKeyFeatures()));
            detection.setConfidence(aiResult.getConfidence());
            detection.setStatus(DetectionStatus.SUCCESS);
            detectionMapper.updateDetectionResult(detection);

            saveAnalysisLog(detection.getDetectionId(), provider, requestPayload, aiResult.getRawResponseJson(),
                    true, null, startedAt);

            Detection savedDetection = detectionMapper.findByIdAndUserId(detection.getDetectionId(), userId);
            Detection responseDetection = savedDetection == null ? detection : savedDetection;
            return enrichWithCommerce(responseDetection, request, aiResult);
        } catch (Exception e) {
            detectionMapper.updateDetectionFailed(detection.getDetectionId(), DetectionStatus.FAILED);
            saveAnalysisLog(detection.getDetectionId(), provider, requestPayload, null, false, e.getMessage(), startedAt);
            throw new CustomException(ErrorCode.AI_ANALYSIS_FAILED);
        }
    }

    public DetectionDetailResponse getDetectionDetail(Long userId, Long detectionId) {
        Detection detection = detectionMapper.findByIdAndUserId(detectionId, userId);
        if (detection == null) {
            throw new CustomException(ErrorCode.DETECTION_NOT_FOUND);
        }
        return DetectionDetailResponse.builder()
                .detectionId(detection.getDetectionId())
                .videoId(detection.getVideoId())
                .timestampSec(detection.getTimestampSec())
                .subtitleSummary(detection.getSubtitleSummary())
                .targetName(detection.getTargetName())
                .categoryName(detection.getCategoryName())
                .brand(detection.getBrand())
                .modelName(detection.getModelName())
                .color(detection.getColor())
                .shape(detection.getShape())
                .logoText(detection.getLogoText())
                .keyFeatures(keyFeaturesFromJson(detection.getKeyFeaturesJson()))
                .confidence(detection.getConfidence())
                .status(detection.getStatus() == null ? null : detection.getStatus().name())
                .createdAt(detection.getCreatedAt())
                .build();
    }

    public PageResponse<DetectionHistoryResponse> getMyDetections(Long userId, int page, int size) {
        PageRequest pageRequest = normalizePage(page, size);
        long totalCount = detectionMapper.countMyDetections(userId);
        List<DetectionHistoryResponse> detections = detectionMapper.findMyDetections(
                userId,
                pageRequest.offset(),
                pageRequest.size()
        );
        return PageResponse.of(detections, pageRequest.page(), pageRequest.size(), totalCount);
    }

    private DetectionAnalyzeResponse toAnalyzeResponse(Detection detection) {
        return DetectionAnalyzeResponse.builder()
                .detectionId(detection.getDetectionId())
                .videoId(detection.getVideoId())
                .timestampSec(detection.getTimestampSec())
                .targetName(detection.getTargetName())
                .categoryName(detection.getCategoryName())
                .brand(detection.getBrand())
                .modelName(detection.getModelName())
                .color(detection.getColor())
                .shape(detection.getShape())
                .logoText(detection.getLogoText())
                .keyFeatures(keyFeaturesFromJson(detection.getKeyFeaturesJson()))
                .confidence(detection.getConfidence())
                .status(detection.getStatus() == null ? null : detection.getStatus().name())
                .createdAt(detection.getCreatedAt())
                .detection(toDetectionSummary(detection))
                .products(List.of())
                .message("상품 분석이 완료되었습니다.")
                .build();
    }

    private DetectionAnalyzeResponse enrichWithCommerce(
            Detection detection,
            DetectionAnalyzeRequest request,
            AiAnalysisResult aiResult
    ) {
        if (aiResult.getCommerceQuery() != null) {
            return enrichWithIntegratedCommerce(detection, aiResult);
        }

        return enrichWithLegacyCommerce(detection, request);
    }

    private DetectionAnalyzeResponse enrichWithIntegratedCommerce(Detection detection, AiAnalysisResult aiResult) {
        DetectionAnalyzeResponse response = toAnalyzeResponse(detection);
        AiCommerceQueryResponse commerceQuery = aiResult.getCommerceQuery();
        List<CommerceProductResponse> products = List.of();

        if (commerceQuery != null && commerceQuery.getPrimaryQuery() != null && !commerceQuery.getPrimaryQuery().isBlank()) {
            try {
                products = commerceService.getTop3Products(commerceQuery.getPrimaryQuery());
            } catch (RuntimeException e) {
                log.warn(
                        "[SyncShopper Commerce Products Result] primary query search failed detectionId={} primaryQuery='{}'",
                        detection.getDetectionId(),
                        commerceQuery.getPrimaryQuery(),
                        e
                );
            }
        }

        log.info(
                "[SyncShopper AI Commerce Query Result] detectionId={} primaryQuery='{}' fallbackQueries={} normalizedBrand='{}' normalizedModel='{}' normalizedCategory='{}' queryConfidence={} reason='{}'",
                detection.getDetectionId(),
                commerceQuery.getPrimaryQuery(),
                commerceQuery.getFallbackQueries(),
                commerceQuery.getNormalizedBrand(),
                commerceQuery.getNormalizedModel(),
                commerceQuery.getNormalizedCategory(),
                commerceQuery.getQueryConfidence(),
                commerceQuery.getReason()
        );

        log.info(
                "[SyncShopper Commerce Products Result] detectionId={} source=PRIMARY_QUERY primaryQuery='{}' productCount={} products={}",
                detection.getDetectionId(),
                commerceQuery == null ? null : commerceQuery.getPrimaryQuery(),
                products.size(),
                products.stream()
                        .map(this::productDebugPayload)
                        .toList()
        );

        response.setCommerceQuery(commerceQuery);
        response.setOcrAnalysis(aiResult.getOcrAnalysis());
        response.setVisualAnalysis(aiResult.getVisualAnalysis());
        response.setSearchIdentification(aiResult.getSearchIdentification());
        response.setGoogleSearchResults(aiResult.getGoogleSearchResults());
        response.setGoogleSourceCounts(aiResult.getGoogleSourceCounts());
        response.setProducts(products);
        response.setMessage(products.isEmpty()
                ? "상품 분석은 완료되었지만 검색된 상품이 없습니다."
                : "상품 분석이 완료되었습니다.");
        return response;
    }

    private DetectionAnalyzeResponse enrichWithLegacyCommerce(Detection detection, DetectionAnalyzeRequest request) {
        DetectionAnalyzeResponse response = toAnalyzeResponse(detection);

        AiCommerceQueryResponse commerceQuery;
        try {
            commerceQuery = aiAnalysisService.generateCommerceQuery(AiCommerceQueryRequest.builder()
                    .targetName(detection.getTargetName())
                    .categoryName(detection.getCategoryName())
                    .brand(detection.getBrand())
                    .modelName(detection.getModelName())
                    .confidence(detection.getConfidence())
                    .subtitleText(request.getSubtitleText())
                    .videoId(request.getVideoId())
                    .timestampSec(request.getTimestampSec())
                    .build());
        } catch (RuntimeException e) {
            log.warn("[SyncShopper AI Commerce Query Result] query generation failed detectionId={}", detection.getDetectionId(), e);
            response.setCommerceQuery(null);
            response.setProducts(List.of());
            response.setMessage("상품 분석은 완료되었지만 검색어 생성에 실패했습니다.");
            return response;
        }

        log.info(
                "[SyncShopper AI Commerce Query Result] detectionId={} primaryQuery='{}' fallbackQueries={} normalizedBrand='{}' normalizedModel='{}' normalizedCategory='{}' queryConfidence={} reason='{}'",
                detection.getDetectionId(),
                commerceQuery.getPrimaryQuery(),
                commerceQuery.getFallbackQueries(),
                commerceQuery.getNormalizedBrand(),
                commerceQuery.getNormalizedModel(),
                commerceQuery.getNormalizedCategory(),
                commerceQuery.getQueryConfidence(),
                commerceQuery.getReason()
        );

        response.setCommerceQuery(commerceQuery);

        List<CommerceProductResponse> products;
        try {
            products = commerceService.searchTop3(commerceQuery);
        } catch (RuntimeException e) {
            log.warn("[SyncShopper Commerce Products Result] search failed detectionId={}", detection.getDetectionId(), e);
            response.setProducts(List.of());
            response.setMessage("상품 분석은 완료되었지만 쇼핑 검색에 실패했습니다.");
            return response;
        }

        log.info(
                "[SyncShopper Commerce Products Result] detectionId={} productCount={} products={}",
                detection.getDetectionId(),
                products.size(),
                products.stream()
                        .map(this::productDebugPayload)
                        .toList()
        );

        response.setProducts(products);
        response.setMessage(products.isEmpty()
                ? "상품 분석은 완료되었지만 검색된 상품이 없습니다."
                : "상품 분석이 완료되었습니다.");
        return response;
    }

    private DetectionAnalyzeResponse.DetectionSummary toDetectionSummary(Detection detection) {
        return DetectionAnalyzeResponse.DetectionSummary.builder()
                .targetName(detection.getTargetName())
                .categoryName(detection.getCategoryName())
                .brand(detection.getBrand())
                .modelName(detection.getModelName())
                .color(detection.getColor())
                .shape(detection.getShape())
                .logoText(detection.getLogoText())
                .keyFeatures(keyFeaturesFromJson(detection.getKeyFeaturesJson()))
                .confidence(detection.getConfidence())
                .build();
    }

    private Map<String, Object> productDebugPayload(CommerceProductResponse product) {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("productId", product.getProductId());
        payload.put("title", product.getTitle());
        payload.put("brand", product.getBrand());
        payload.put("categoryName", product.getCategoryName());
        payload.put("price", product.getPrice());
        payload.put("mallName", product.getMallName());
        return payload;
    }

    private void saveAnalysisLog(
            Long detectionId,
            AiProvider provider,
            String requestPayload,
            String responsePayload,
            boolean success,
            String errorMessage,
            long startedAt
    ) {
        long latencyMs = System.currentTimeMillis() - startedAt;
        aiAnalysisLogMapper.insertAiAnalysisLog(AiAnalysisLog.builder()
                .detectionId(detectionId)
                .apiProvider(provider)
                .requestPayload(requestPayload)
                .responsePayload(responsePayload)
                .successYn(success ? "Y" : "N")
                .errorMessage(errorMessage)
                .latencyMs((int) Math.min(latencyMs, Integer.MAX_VALUE))
                .build());
    }

    private Map<String, Object> sanitizedRequestPayload(DetectionAnalyzeRequest request, String imageHash) {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("videoId", request.getVideoId());
        payload.put("timestampSec", request.getTimestampSec());
        payload.put("subtitleText", request.getSubtitleText());
        payload.put("imageHash", imageHash);
        return payload;
    }

    private String toJson(Object value) {
        try {
            return objectMapper.writeValueAsString(value);
        } catch (JsonProcessingException e) {
            return "{}";
        }
    }

    private List<String> keyFeaturesFromJson(String value) {
        if (value == null || value.isBlank()) {
            return List.of();
        }

        try {
            return objectMapper.readerForListOf(String.class).readValue(value);
        } catch (Exception e) {
            return List.of();
        }
    }

    private String sha256(String value) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hashed = digest.digest(value.getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(hashed);
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException("SHA-256 algorithm is not available.", e);
        }
    }

    private String summarizeSubtitle(String subtitleText) {
        if (subtitleText == null || subtitleText.isBlank()) {
            return null;
        }
        if (subtitleText.length() <= SUBTITLE_SUMMARY_MAX_LENGTH) {
            return subtitleText;
        }
        return subtitleText.substring(0, SUBTITLE_SUMMARY_MAX_LENGTH);
    }

    private PageRequest normalizePage(int page, int size) {
        int normalizedPage = page < 1 ? DEFAULT_PAGE : page;
        int normalizedSize = size < 1 ? DEFAULT_SIZE : Math.min(size, MAX_SIZE);
        return new PageRequest(normalizedPage, normalizedSize, (normalizedPage - 1) * normalizedSize);
    }

    private record PageRequest(int page, int size, int offset) {
    }
}
