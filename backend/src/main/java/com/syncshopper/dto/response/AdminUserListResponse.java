package com.syncshopper.dto.response;

import com.syncshopper.domain.user.User;
import lombok.Builder;
import lombok.Getter;

import java.time.LocalDateTime;

@Getter
@Builder
public class AdminUserListResponse {
    private Long id;
    private String email;
    private String nickname;
    private String phone;
    private String status;
    private String role;
    private LocalDateTime createdAt;

    public static AdminUserListResponse from(User user) {
        return AdminUserListResponse.builder()
                .id(user.getUserId())
                .email(user.getEmail())
                .nickname(user.getNickname())
                .phone(user.getPhone())
                .status(user.getStatus().name())
                .role(user.getRole().name())
                .createdAt(user.getCreatedAt())
                .build();
    }
}
