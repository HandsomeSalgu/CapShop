package com.syncshopper.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;

@Getter
@Setter
@ConfigurationProperties(prefix = "app.ai")
public class AiProperties {

    private boolean mockEnabled = true;
    private String fastapiBaseUrl = "http://localhost:8000";
    private String analyzePath = "/api/ai/analyze-frame";
    private String commerceQueryPath = "/api/ai/generate-commerce-query";
    private int timeoutMs = 5000;
}
