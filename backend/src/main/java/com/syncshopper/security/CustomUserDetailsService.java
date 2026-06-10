package com.syncshopper.security;

import com.syncshopper.common.exception.CustomException;
import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.domain.user.User;
import com.syncshopper.domain.user.UserStatus;
import com.syncshopper.service.UserService;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class CustomUserDetailsService {

    private final UserService userService;

    public CustomUserDetailsService(UserService userService) {
        this.userService = userService;
    }

    public UserDetails loadUserById(Long userId) {
        User user = userService.findById(userId);
        if (user.getStatus() != UserStatus.ACTIVE) {
            throw new CustomException(ErrorCode.INACTIVE_USER);
        }

        return new org.springframework.security.core.userdetails.User(
                String.valueOf(user.getUserId()),
                user.getPassword() == null ? "" : user.getPassword(),
                List.of(new SimpleGrantedAuthority("ROLE_" + user.getRole().name()))
        );
    }
}
