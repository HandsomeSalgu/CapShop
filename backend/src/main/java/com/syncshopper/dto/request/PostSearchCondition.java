package com.syncshopper.dto.request;

import com.syncshopper.domain.post.PostType;
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
@Schema(description = "Post search condition")
public class PostSearchCondition {

    @Schema(description = "Post type: NOTICE, FAQ, EVENT", example = "NOTICE")
    private PostType postType;

    @Schema(description = "Keyword for title or content", example = "shipping")
    private String keyword;

    @Schema(description = "Page number, starts at 1", example = "1")
    private Integer page;

    @Schema(description = "Page size", example = "10")
    private Integer size;

    @Schema(hidden = true)
    private Integer offset;
}
