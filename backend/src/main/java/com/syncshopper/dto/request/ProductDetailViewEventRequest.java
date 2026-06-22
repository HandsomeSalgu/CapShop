package com.syncshopper.dto.request;

import com.syncshopper.dto.response.CommerceProductResponse;
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
@Schema(description = "Product detail view event request")
public class ProductDetailViewEventRequest {

    @Schema(description = "Product ID", example = "1")
    private Long productId;

    @Schema(description = "Product information for upserting")
    private CommerceProductResponse product;

    @Schema(description = "Previous page before entering product detail", example = "PRODUCT_LIST")
    private String sourcePage;
}
