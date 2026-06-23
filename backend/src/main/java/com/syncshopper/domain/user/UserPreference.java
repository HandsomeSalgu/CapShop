package com.syncshopper.domain.user;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class UserPreference {
    private Long preferenceId;
    private Long userId;
    private Long categoryId;
    private String categoryName;
    private String brand;
    private Integer priceMin;
    private Integer priceMax;
    private LocalDateTime createdAt;
}
