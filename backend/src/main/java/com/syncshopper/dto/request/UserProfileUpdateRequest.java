package com.syncshopper.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Past;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDate;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
@Schema(description = "User profile update request")
public class UserProfileUpdateRequest {

    @NotBlank(message = "Nickname is required.")
    @Size(min = 2, max = 30, message = "Nickname must be between 2 and 30 characters.")
    @Schema(description = "Nickname", example = "hwarang", requiredMode = Schema.RequiredMode.REQUIRED)
    private String nickname;

    @Pattern(regexp = "^[0-9-]*$", message = "Phone number can contain only numbers and hyphens.")
    @Schema(description = "Phone number", example = "010-1234-5678")
    private String phone;

    @Past(message = "Birth date must be in the past.")
    @Schema(description = "Birth date", example = "1997-01-01")
    private LocalDate birthDate;

    @Schema(description = "Profile image URL", example = "https://example.com/profile.jpg")
    private String profileImageUrl;
}
