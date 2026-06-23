package com.syncshopper.controller;

import com.syncshopper.dto.response.UserResponse;
import com.syncshopper.security.CustomUserDetailsService;
import com.syncshopper.security.JwtBlacklistService;
import com.syncshopper.security.JwtTokenProvider;
import com.syncshopper.service.AuthService;
import com.syncshopper.service.EmailVerificationService;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(AuthController.class)
@AutoConfigureMockMvc(addFilters = false)
class AuthControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private AuthService authService;

    @MockitoBean
    private JwtTokenProvider jwtTokenProvider;

    @MockitoBean
    private JwtBlacklistService jwtBlacklistService;

    @MockitoBean
    private CustomUserDetailsService customUserDetailsService;

    @MockitoBean
    private EmailVerificationService emailVerificationService;

    @Test
    void signupBindsJsonRequestBody() throws Exception {
        when(authService.signup(any())).thenReturn(UserResponse.builder().userId(1L).build());

        mockMvc.perform(post("/api/auth/signup")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "email": "user@example.com",
                                  "password": "password1234",
                                  "nickname": "hwarang",
                                  "phone": "01012345678",
                                  "birthDate": "2000-01-01"
                                }
                                """))
                .andExpect(status().isOk());

        ArgumentCaptor<com.syncshopper.dto.request.SignupRequest> captor =
                ArgumentCaptor.forClass(com.syncshopper.dto.request.SignupRequest.class);
        verify(authService).signup(captor.capture());

        assertThat(captor.getValue().getEmail()).isEqualTo("user@example.com");
        assertThat(captor.getValue().getPassword()).isEqualTo("password1234");
        assertThat(captor.getValue().getNickname()).isEqualTo("hwarang");
        assertThat(captor.getValue().getPhone()).isEqualTo("01012345678");
        assertThat(captor.getValue().getBirthDate().toString()).isEqualTo("2000-01-01");
    }

    @Test
    void logoutPassesBearerTokenToService() throws Exception {
        mockMvc.perform(post("/api/auth/logout")
                        .header("Authorization", "Bearer access-token"))
                .andExpect(status().isOk());

        verify(authService).logout("access-token");
    }
}
