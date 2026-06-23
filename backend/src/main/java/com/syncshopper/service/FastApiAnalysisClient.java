package com.syncshopper.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.syncshopper.config.AiProperties;
import com.syncshopper.dto.request.AiCommerceQueryRequest;
import com.syncshopper.dto.request.DetectionAnalyzeRequest;
import com.syncshopper.dto.response.AiAnalysisResult;
import com.syncshopper.dto.response.AiCommerceQueryResponse;
import com.syncshopper.dto.response.CommerceProductResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@RequiredArgsConstructor
@Component
public class FastApiAnalysisClient {

    private final RestClient.Builder restClientBuilder;
    private final AiProperties aiProperties;
    private final ObjectMapper objectMapper;

    public AiAnalysisResult analyze(DetectionAnalyzeRequest request) {
        Map<String, Object> requestBody = toFastApiRequestBody(request);

        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        Duration timeout = Duration.ofMillis(aiProperties.getTimeoutMs());
        requestFactory.setConnectTimeout(timeout);
        requestFactory.setReadTimeout(timeout);

        byte[] responseBytes = restClientBuilder.clone()
                .baseUrl(aiProperties.getFastapiBaseUrl())
                .requestFactory(requestFactory)
                .build()
                .post()
                .uri(aiProperties.getAnalyzePath())
                .accept(MediaType.APPLICATION_JSON, MediaType.TEXT_PLAIN, MediaType.APPLICATION_OCTET_STREAM)
                .body(requestBody)
                .retrieve()
                .body(byte[].class);

        String responseBody = decodeResponseBody(responseBytes);
        try {
            JsonNode root = objectMapper.readTree(responseBody);
            return AiAnalysisResult.builder()
                    .targetName(root.path("target_name").asText(null))
                    .categoryName(root.path("category_name").asText(null))
                    .brand(root.path("brand").asText(null))
                    .modelName(root.path("model_name").asText(null))
                    .color(root.path("color").asText(null))
                    .shape(root.path("shape").asText(null))
                    .logoText(root.path("logo_text").asText(null))
                    .keyFeatures(parseKeyFeatures(root))
                    .confidence(root.path("confidence").isMissingNode() ? null : root.path("confidence").asDouble())
                    .ocrAnalysis(parseObject(root, "ocr_analysis"))
                    .visualAnalysis(parseObject(root, "visual_analysis"))
                    .searchIdentification(parseObject(root, "search_identification"))
                    .googleSearchResults(parseObjectList(root, "google_search_results"))
                    .googleSourceCounts(parseObject(root, "google_source_counts"))
                    .commerceQuery(parseCommerceQuery(root))
                    .products(parseProducts(root))
                    .rawResponseJson(responseBody)
                    .build();
        } catch (Exception e) {
            throw new IllegalStateException("Invalid FastAPI analysis response: " + truncate(responseBody), e);
        }
    }

    private String decodeResponseBody(byte[] responseBytes) {
        if (responseBytes == null || responseBytes.length == 0) {
            return "";
        }

        return new String(responseBytes, StandardCharsets.UTF_8);
    }

    private String truncate(String value) {
        if (value == null) {
            return "";
        }

        int maxLength = 500;
        if (value.length() <= maxLength) {
            return value;
        }

        return value.substring(0, maxLength) + "...";
    }

    private Map<String, Object> toFastApiRequestBody(DetectionAnalyzeRequest request) {
        Map<String, Object> requestBody = new LinkedHashMap<>();
        requestBody.put("video_id", request.getVideoId());
        requestBody.put("timestamp_sec", request.getTimestampSec());
        requestBody.put("image_base64", request.getImageBase64());
        requestBody.put("subtitle_text", request.getSubtitleText());
        return requestBody;
    }

    private AiCommerceQueryResponse parseCommerceQuery(JsonNode root) throws Exception {
        JsonNode commerceQuery = root.path("commerce_query");
        if (commerceQuery.isMissingNode() || commerceQuery.isNull()) {
            return null;
        }

        return objectMapper.treeToValue(commerceQuery, AiCommerceQueryResponse.class);
    }

    private List<CommerceProductResponse> parseProducts(JsonNode root) throws Exception {
        JsonNode products = root.path("products");
        if (products.isMissingNode() || products.isNull() || !products.isArray()) {
            return List.of();
        }

        return objectMapper.readerForListOf(CommerceProductResponse.class).readValue(products);
    }

    private List<String> parseKeyFeatures(JsonNode root) throws Exception {
        JsonNode keyFeatures = root.path("key_features");
        if (keyFeatures.isMissingNode() || keyFeatures.isNull() || !keyFeatures.isArray()) {
            return List.of();
        }

        return objectMapper.readerForListOf(String.class).readValue(keyFeatures);
    }

    private Map<String, Object> parseObject(JsonNode root, String fieldName) throws Exception {
        JsonNode node = root.path(fieldName);
        if (node.isMissingNode() || node.isNull() || !node.isObject()) {
            return Map.of();
        }

        return objectMapper.readerForMapOf(Object.class).readValue(node);
    }

    private List<Map<String, Object>> parseObjectList(JsonNode root, String fieldName) throws Exception {
        JsonNode node = root.path(fieldName);
        if (node.isMissingNode() || node.isNull() || !node.isArray()) {
            return List.of();
        }

        return objectMapper.readerForListOf(Map.class).readValue(node);
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
