package com.syncshopper.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
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
@Schema(description = "Video frame analysis request")
public class DetectionAnalyzeRequest {

    @NotBlank(message = "Video ID is required.")
    @Size(max = 100, message = "Video ID must be 100 characters or fewer.")
    @Schema(description = "YouTube video ID", example = "youtube-video-id-123")
    private String videoId;

    @NotNull(message = "Timestamp is required.")
    @Min(value = 0, message = "Timestamp must be 0 seconds or greater.")
    @Schema(description = "Video timestamp in seconds", example = "135")
    private Integer timestampSec;

    @NotBlank(message = "Frame image is required.")
    @Schema(description = "Base64 encoded frame image")
    private String imageBase64;

    @Schema(description = "Subtitle text around the frame", example = "Introducing today's Nike sneakers.")
    private String subtitleText;
}
