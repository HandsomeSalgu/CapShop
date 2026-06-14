package com.syncshopper.service;

import com.syncshopper.dto.request.DetectionAnalyzeRequest;
import com.syncshopper.dto.response.AiAnalysisResult;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

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
                    .confidence(0.93)
                    .rawResponseJson("{\"target_name\":\"Apple AirPods Pro\",\"category_name\":\"Electronics\",\"brand\":\"Apple\",\"model_name\":\"AirPods Pro\",\"confidence\":0.93}")
                    .build();
        }

        if (keywordSource.contains("nike")) {
            return AiAnalysisResult.builder()
                    .targetName("Nike sneakers")
                    .categoryName("Fashion")
                    .brand("Nike")
                    .modelName("Air Force 1")
                    .confidence(0.91)
                    .rawResponseJson("{\"target_name\":\"Nike sneakers\",\"category_name\":\"Fashion\",\"brand\":\"Nike\",\"model_name\":\"Air Force 1\",\"confidence\":0.91}")
                    .build();
        }

        return AiAnalysisResult.builder()
                .targetName("Nike sneakers")
                .categoryName("Fashion")
                .brand("Nike")
                .modelName("Air Force 1")
                .confidence(0.91)
                .rawResponseJson("{\"target_name\":\"Nike sneakers\",\"category_name\":\"Fashion\",\"brand\":\"Nike\",\"model_name\":\"Air Force 1\",\"confidence\":0.91}")
                .build();
    }
}
