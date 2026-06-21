package com.syncshopper.dto.request;

import com.fasterxml.jackson.annotation.JsonProperty;
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
public class AiCommerceQueryRequest {

    @JsonProperty("target_name")
    private String targetName;

    @JsonProperty("category_name")
    private String categoryName;

    private String brand;

    @JsonProperty("model_name")
    private String modelName;

    private Double confidence;

    @JsonProperty("subtitle_text")
    private String subtitleText;

    @JsonProperty("video_id")
    private String videoId;

    @JsonProperty("timestamp_sec")
    private Integer timestampSec;
}
