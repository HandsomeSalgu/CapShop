package com.syncshopper.security;

import java.util.Map;

public class GoogleOAuth2UserInfo implements OAuth2UserInfo {

    private final Map<String, Object> attributes;

    public GoogleOAuth2UserInfo(Map<String, Object> attributes) {
        this.attributes = attributes;
    }

    @Override
    public String getProviderId() {
        return value("sub");
    }

    @Override
    public String getEmail() {
        return value("email");
    }

    @Override
    public String getNickname() {
        return value("name");
    }

    @Override
    public String getProfileImageUrl() {
        return value("picture");
    }

    private String value(String key) {
        Object value = attributes.get(key);
        return value == null ? null : String.valueOf(value);
    }
}
