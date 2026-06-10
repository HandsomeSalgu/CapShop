package com.syncshopper.security;

public interface OAuth2UserInfo {

    String getProviderId();

    String getEmail();

    String getNickname();

    String getProfileImageUrl();
}
