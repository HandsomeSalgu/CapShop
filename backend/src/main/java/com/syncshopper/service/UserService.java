package com.syncshopper.service;

import com.syncshopper.common.exception.CustomException;
import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.domain.user.AuthProvider;
import com.syncshopper.domain.user.User;
import com.syncshopper.domain.user.UserRole;
import com.syncshopper.domain.user.UserStatus;
import com.syncshopper.mapper.UserMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.time.LocalDate;

@Service
public class UserService {

    private final UserMapper userMapper;

    public UserService(UserMapper userMapper) {
        this.userMapper = userMapper;
    }

    @Transactional
    public User createLocalUser(String email, String encodedPassword, String nickname, String phone,
            LocalDate birthDate) {
        User user = User.builder()
                .email(email)
                .password(encodedPassword)
                .provider(AuthProvider.LOCAL)
                .nickname(nickname)
                .phone(phone)
                .birthDate(birthDate)
                .role(UserRole.USER)
                .status(UserStatus.ACTIVE)
                .build();
        userMapper.insertUser(user);
        return user;
    }



    @Transactional
    public User createSocialUserWithDetails(String email, String encodedPassword, AuthProvider provider, String providerId, 
            String nickname, String profileImageUrl, String phone, LocalDate birthDate) {
        User user = User.builder()
                .email(email)
                .password(encodedPassword)
                .provider(provider)
                .providerId(providerId)
                .nickname(nickname)
                .profileImageUrl(profileImageUrl)
                .phone(phone)
                .birthDate(birthDate)
                .role(UserRole.USER)
                .status(UserStatus.ACTIVE)
                .build();
        userMapper.insertUser(user);
        return user;
    }

    public User findById(Long userId) {
        User user = userMapper.findById(userId);
        if (user == null) {
            throw new CustomException(ErrorCode.USER_NOT_FOUND);
        }
        return user;
    }

    public User findByEmail(String email) {
        return userMapper.findByEmail(email);
    }

    public User findByProviderAndProviderId(AuthProvider provider, String providerId) {
        return userMapper.findByProviderAndProviderId(provider.name(), providerId);
    }

    public boolean existsByEmail(String email) {
        return userMapper.existsByEmail(email) > 0;
    }

    @Transactional
    public void updateLastLoginAt(Long userId) {
        userMapper.updateLastLoginAt(userId);
    }

    @Transactional
    public User updateOAuthUser(User user, String nickname, String profileImageUrl) {
        user.setNickname(nickname);
        user.setProfileImageUrl(profileImageUrl);
        userMapper.updateOAuthUser(user);
        return findById(user.getUserId());
    }

    public User findByNicknameAndPhone(String nickname, String phone) {
        return userMapper.findByNicknameAndPhone(nickname, phone);
    }

    public User findByEmailAndNicknameAndPhone(String email, String nickname, String phone) {
        return userMapper.findByEmailAndNicknameAndPhone(email, nickname, phone);
    }

    @Transactional
    public void updatePassword(Long userId, String encodedPassword) {
        userMapper.updatePassword(userId, encodedPassword);
    }
}
