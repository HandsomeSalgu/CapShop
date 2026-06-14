package com.syncshopper.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;

@Getter
@Setter
@ConfigurationProperties(prefix = "app.naver.shopping")
public class NaverShoppingProperties {

    private String clientId;
    private String clientSecret;
    private String baseUrl = "https://openapi.naver.com";
    private String searchPath = "/v1/search/shop.json";
    private Integer display = 10;
    private Integer start = 1;
    private String sort = "sim";
    private String exclude = "used:rental:cbshop";
}
