package com.syncshopper.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
@Schema(description = "Password verify request")
public class PasswordVerifyRequest {

    @NotBlank(message = "Password is required.")
    @Schema(description = "Current password to verify", example = "password1234", requiredMode = Schema.RequiredMode.REQUIRED)
    private String password;
}
