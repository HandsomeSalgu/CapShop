package com.syncshopper.domain.detection;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AiAnalysisLog {

    private Long logId;
    private Long detectionId;
    private AiProvider apiProvider;
    private String requestPayload;
    private String responsePayload;
    private String successYn;
    private String errorMessage;
    private Integer latencyMs;
    private LocalDateTime createdAt;
}
