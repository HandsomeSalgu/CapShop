package com.syncshopper.dto.request;

import com.fasterxml.jackson.annotation.JsonAlias;
import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "Login request")
public class LoginRequest {

    @Schema(description = "Email", example = "user@example.com", requiredMode = Schema.RequiredMode.REQUIRED)
    @JsonAlias({"userEmail", "memberEmail", "loginId"})
    @Email(message = "이메일 형식이 올바르지 않습니다.")
    @NotBlank(message = "이메일은 필수입니다.")
    private String email;

    @Schema(description = "Password", example = "password1234", requiredMode = Schema.RequiredMode.REQUIRED)
    @JsonAlias({"userPassword", "memberPassword", "pwd"})
    @NotBlank(message = "비밀번호는 필수입니다.")
    private String password;
}
