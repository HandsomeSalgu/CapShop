package com.syncshopper.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;

@Getter
@Setter
@ConfigurationProperties(prefix = "app.naver")
public class NaverSearchProperties {

    private String clientId;
    private String clientSecret;
    private Search search = new Search();

    @Getter
    @Setter
    public static class Search {

        private String shoppingUrl = "https://openapi.naver.com/v1/search/shop.json";
        private String imageUrl = "https://openapi.naver.com/v1/search/image";
        private String blogUrl = "https://openapi.naver.com/v1/search/blog.json";
        private String cafeUrl = "https://openapi.naver.com/v1/search/cafearticle.json";
        private String webUrl = "https://openapi.naver.com/v1/search/webkr.json";
        private Integer display = 5;
        private Integer start = 1;
        private String sort = "sim";
        private String exclude = "used:rental:cbshop";
        private Long cacheTtlHours = 24L;
    }
}
