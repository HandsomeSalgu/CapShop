package com.syncshopper.service;

import com.syncshopper.common.exception.CustomException;
import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.domain.user.AuthProvider;
import com.syncshopper.domain.user.User;
import com.syncshopper.domain.user.UserRole;
import com.syncshopper.domain.user.UserStatus;
import com.syncshopper.dto.request.UserProfileUpdateRequest;
import com.syncshopper.mapper.UserMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.time.LocalDate;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class UserProfileServiceTest {

    private UserMapper userMapper;
    private PasswordEncoder passwordEncoder;
    private UserProfileService userProfileService;

    @BeforeEach
    void setUp() {
        userMapper = mock(UserMapper.class);
        passwordEncoder = mock(PasswordEncoder.class);
        userProfileService = new UserProfileService(userMapper, passwordEncoder);
    }

    @Test
    void updateMyProfileRejectsPartialPasswordChangeRequest() {
        User user = localUser();
        when(userMapper.findById(1L)).thenReturn(user);

        UserProfileUpdateRequest request = UserProfileUpdateRequest.builder()
                .nickname("new-name")
                .newPassword("newPassword1234")
                .confirmNewPassword("newPassword1234")
                .build();

        assertThatThrownBy(() -> userProfileService.updateMyProfile(1L, request))
                .isInstanceOf(CustomException.class)
                .extracting("errorCode")
                .isEqualTo(ErrorCode.INVALID_INPUT_VALUE);

        verify(passwordEncoder, never()).matches(any(), any());
        verify(userMapper, never()).updateProfile(any());
    }

    @Test
    void updateMyProfilePassesOnlyRequestedProfileFieldsToMapper() {
        User user = localUser();
        when(userMapper.findById(1L)).thenReturn(user);
        when(userMapper.updateProfile(any())).thenReturn(1);

        UserProfileUpdateRequest request = UserProfileUpdateRequest.builder()
                .nickname("new-name")
                .build();

        userProfileService.updateMyProfile(1L, request);

        ArgumentCaptor<User> captor = ArgumentCaptor.forClass(User.class);
        verify(userMapper).updateProfile(captor.capture());

        User updateUser = captor.getValue();
        assertThat(updateUser.getUserId()).isEqualTo(1L);
        assertThat(updateUser.getNickname()).isEqualTo("new-name");
        assertThat(updateUser.getPhone()).isNull();
        assertThat(updateUser.getBirthDate()).isNull();
        assertThat(updateUser.getProfileImageUrl()).isNull();
        assertThat(updateUser.getPassword()).isNull();
    }

    @Test
    void updateMyProfileTreatsBlankOptionalFieldsAsNotRequested() {
        User user = localUser();
        when(userMapper.findById(1L)).thenReturn(user);
        when(userMapper.updateProfile(any())).thenReturn(1);

        UserProfileUpdateRequest request = UserProfileUpdateRequest.builder()
                .nickname("new-name")
                .phone("")
                .profileImageUrl("   ")
                .build();

        userProfileService.updateMyProfile(1L, request);

        ArgumentCaptor<User> captor = ArgumentCaptor.forClass(User.class);
        verify(userMapper).updateProfile(captor.capture());

        User updateUser = captor.getValue();
        assertThat(updateUser.getPhone()).isNull();
        assertThat(updateUser.getProfileImageUrl()).isNull();
    }

    @Test
    void updateMyProfileChangesPasswordWithCurrentPasswordVerification() {
        User user = localUser();
        when(userMapper.findById(1L)).thenReturn(user);
        when(passwordEncoder.matches("password1234", "encoded-password")).thenReturn(true);
        when(passwordEncoder.encode("newPassword1234")).thenReturn("new-encoded-password");
        when(userMapper.updateProfile(any())).thenReturn(1);

        UserProfileUpdateRequest request = UserProfileUpdateRequest.builder()
                .nickname("new-name")
                .currentPassword("password1234")
                .newPassword("newPassword1234")
                .confirmNewPassword("newPassword1234")
                .build();

        userProfileService.updateMyProfile(1L, request);

        ArgumentCaptor<User> captor = ArgumentCaptor.forClass(User.class);
        verify(userMapper).updateProfile(captor.capture());

        assertThat(captor.getValue().getPassword()).isEqualTo("new-encoded-password");
    }

    private User localUser() {
        return User.builder()
                .userId(1L)
                .email("user@example.com")
                .password("encoded-password")
                .provider(AuthProvider.LOCAL)
                .nickname("old-name")
                .phone("010-1234-5678")
                .birthDate(LocalDate.of(2000, 1, 1))
                .role(UserRole.USER)
                .status(UserStatus.ACTIVE)
                .build();
    }
}
