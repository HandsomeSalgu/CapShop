package com.syncshopper.dto.response;

import com.syncshopper.domain.user.UserEvent;
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
@Schema(description = "User event save response")
public class UserEventResponse {

    @Schema(description = "Event ID", example = "10")
    private Long eventId;

    @Schema(description = "Product ID", example = "1")
    private Long productId;

    @Schema(description = "Event type", example = "PRODUCT_DETAIL_VIEW")
    private String eventType;

    @Schema(description = "Previous page before entering product detail", example = "PRODUCT_LIST")
    private String sourcePage;

    @Schema(description = "Event creation time")
    private LocalDateTime createdAt;

    public static UserEventResponse from(UserEvent userEvent) {
        return UserEventResponse.builder()
                .eventId(userEvent.getEventId())
                .productId(userEvent.getProductId())
                .eventType(userEvent.getEventType().name())
                .sourcePage(userEvent.getSourcePage())
                .createdAt(userEvent.getCreatedAt())
                .build();
    }
}
