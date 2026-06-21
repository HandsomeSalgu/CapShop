package com.syncshopper.dto.request;

import com.fasterxml.jackson.annotation.JsonAlias;
import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDate;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "Signup request")
public class SignupRequest {

    @Schema(description = "Email", example = "user@example.com", requiredMode = Schema.RequiredMode.REQUIRED)
    @JsonAlias({"userEmail", "memberEmail", "loginId"})
    @Email(message = "이메일 형식이 올바르지 않습니다.")
    @NotBlank(message = "이메일은 필수입니다.")
    private String email;

    @Schema(description = "Password", example = "password1234", requiredMode = Schema.RequiredMode.REQUIRED)
    @JsonAlias({"userPassword", "memberPassword", "pwd"})
    @NotBlank(message = "비밀번호는 필수입니다.")
    @Size(min = 8, message = "비밀번호는 최소 8자 이상이어야 합니다.")
    private String password;

    @Schema(description = "Nickname", example = "hwarang", requiredMode = Schema.RequiredMode.REQUIRED)
    @JsonAlias({"name", "username", "userName", "userNickname", "memberName", "memberNickname"})
    @NotBlank(message = "닉네임은 필수입니다.")
    @Size(max = 50, message = "닉네임은 50자 이하여야 합니다.")
    private String nickname;

    @Schema(description = "Phone Number", example = "01012345678", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotBlank(message = "전화번호는 필수입니다.")
    @Pattern(regexp = "^[0-9]{10,11}$", message = "전화번호는 숫자만 10~11자리 입력 가능합니다.")
    private String phone;

    @Schema(description = "Birth Date", example = "2000-01-01", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotNull(message = "생년월일은 필수입니다.")
    private LocalDate birthDate;

    @Schema(description = "Social Signup Token", example = "eyJhbGciOiJIUzI1...", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
    private String signupToken;
}
