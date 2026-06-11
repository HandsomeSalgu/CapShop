package com.syncshopper.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
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
@Schema(description = "Password change request")
public class PasswordChangeRequest {

    @NotBlank(message = "Current password is required.")
    @Schema(description = "Current password", example = "password1234", requiredMode = Schema.RequiredMode.REQUIRED)
    private String currentPassword;

    @NotBlank(message = "New password is required.")
    @Size(min = 8, max = 30, message = "New password must be between 8 and 30 characters.")
    @Schema(description = "New password", example = "newPassword1234", requiredMode = Schema.RequiredMode.REQUIRED)
    private String newPassword;

    @NotBlank(message = "New password confirmation is required.")
    @Schema(description = "New password confirmation", example = "newPassword1234", requiredMode = Schema.RequiredMode.REQUIRED)
    private String confirmNewPassword;
}
