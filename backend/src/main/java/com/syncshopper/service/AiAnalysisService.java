package com.syncshopper.service;

import com.syncshopper.config.AiProperties;
import com.syncshopper.domain.detection.AiProvider;
import com.syncshopper.dto.request.AiCommerceQueryRequest;
import com.syncshopper.dto.request.DetectionAnalyzeRequest;
import com.syncshopper.dto.response.AiAnalysisResult;
import com.syncshopper.dto.response.AiCommerceQueryResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@RequiredArgsConstructor
@Service
public class AiAnalysisService {

    private final AiProperties aiProperties;
    private final MockAiAnalysisService mockAiAnalysisService;
    private final FastApiAnalysisClient fastApiAnalysisClient;

    public AiAnalysisResult analyze(DetectionAnalyzeRequest request) {
        if (aiProperties.isMockEnabled()) {
            return mockAiAnalysisService.analyze(request);
        }
        return fastApiAnalysisClient.analyze(request);
    }

    public AiCommerceQueryResponse generateCommerceQuery(AiCommerceQueryRequest request) {
        if (aiProperties.isMockEnabled()) {
            return mockAiAnalysisService.generateCommerceQuery(request);
        }
        return fastApiAnalysisClient.generateCommerceQuery(request);
    }

    public AiProvider getCurrentProvider() {
        return aiProperties.isMockEnabled() ? AiProvider.MOCK : AiProvider.FASTAPI;
    }
}
