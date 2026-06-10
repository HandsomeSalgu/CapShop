package com.syncshopper.security;

import java.util.Map;

public class KakaoOAuth2UserInfo implements OAuth2UserInfo {

    private final Map<String, Object> attributes;

    public KakaoOAuth2UserInfo(Map<String, Object> attributes) {
        this.attributes = attributes;
    }

    @Override
    public String getProviderId() {
        Object id = attributes.get("id");
        return id == null ? null : String.valueOf(id);
    }

    @Override
    public String getEmail() {
        return kakaoAccountValue("email");
    }

    @Override
    public String getNickname() {
        Map<String, Object> profile = profile();
        Object nickname = profile.get("nickname");
        return nickname == null ? null : String.valueOf(nickname);
    }

    @Override
    public String getProfileImageUrl() {
        Map<String, Object> profile = profile();
        Object profileImageUrl = profile.get("profile_image_url");
        return profileImageUrl == null ? null : String.valueOf(profileImageUrl);
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> kakaoAccount() {
        Object account = attributes.get("kakao_account");
        if (account instanceof Map<?, ?> map) {
            return (Map<String, Object>) map;
        }
        return Map.of();
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> profile() {
        Object profile = kakaoAccount().get("profile");
        if (profile instanceof Map<?, ?> map) {
            return (Map<String, Object>) map;
        }
        return Map.of();
    }

    private String kakaoAccountValue(String key) {
        Object value = kakaoAccount().get(key);
        return value == null ? null : String.valueOf(value);
    }
}
