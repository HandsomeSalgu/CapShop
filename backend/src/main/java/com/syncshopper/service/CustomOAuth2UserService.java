package com.syncshopper.service;

import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.domain.user.AuthProvider;
import com.syncshopper.domain.user.User;
import com.syncshopper.domain.user.UserStatus;
import com.syncshopper.security.GoogleOAuth2UserInfo;
import com.syncshopper.security.KakaoOAuth2UserInfo;
import com.syncshopper.security.OAuth2UserInfo;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.oauth2.client.userinfo.DefaultOAuth2UserService;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserRequest;
import org.springframework.security.oauth2.core.OAuth2AuthenticationException;
import org.springframework.security.oauth2.core.OAuth2Error;
import org.springframework.security.oauth2.core.user.DefaultOAuth2User;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class CustomOAuth2UserService extends DefaultOAuth2UserService {

    private final UserService userService;

    public CustomOAuth2UserService(UserService userService) {
        this.userService = userService;
    }

    @Override
    public OAuth2User loadUser(OAuth2UserRequest userRequest) throws OAuth2AuthenticationException {
        OAuth2User oauth2User = super.loadUser(userRequest);
        String registrationId = userRequest.getClientRegistration().getRegistrationId();
        AuthProvider provider = AuthProvider.valueOf(registrationId.toUpperCase());
        OAuth2UserInfo userInfo = createUserInfo(provider, oauth2User.getAttributes());

        if (!StringUtils.hasText(userInfo.getProviderId()) || !StringUtils.hasText(userInfo.getEmail())) {
            throw oauthException(ErrorCode.INVALID_LOGIN);
        }

        Map<String, Object> attributes = new HashMap<>(oauth2User.getAttributes());

        User user = userService.findByProviderAndProviderId(provider, userInfo.getProviderId());
        if (user != null) {
            user = userService.updateOAuthUser(user, userInfo.getNickname(), userInfo.getProfileImageUrl());
            
            if (user.getStatus() != UserStatus.ACTIVE) {
                throw oauthException(ErrorCode.INACTIVE_USER);
            }
            
            attributes.put("isNew", false);
            attributes.put("userId", user.getUserId());
            attributes.put("email", user.getEmail());
            attributes.put("role", user.getRole().name());
            attributes.put("provider", user.getProvider().name());

            return new DefaultOAuth2User(
                    List.of(new SimpleGrantedAuthority("ROLE_" + user.getRole().name())),
                    attributes,
                    "userId"
            );
        } else {
            User emailUser = userService.findByEmail(userInfo.getEmail());
            if (emailUser != null) {
                throw oauthException(ErrorCode.OAUTH_EMAIL_CONFLICT);
            }
            
            attributes.put("isNew", true);
            attributes.put("email", userInfo.getEmail());
            attributes.put("nickname", userInfo.getNickname());
            attributes.put("provider", provider.name());
            attributes.put("providerId", userInfo.getProviderId());
            attributes.put("profileImageUrl", userInfo.getProfileImageUrl());

            return new DefaultOAuth2User(
                    List.of(new SimpleGrantedAuthority("ROLE_GUEST")),
                    attributes,
                    "email"
            );
        }
    }

    private OAuth2UserInfo createUserInfo(AuthProvider provider, Map<String, Object> attributes) {
        return switch (provider) {
            case GOOGLE -> new GoogleOAuth2UserInfo(attributes);
            case KAKAO -> new KakaoOAuth2UserInfo(attributes);
            case LOCAL -> throw oauthException(ErrorCode.INVALID_LOGIN);
        };
    }

    private OAuth2AuthenticationException oauthException(ErrorCode errorCode) {
        return new OAuth2AuthenticationException(new OAuth2Error(errorCode.name()), errorCode.getMessage());
    }
}
