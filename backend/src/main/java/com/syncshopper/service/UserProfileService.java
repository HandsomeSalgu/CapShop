package com.syncshopper.service;

import com.syncshopper.common.exception.CustomException;
import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.domain.user.AuthProvider;
import com.syncshopper.domain.user.User;
import com.syncshopper.dto.request.PasswordChangeRequest;
import com.syncshopper.dto.request.UserProfileUpdateRequest;
import com.syncshopper.dto.response.UserProfileResponse;
import com.syncshopper.mapper.UserMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

@RequiredArgsConstructor
@Service
public class UserProfileService {

    private final UserMapper userMapper;
    private final PasswordEncoder passwordEncoder;

    public UserProfileResponse getMyProfile(Long userId) {
        return UserProfileResponse.from(findUser(userId));
    }

    @Transactional
    public UserProfileResponse updateMyProfile(Long userId, UserProfileUpdateRequest request, org.springframework.web.multipart.MultipartFile profileImage) {
        User user = findUser(userId);
        
        String profileImageUrl = null;
        if (profileImage != null && !profileImage.isEmpty()) {
            try {
                String originalFilename = profileImage.getOriginalFilename();
                String extension = originalFilename != null && originalFilename.contains(".") 
                        ? originalFilename.substring(originalFilename.lastIndexOf(".")) 
                        : ".jpg";
                String savedFilename = java.util.UUID.randomUUID() + extension;

                java.nio.file.Path uploadPath = java.nio.file.Paths.get("uploads/profiles");
                if (!java.nio.file.Files.exists(uploadPath)) {
                    java.nio.file.Files.createDirectories(uploadPath);
                }
                java.nio.file.Path filePath = uploadPath.resolve(savedFilename);
                java.nio.file.Files.copy(profileImage.getInputStream(), filePath, java.nio.file.StandardCopyOption.REPLACE_EXISTING);
                profileImageUrl = "/uploads/profiles/" + savedFilename;
            } catch (java.io.IOException e) {
                throw new RuntimeException("Failed to store profile image", e);
            }
        }

        User updateUser = User.builder()
                .userId(userId)
                .nickname(request.getNickname())
                .phone(blankToNull(request.getPhone()))
                .birthDate(request.getBirthDate())
                .profileImageUrl(profileImageUrl)
                .build();

        if (StringUtils.hasText(request.getNewPassword())) {
            if (user.getProvider() != AuthProvider.LOCAL || user.getPassword() == null) {
                throw new CustomException(ErrorCode.OAUTH_USER_PASSWORD_CHANGE_NOT_ALLOWED);
            }
            if (!request.getNewPassword().equals(request.getConfirmNewPassword())) {
                throw new CustomException(ErrorCode.PASSWORD_CONFIRM_NOT_MATCHED);
            }
            updateUser.setPassword(passwordEncoder.encode(request.getNewPassword()));
        }

        userMapper.updateProfile(updateUser);

        return UserProfileResponse.from(findUser(userId));
    }

    @Transactional
    public void changePassword(Long userId, PasswordChangeRequest request) {
        User user = findUser(userId);
        if (user.getProvider() != AuthProvider.LOCAL || user.getPassword() == null) {
            throw new CustomException(ErrorCode.OAUTH_USER_PASSWORD_CHANGE_NOT_ALLOWED);
        }
        if (!passwordEncoder.matches(request.getCurrentPassword(), user.getPassword())) {
            throw new CustomException(ErrorCode.CURRENT_PASSWORD_NOT_MATCHED);
        }
        if (!request.getNewPassword().equals(request.getConfirmNewPassword())) {
            throw new CustomException(ErrorCode.PASSWORD_CONFIRM_NOT_MATCHED);
        }

        userMapper.updatePassword(userId, passwordEncoder.encode(request.getNewPassword()));
    }

    public boolean verifyPassword(Long userId, String password) {
        User user = findUser(userId);
        if (user.getProvider() != AuthProvider.LOCAL || user.getPassword() == null) {
            throw new CustomException(ErrorCode.OAUTH_USER_PASSWORD_CHANGE_NOT_ALLOWED);
        }
        return passwordEncoder.matches(password, user.getPassword());
    }
    private User findUser(Long userId) {
        User user = userMapper.findById(userId);
        if (user == null) {
            throw new CustomException(ErrorCode.USER_NOT_FOUND);
        }
        return user;
    }



    private String blankToNull(String value) {
        return StringUtils.hasText(value) ? value : null;
    }
}
