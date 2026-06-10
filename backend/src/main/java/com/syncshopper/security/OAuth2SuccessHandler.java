package com.syncshopper.security;

import com.syncshopper.domain.user.User;
import com.syncshopper.domain.user.UserRole;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.security.web.authentication.AuthenticationSuccessHandler;
import org.springframework.stereotype.Component;
import org.springframework.web.util.UriComponentsBuilder;

import java.io.IOException;

@Component
public class OAuth2SuccessHandler implements AuthenticationSuccessHandler {

    private final JwtTokenProvider jwtTokenProvider;
    private final String authorizedRedirectUri;

    public OAuth2SuccessHandler(
            JwtTokenProvider jwtTokenProvider,
            @Value("${app.oauth2.authorized-redirect-uri}") String authorizedRedirectUri
    ) {
        this.jwtTokenProvider = jwtTokenProvider;
        this.authorizedRedirectUri = authorizedRedirectUri;
    }

    @Override
    public void onAuthenticationSuccess(HttpServletRequest request, HttpServletResponse response, Authentication authentication)
            throws IOException, ServletException {
        OAuth2User principal = (OAuth2User) authentication.getPrincipal();

        User user = User.builder()
                .userId(asLong(principal.getAttribute("userId")))
                .email(principal.getAttribute("email"))
                .role(UserRole.valueOf(principal.getAttribute("role")))
                .build();

        String accessToken = jwtTokenProvider.createAccessToken(user);
        String redirectUri = UriComponentsBuilder.fromUriString(authorizedRedirectUri)
                .queryParam("accessToken", accessToken)
                .queryParam("tokenType", "Bearer")
                .build()
                .toUriString();

        // TODO: In production, prefer HttpOnly Cookie or one-time code exchange instead of query string tokens.
        response.sendRedirect(redirectUri);
    }

    private Long asLong(Object value) {
        if (value instanceof Long longValue) {
            return longValue;
        }
        if (value instanceof Number number) {
            return number.longValue();
        }
        return Long.valueOf(String.valueOf(value));
    }
}
