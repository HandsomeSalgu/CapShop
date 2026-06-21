package com.syncshopper.service;

import com.syncshopper.common.exception.CustomException;
import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.domain.user.AuthProvider;
import com.syncshopper.domain.user.User;
import com.syncshopper.domain.user.UserStatus;
import com.syncshopper.dto.request.LoginRequest;
import com.syncshopper.dto.request.SignupRequest;
import com.syncshopper.dto.response.LoginResponse;
import com.syncshopper.dto.response.UserResponse;
import com.syncshopper.security.JwtTokenProvider;
import io.jsonwebtoken.Claims;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AuthService {

    private final UserService userService;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider jwtTokenProvider;

    public AuthService(UserService userService, PasswordEncoder passwordEncoder, JwtTokenProvider jwtTokenProvider) {
        this.userService = userService;
        this.passwordEncoder = passwordEncoder;
        this.jwtTokenProvider = jwtTokenProvider;
    }

    @Transactional
    public UserResponse signup(SignupRequest request) {
        if (request.getSignupToken() != null && !request.getSignupToken().isEmpty()) {
            Claims claims = jwtTokenProvider.parseSignupToken(request.getSignupToken());
            String email = claims.get("email", String.class);
            String providerStr = claims.get("provider", String.class);
            String providerId = claims.get("providerId", String.class);
            String profileImageUrl = claims.get("profileImageUrl", String.class);

            if (userService.existsByEmail(email)) {
                throw new CustomException(ErrorCode.DUPLICATE_EMAIL);
            }

            String encodedPassword = passwordEncoder.encode(request.getPassword());
            User user = userService.createSocialUserWithDetails(
                    email,
                    encodedPassword,
                    AuthProvider.valueOf(providerStr),
                    providerId,
                    request.getNickname(),
                    profileImageUrl,
                    request.getPhone(),
                    request.getBirthDate());
            return UserResponse.from(user);
        }

        if (userService.existsByEmail(request.getEmail())) {
            throw new CustomException(ErrorCode.DUPLICATE_EMAIL);
        }

        String encodedPassword = passwordEncoder.encode(request.getPassword());
        User user = userService.createLocalUser(
                request.getEmail(),
                encodedPassword,
                request.getNickname(),
                request.getPhone(),
                request.getBirthDate());
        return UserResponse.from(user);
    }

    @Transactional
    public LoginResponse login(LoginRequest request) {
        User user = userService.findByEmail(request.getEmail());
        if (user == null || user.getProvider() != AuthProvider.LOCAL) {
            throw new CustomException(ErrorCode.INVALID_LOGIN);
        }
        if (!passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            throw new CustomException(ErrorCode.INVALID_LOGIN);
        }
        if (user.getStatus() != UserStatus.ACTIVE) {
            throw new CustomException(ErrorCode.INACTIVE_USER);
        }

        userService.updateLastLoginAt(user.getUserId());
        String accessToken = jwtTokenProvider.createAccessToken(user);

        return LoginResponse.builder()
                .accessToken(accessToken)
                .expiresIn(jwtTokenProvider.getAccessTokenExpiration())
                .user(UserResponse.from(user))
                .build();
    }

    public UserResponse me() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication == null || !authentication.isAuthenticated()) {
            throw new CustomException(ErrorCode.UNAUTHORIZED);
        }

        Long userId = Long.valueOf(authentication.getName());
        return UserResponse.from(userService.findById(userId));
    }

    public boolean checkEmailAvailability(String email) {
        return !userService.existsByEmail(email);
    }
}
