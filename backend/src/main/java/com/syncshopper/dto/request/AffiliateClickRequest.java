package com.syncshopper.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotNull;
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
@Schema(description = "Affiliate click log request")
public class AffiliateClickRequest {

    @NotNull(message = "Product ID is required.")
    @Schema(description = "Product ID", example = "1", requiredMode = Schema.RequiredMode.REQUIRED)
    private Long productId;

    @Schema(description = "Recommendation ID", example = "10")
    private Long recommendationId;

    @Schema(description = "Click source", example = "PRODUCT_DETAIL")
    private String source;

    @Schema(description = "Affiliate target URL", example = "https://example.com/buy/product1")
    private String targetUrl;

    @Schema(description = "Video ID", example = "youtube-video-id")
    private String videoId;

    @Schema(description = "Category name", example = "Fashion")
    private String categoryName;

    @Schema(description = "Brand name", example = "Nike")
    private String brand;
}
