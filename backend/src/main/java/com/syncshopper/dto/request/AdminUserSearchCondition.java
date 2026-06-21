package com.syncshopper.dto.request;

import io.swagger.v3.oas.annotations.Parameter;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class AdminUserSearchCondition {
    @Parameter(description = "Page number, starts at 1", example = "1")
    private int page = 1;

    @Parameter(description = "Page size", example = "10")
    private int size = 10;

    @Parameter(description = "Search keyword (nickname or email)", example = "hong")
    private String keyword;
}
