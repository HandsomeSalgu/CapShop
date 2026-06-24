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
    private String category1Name;
    private String category2Name;
    private String brand;
    private LocalDateTime createdAt;
}
