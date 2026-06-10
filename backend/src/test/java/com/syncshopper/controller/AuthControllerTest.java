package com.syncshopper.controller;

import com.syncshopper.dto.response.UserResponse;
import com.syncshopper.security.CustomUserDetailsService;
import com.syncshopper.security.JwtTokenProvider;
import com.syncshopper.service.AuthService;
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
    private CustomUserDetailsService customUserDetailsService;

    @Test
    void signupBindsJsonRequestBody() throws Exception {
        when(authService.signup(any())).thenReturn(UserResponse.builder().userId(1L).build());

        mockMvc.perform(post("/api/auth/signup")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "email": "user@example.com",
                                  "password": "password1234",
                                  "nickname": "hwarang"
                                }
                                """))
                .andExpect(status().isOk());

        ArgumentCaptor<com.syncshopper.dto.request.SignupRequest> captor =
                ArgumentCaptor.forClass(com.syncshopper.dto.request.SignupRequest.class);
        verify(authService).signup(captor.capture());

        assertThat(captor.getValue().getEmail()).isEqualTo("user@example.com");
        assertThat(captor.getValue().getPassword()).isEqualTo("password1234");
        assertThat(captor.getValue().getNickname()).isEqualTo("hwarang");
    }
}
