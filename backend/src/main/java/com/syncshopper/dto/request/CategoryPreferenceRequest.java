package com.syncshopper.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "Category preference request")
public class CategoryPreferenceRequest {

    @Schema(description = "Category 1 Name (Major)", example = "패션/의류")
    private String category1Name;

    @Schema(description = "Category 2 Name (Minor)", example = "여성 의류")
    private String category2Name;
}
