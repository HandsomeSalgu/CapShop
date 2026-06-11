package com.syncshopper.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "Product search condition")
public class ProductSearchCondition {

    @Schema(description = "Category ID", example = "1")
    private Long categoryId;

    @Schema(description = "Keyword for title, brand, or category name", example = "Nike")
    private String keyword;

    @Schema(description = "Sort type: latest, priceAsc, priceDesc, rating, popular", example = "latest")
    private String sort;

    @Schema(description = "Page number, starts at 1", example = "1")
    private Integer page;

    @Schema(description = "Page size", example = "12")
    private Integer size;

    @Schema(hidden = true)
    private Integer offset;
}
