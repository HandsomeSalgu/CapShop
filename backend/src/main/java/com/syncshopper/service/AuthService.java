package com.syncshopper.service;

import com.syncshopper.common.exception.CustomException;
import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.domain.user.AuthProvider;
import com.syncshopper.domain.user.User;
import com.syncshopper.domain.user.UserPreference;
import com.syncshopper.domain.user.UserStatus;
import com.syncshopper.dto.request.LoginRequest;
import com.syncshopper.dto.request.SignupRequest;
import com.syncshopper.dto.response.LoginResponse;
import com.syncshopper.dto.response.UserResponse;

import com.syncshopper.mapper.UserPreferenceMapper;
import com.syncshopper.security.JwtBlacklistService;
import com.syncshopper.security.JwtTokenProvider;
import io.jsonwebtoken.Claims;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class AuthService {

    private final UserService userService;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider jwtTokenProvider;
    private final JwtBlacklistService jwtBlacklistService;
    private final EmailVerificationService emailVerificationService;
    private final UserPreferenceMapper userPreferenceMapper;

    public AuthService(UserService userService, PasswordEncoder passwordEncoder, JwtTokenProvider jwtTokenProvider, JwtBlacklistService jwtBlacklistService, EmailVerificationService emailVerificationService, UserPreferenceMapper userPreferenceMapper) {
        this.userService = userService;
        this.passwordEncoder = passwordEncoder;
        this.jwtTokenProvider = jwtTokenProvider;
        this.jwtBlacklistService = jwtBlacklistService;
        this.emailVerificationService = emailVerificationService;
        this.userPreferenceMapper = userPreferenceMapper;
    }

    @Transactional
    public UserResponse signup(SignupRequest request, org.springframework.web.multipart.MultipartFile profileImage) {
        User user;
        
        String profileImageUrl = null;
        if (profileImage != null && !profileImage.isEmpty()) {
            try {
                String uploadDir = "uploads/profiles/";
                java.io.File dir = new java.io.File(uploadDir);
                if (!dir.exists()) {
                    dir.mkdirs();
                }
                String originalFilename = profileImage.getOriginalFilename();
                String extension = originalFilename != null && originalFilename.contains(".") 
                                   ? originalFilename.substring(originalFilename.lastIndexOf(".")) 
                                   : ".jpg";
                String savedFilename = java.util.UUID.randomUUID().toString() + extension;
                java.nio.file.Path filePath = java.nio.file.Paths.get(uploadDir + savedFilename);
                java.nio.file.Files.copy(profileImage.getInputStream(), filePath);
                profileImageUrl = "/uploads/profiles/" + savedFilename;
            } catch (java.io.IOException e) {
                throw new CustomException(ErrorCode.INTERNAL_SERVER_ERROR);
            }
        } else {
            int randomNum = new java.util.Random().nextInt(5) + 1;
            profileImageUrl = "/src/assets/images/basic_image/Basic_image" + randomNum + ".jpeg";
        }

        if (request.getSignupToken() != null && !request.getSignupToken().isEmpty()) {
            Claims claims = jwtTokenProvider.parseSignupToken(request.getSignupToken());
            String email = claims.get("email", String.class);
            String providerStr = claims.get("provider", String.class);
            String providerId = claims.get("providerId", String.class);
            String tokenProfileImageUrl = claims.get("profileImageUrl", String.class);

            if (userService.existsByEmail(email)) {
                throw new CustomException(ErrorCode.DUPLICATE_EMAIL);
            }

            // 만약 소셜 제공 이미지가 있고, 유저가 새로 올리지 않았다면 소셜 이미지 사용
            if (profileImage == null || profileImage.isEmpty()) {
                if (tokenProfileImageUrl != null && !tokenProfileImageUrl.isEmpty()) {
                    profileImageUrl = tokenProfileImageUrl;
                }
            }

            // 소셜 로그인은 비밀번호를 받지 않으므로 랜덤 더미 비밀번호를 생성하여 저장합니다.
            String dummyPassword = java.util.UUID.randomUUID().toString();
            String encodedPassword = passwordEncoder.encode(dummyPassword);
            user = userService.createSocialUserWithDetails(
                    email,
                    encodedPassword,
                    AuthProvider.valueOf(providerStr),
                    providerId,
                    request.getNickname(),
                    profileImageUrl,
                    request.getPhone(),
                    request.getBirthDate());
        } else {
            if (userService.existsByEmail(request.getEmail())) {
                throw new CustomException(ErrorCode.DUPLICATE_EMAIL);
            }

            String encodedPassword = passwordEncoder.encode(request.getPassword());
            user = userService.createLocalUser(
                    request.getEmail(),
                    encodedPassword,
                    request.getNickname(),
                    profileImageUrl,
                    request.getPhone(),
                    request.getBirthDate());
        }

        // Save User Preferences
        List<com.syncshopper.dto.request.CategoryPreferenceRequest> preferredCategories = request.getPreferredCategories();
        if (preferredCategories != null && !preferredCategories.isEmpty()) {
            for (com.syncshopper.dto.request.CategoryPreferenceRequest pref : preferredCategories) {
                UserPreference userPreference = UserPreference.builder()
                        .userId(user.getUserId())
                        .category1Name(pref.getCategory1Name())
                        .category2Name(pref.getCategory2Name())
                        .build();
                userPreferenceMapper.insertUserPreference(userPreference);
            }
        }

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

    public void logout(String accessToken) {
        jwtTokenProvider.validateToken(accessToken);
        jwtBlacklistService.blacklist(accessToken, jwtTokenProvider.getExpiration(accessToken));
        SecurityContextHolder.clearContext();
    }

    public boolean checkEmailAvailability(String email) {
        return !userService.existsByEmail(email);
    }

    public String findEmail(com.syncshopper.dto.request.FindEmailRequest request) {
        User user = userService.findByNicknameAndPhone(request.getNickname(), request.getPhone());
        if (user == null) {
            throw new CustomException(ErrorCode.USER_NOT_FOUND);
        }
        return user.getEmail();
    }

    @Transactional
    public void findPassword(com.syncshopper.dto.request.FindPasswordRequest request) {
        User user = userService.findByEmailAndNicknameAndPhone(request.getEmail(), request.getNickname(), request.getPhone());
        if (user == null) {
            throw new CustomException(ErrorCode.USER_NOT_FOUND);
        }

        // 임시 비밀번호 생성 (8자리 영문자+숫자 랜덤)
        String tempPassword = java.util.UUID.randomUUID().toString().replace("-", "").substring(0, 8) + "!";
        
        // 비밀번호 업데이트
        userService.updatePassword(user.getUserId(), passwordEncoder.encode(tempPassword));

        // 이메일 전송
        emailVerificationService.sendTemporaryPassword(user.getEmail(), tempPassword);
    }
}
