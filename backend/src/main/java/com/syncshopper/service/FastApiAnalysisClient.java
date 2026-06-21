package com.syncshopper.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.syncshopper.config.AiProperties;
import com.syncshopper.dto.request.AiCommerceQueryRequest;
import com.syncshopper.dto.request.DetectionAnalyzeRequest;
import com.syncshopper.dto.response.AiAnalysisResult;
import com.syncshopper.dto.response.AiCommerceQueryResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.Map;

@RequiredArgsConstructor
@Component
public class FastApiAnalysisClient {

    private final RestClient.Builder restClientBuilder;
    private final AiProperties aiProperties;
    private final ObjectMapper objectMapper;

    public AiAnalysisResult analyze(DetectionAnalyzeRequest request) {
        Map<String, Object> requestBody = new LinkedHashMap<>();
        requestBody.put("video_id", request.getVideoId());
        requestBody.put("timestamp_sec", request.getTimestampSec());
        requestBody.put("image_base64", request.getImageBase64());
        requestBody.put("subtitle_text", request.getSubtitleText());

        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        Duration timeout = Duration.ofMillis(aiProperties.getTimeoutMs());
        requestFactory.setConnectTimeout(timeout);
        requestFactory.setReadTimeout(timeout);

        String responseBody = restClientBuilder.clone()
                .baseUrl(aiProperties.getFastapiBaseUrl())
                .requestFactory(requestFactory)
                .build()
                .post()
                .uri(aiProperties.getAnalyzePath())
                .body(requestBody)
                .retrieve()
                .body(String.class);

        try {
            JsonNode root = objectMapper.readTree(responseBody);
            return AiAnalysisResult.builder()
                    .targetName(root.path("target_name").asText(null))
                    .categoryName(root.path("category_name").asText(null))
                    .brand(root.path("brand").asText(null))
                    .modelName(root.path("model_name").asText(null))
                    .confidence(root.path("confidence").isMissingNode() ? null : root.path("confidence").asDouble())
                    .rawResponseJson(responseBody)
                    .build();
        } catch (Exception e) {
            throw new IllegalStateException("Invalid FastAPI analysis response.", e);
        }
    }

    public AiCommerceQueryResponse generateCommerceQuery(AiCommerceQueryRequest request) {
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        Duration timeout = Duration.ofMillis(aiProperties.getTimeoutMs());
        requestFactory.setConnectTimeout(timeout);
        requestFactory.setReadTimeout(timeout);

        return restClientBuilder.clone()
                .baseUrl(aiProperties.getFastapiBaseUrl())
                .requestFactory(requestFactory)
                .build()
                .post()
                .uri(aiProperties.getCommerceQueryPath())
                .body(request)
                .retrieve()
                .body(AiCommerceQueryResponse.class);
    }
}
