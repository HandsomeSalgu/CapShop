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
public class AffiliateClick {

    private Long clickId;
    private Long userId;
    private Long productId;
    private Long recommendationId;
    private String source;
    private LocalDateTime clickedAt;
}
