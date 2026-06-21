package com.syncshopper.service;

import com.syncshopper.common.exception.CustomException;
import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.domain.user.User;
import com.syncshopper.dto.request.AdminUserSearchCondition;
import com.syncshopper.dto.response.AdminUserListResponse;
import com.syncshopper.dto.response.PageResponse;
import com.syncshopper.mapper.UserMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class AdminUserService {

    private final UserMapper userMapper;

    @Transactional(readOnly = true)
    public PageResponse<AdminUserListResponse> getUsers(AdminUserSearchCondition condition) {
        int page = condition.getPage();
        int size = condition.getSize();
        int offset = (page - 1) * size;
        String keyword = condition.getKeyword();

        List<User> users = userMapper.findAllUsers(offset, size, keyword);
        long totalCount = userMapper.countAllUsers(keyword);

        List<AdminUserListResponse> content = users.stream()
                .map(AdminUserListResponse::from)
                .collect(Collectors.toList());

        return PageResponse.of(content, page, size, totalCount);
    }

    @Transactional
    public void updateUserStatus(Long userId, String status) {
        checkNotSelfModification(userId);
        User user = userMapper.findById(userId);
        if (user == null) {
            throw new CustomException(ErrorCode.USER_NOT_FOUND);
        }
        userMapper.updateUserStatus(userId, status);
    }

    @Transactional
    public void updateUserRole(Long userId, String role) {
        checkNotSelfModification(userId);
        User user = userMapper.findById(userId);
        if (user == null) {
            throw new CustomException(ErrorCode.USER_NOT_FOUND);
        }
        userMapper.updateUserRole(userId, role);
    }

    private void checkNotSelfModification(Long targetUserId) {
        String currentUserIdStr = SecurityContextHolder.getContext().getAuthentication().getName();
        if (currentUserIdStr != null && currentUserIdStr.equals(String.valueOf(targetUserId))) {
            throw new CustomException(ErrorCode.INVALID_INPUT_VALUE, "본인의 계정 상태 및 권한은 변경할 수 없습니다.");
        }
    }
}
