package com.syncshopper.security;

import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.web.authentication.AuthenticationFailureHandler;
import org.springframework.stereotype.Component;
import org.springframework.web.util.UriComponentsBuilder;

import java.io.IOException;

@Component
public class OAuth2FailureHandler implements AuthenticationFailureHandler {

    private final String authorizedRedirectUri;

    public OAuth2FailureHandler(@Value("${app.oauth2.authorized-redirect-uri}") String authorizedRedirectUri) {
        this.authorizedRedirectUri = authorizedRedirectUri;
    }

    @Override
    public void onAuthenticationFailure(HttpServletRequest request, HttpServletResponse response, AuthenticationException exception)
            throws IOException, ServletException {
        String redirectUri = UriComponentsBuilder.fromUriString(authorizedRedirectUri)
                .queryParam("error", "oauth_failed")
                .build()
                .toUriString();
        response.sendRedirect(redirectUri);
    }
}
