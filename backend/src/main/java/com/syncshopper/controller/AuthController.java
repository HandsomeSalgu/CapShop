package com.syncshopper.controller;

import com.syncshopper.common.response.ApiResponse;
import com.syncshopper.dto.request.EmailCodeRequest;
import com.syncshopper.dto.request.EmailVerifyRequest;
import com.syncshopper.dto.request.LoginRequest;
import com.syncshopper.dto.request.SignupRequest;
import com.syncshopper.dto.response.LoginResponse;
import com.syncshopper.dto.response.UserResponse;
import com.syncshopper.service.AuthService;
import com.syncshopper.service.EmailVerificationService;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.ExampleObject;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@Tag(name = "Auth", description = "Signup, login, and authentication APIs")
@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final AuthService authService;
    private final EmailVerificationService emailVerificationService;

    public AuthController(AuthService authService, EmailVerificationService emailVerificationService) {
        this.authService = authService;
        this.emailVerificationService = emailVerificationService;
    }

    @Operation(summary = "Signup", requestBody = @io.swagger.v3.oas.annotations.parameters.RequestBody(required = true, content = @Content(mediaType = "application/json", schema = @Schema(implementation = SignupRequest.class), examples = @ExampleObject(value = """
            {
              "email": "user@example.com",
              "password": "password1234",
              "nickname": "hwarang",
              "phone": "01012345678",
              "birthDate": "2000-01-01"
            }
            """))))
    @PostMapping("/signup")
    public ApiResponse<UserResponse> signup(@Valid @RequestBody SignupRequest request) {
        return ApiResponse.success("Signup completed.", authService.signup(request));
    }

    @Operation(summary = "Login", requestBody = @io.swagger.v3.oas.annotations.parameters.RequestBody(required = true, content = @Content(mediaType = "application/json", schema = @Schema(implementation = LoginRequest.class), examples = @ExampleObject(value = """
            {
              "email": "user@example.com",
              "password": "password1234"
            }
            """))))
    @PostMapping("/login")
    public ApiResponse<LoginResponse> login(@Valid @RequestBody LoginRequest request) {
        return ApiResponse.success("Login succeeded.", authService.login(request));
    }

    @Operation(summary = "Get current user")
    @GetMapping("/me")
    public ApiResponse<UserResponse> me() {
        return ApiResponse.success(authService.me());
    }

    @Operation(summary = "Logout")
    @PostMapping("/logout")
    public ApiResponse<Void> logout() {
        return ApiResponse.success("Logged out.");
    }

    @Operation(summary = "Check email availability")
    @GetMapping("/check-email")
    public ApiResponse<Boolean> checkEmail(@RequestParam String email) {
        return ApiResponse.success("Email availability checked.", authService.checkEmailAvailability(email));
    }

    @Operation(summary = "Send email verification code")
    @PostMapping("/email/send-code")
    public ApiResponse<Void> sendEmailCode(@RequestBody EmailCodeRequest request) {
        if (!authService.checkEmailAvailability(request.getEmail())) {
            return ApiResponse.fail("이메일이 이미 존재합니다.");
        }
        emailVerificationService.sendVerificationCode(request.getEmail());
        return ApiResponse.success("인증번호가 발송되었습니다.");
    }

    @Operation(summary = "Verify email code")
    @PostMapping("/email/verify-code")
    public ApiResponse<Boolean> verifyEmailCode(@RequestBody EmailVerifyRequest request) {
        boolean isValid = emailVerificationService.verifyCode(request.getEmail(), request.getCode());
        if (!isValid) {
            return ApiResponse.fail("인증번호가 유효하지 않거나 만료되었습니다.", false);
        }
        return ApiResponse.success("이메일 인증이 완료되었습니다.", true);
    }

    @Operation(summary = "Find email by nickname and phone")
    @PostMapping("/find-email")
    public ApiResponse<String> findEmail(@Valid @RequestBody com.syncshopper.dto.request.FindEmailRequest request) {
        String email = authService.findEmail(request);
        return ApiResponse.success("이메일을 성공적으로 찾았습니다.", email);
    }

    @Operation(summary = "Find password and send temporary password")
    @PostMapping("/find-password")
    public ApiResponse<Void> findPassword(@Valid @RequestBody com.syncshopper.dto.request.FindPasswordRequest request) {
        authService.findPassword(request);
        return ApiResponse.success("임시 비밀번호가 이메일로 발송되었습니다.");
    }
}
