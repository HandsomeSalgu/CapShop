package com.syncshopper.service;

import com.syncshopper.dto.request.DetectionAnalyzeRequest;
import com.syncshopper.dto.request.AiCommerceQueryRequest;
import com.syncshopper.dto.response.AiAnalysisResult;
import com.syncshopper.dto.response.AiCommerceQueryResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Stream;

@RequiredArgsConstructor
@Service
public class MockAiAnalysisService {

    public AiAnalysisResult analyze(DetectionAnalyzeRequest request) {
        String keywordSource = ((request.getSubtitleText() == null ? "" : request.getSubtitleText())
                + " " + request.getVideoId()).toLowerCase();

        if (keywordSource.contains("airpods")) {
            return AiAnalysisResult.builder()
                    .targetName("Apple AirPods Pro")
                    .categoryName("Electronics")
                    .brand("Apple")
                    .modelName("AirPods Pro")
                    .color("white")
                    .shape("wireless earbuds with charging case")
                    .logoText(null)
                    .keyFeatures(List.of("white earbuds", "rounded charging case", "in-ear tips"))
                    .confidence(0.93)
                    .rawResponseJson("{\"target_name\":\"Apple AirPods Pro\",\"category_name\":\"Electronics\",\"brand\":\"Apple\",\"model_name\":\"AirPods Pro\",\"color\":\"white\",\"shape\":\"wireless earbuds with charging case\",\"logo_text\":null,\"key_features\":[\"white earbuds\",\"rounded charging case\",\"in-ear tips\"],\"confidence\":0.93}")
                    .build();
        }

        if (keywordSource.contains("nike")) {
            return AiAnalysisResult.builder()
                    .targetName("Nike sneakers")
                    .categoryName("Fashion")
                    .brand("Nike")
                    .modelName("Air Force 1")
                    .color("white")
                    .shape("low-top sneakers")
                    .logoText("Nike")
                    .keyFeatures(List.of("low-top silhouette", "white leather upper", "side swoosh logo"))
                    .confidence(0.91)
                    .rawResponseJson("{\"target_name\":\"Nike sneakers\",\"category_name\":\"Fashion\",\"brand\":\"Nike\",\"model_name\":\"Air Force 1\",\"color\":\"white\",\"shape\":\"low-top sneakers\",\"logo_text\":\"Nike\",\"key_features\":[\"low-top silhouette\",\"white leather upper\",\"side swoosh logo\"],\"confidence\":0.91}")
                    .build();
        }

        return AiAnalysisResult.builder()
                .targetName("Nike sneakers")
                .categoryName("Fashion")
                .brand("Nike")
                .modelName("Air Force 1")
                .color("white")
                .shape("low-top sneakers")
                .logoText("Nike")
                .keyFeatures(List.of("low-top silhouette", "white leather upper", "side swoosh logo"))
                .confidence(0.91)
                .rawResponseJson("{\"target_name\":\"Nike sneakers\",\"category_name\":\"Fashion\",\"brand\":\"Nike\",\"model_name\":\"Air Force 1\",\"color\":\"white\",\"shape\":\"low-top sneakers\",\"logo_text\":\"Nike\",\"key_features\":[\"low-top silhouette\",\"white leather upper\",\"side swoosh logo\"],\"confidence\":0.91}")
                .build();
    }

    public AiCommerceQueryResponse generateCommerceQuery(AiCommerceQueryRequest request) {
        String brand = request.getBrand();
        String model = request.getModelName();
        String target = request.getTargetName();
        String primaryQuery = joinNonBlank(brand, model);
        if (primaryQuery == null) {
            primaryQuery = target == null || target.isBlank() ? "Nike Air Force 1" : target;
        }

        return AiCommerceQueryResponse.builder()
                .primaryQuery(primaryQuery)
                .fallbackQueries(Stream.of(
                        nullToDefault(target, primaryQuery),
                        joinNonBlank(brand, target),
                        joinNonBlank(brand, request.getCategoryName())
                ).filter(value -> value != null && !value.isBlank()).distinct().toList())
                .normalizedBrand(brand)
                .normalizedModel(model)
                .normalizedCategory(request.getCategoryName())
                .queryConfidence(0.9)
                .reason("Mock commerce query generated from detection result.")
                .build();
    }

    private String joinNonBlank(String first, String second) {
        String normalizedFirst = first == null ? "" : first.trim();
        String normalizedSecond = second == null ? "" : second.trim();
        String joined = (normalizedFirst + " " + normalizedSecond).trim();
        return joined.isBlank() ? null : joined;
    }

    private String nullToDefault(String value, String defaultValue) {
        return value == null || value.isBlank() ? defaultValue : value;
    }
}
