package com.syncshopper.dto.response;

import com.syncshopper.domain.post.Post;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "Post list response")
public class PostListResponse {

    private Long postId;
    private String title;
    private String postType;
    private LocalDateTime createdAt;

    public static PostListResponse from(Post post) {
        return PostListResponse.builder()
                .postId(post.getPostId())
                .title(post.getTitle())
                .postType(post.getPostType().name())
                .createdAt(post.getCreatedAt())
                .build();
    }
}
