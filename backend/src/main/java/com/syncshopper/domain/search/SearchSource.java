package com.syncshopper.domain.search;

public enum SearchSource {
    NAVER_SHOPPING("네이버 쇼핑"),
    NAVER_IMAGE("네이버 이미지"),
    NAVER_BLOG("네이버 블로그"),
    NAVER_CAFE("네이버 카페"),
    NAVER_WEB("네이버 웹문서");

    private final String label;

    SearchSource(String label) {
        this.label = label;
    }

    public String getLabel() {
        return label;
    }
}
