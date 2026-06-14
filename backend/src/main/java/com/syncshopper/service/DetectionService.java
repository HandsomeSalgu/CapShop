package com.syncshopper.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.syncshopper.common.exception.CustomException;
import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.domain.detection.AiAnalysisLog;
import com.syncshopper.domain.detection.AiProvider;
import com.syncshopper.domain.detection.Detection;
import com.syncshopper.domain.detection.DetectionStatus;
import com.syncshopper.dto.request.DetectionAnalyzeRequest;
import com.syncshopper.dto.response.AiAnalysisResult;
import com.syncshopper.dto.response.DetectionAnalyzeResponse;
import com.syncshopper.dto.response.DetectionDetailResponse;
import com.syncshopper.dto.response.DetectionHistoryResponse;
import com.syncshopper.dto.response.PageResponse;
import com.syncshopper.mapper.AiAnalysisLogMapper;
import com.syncshopper.mapper.DetectionMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

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
    private final ObjectMapper objectMapper;

    @Transactional
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
            detection.setTargetName(aiResult.getTargetName());
            detection.setCategoryName(aiResult.getCategoryName());
            detection.setBrand(aiResult.getBrand());
            detection.setModelName(aiResult.getModelName());
            detection.setConfidence(aiResult.getConfidence());
            detection.setStatus(DetectionStatus.SUCCESS);
            detectionMapper.updateDetectionResult(detection);

            saveAnalysisLog(detection.getDetectionId(), provider, requestPayload, aiResult.getRawResponseJson(),
                    true, null, startedAt);

            Detection savedDetection = detectionMapper.findByIdAndUserId(detection.getDetectionId(), userId);
            return toAnalyzeResponse(savedDetection == null ? detection : savedDetection);
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
                .confidence(detection.getConfidence())
                .status(detection.getStatus() == null ? null : detection.getStatus().name())
                .createdAt(detection.getCreatedAt())
                .build();
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
