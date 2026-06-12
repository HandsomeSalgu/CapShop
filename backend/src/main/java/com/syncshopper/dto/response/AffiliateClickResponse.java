package com.syncshopper.dto.response;

import com.syncshopper.domain.user.AffiliateClick;
import io.swagger.v3.oas.annotations.media.Schema;
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
@Schema(description = "Affiliate click save response")
public class AffiliateClickResponse {

    private Long clickId;
    private Long productId;
    private Long recommendationId;
    private String source;
    private LocalDateTime clickedAt;

    public static AffiliateClickResponse from(AffiliateClick affiliateClick) {
        return AffiliateClickResponse.builder()
                .clickId(affiliateClick.getClickId())
                .productId(affiliateClick.getProductId())
                .recommendationId(affiliateClick.getRecommendationId())
                .source(affiliateClick.getSource())
                .clickedAt(affiliateClick.getClickedAt())
                .build();
    }
}
