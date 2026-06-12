package com.syncshopper.service;

import com.syncshopper.common.exception.CustomException;
import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.domain.post.Post;
import com.syncshopper.domain.post.PostType;
import com.syncshopper.dto.request.PostSearchCondition;
import com.syncshopper.dto.response.PageResponse;
import com.syncshopper.dto.response.PostDetailResponse;
import com.syncshopper.dto.response.PostListResponse;
import com.syncshopper.mapper.PostMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@RequiredArgsConstructor
@Service
public class PostService {

    private static final int DEFAULT_PAGE = 1;
    private static final int DEFAULT_SIZE = 10;
    private static final int MAX_SIZE = 50;

    private final PostMapper postMapper;

    public PageResponse<PostListResponse> getPosts(PostSearchCondition condition) {
        PostSearchCondition normalizedCondition = normalizeCondition(condition);

        long totalCount = postMapper.countPosts(normalizedCondition);
        List<PostListResponse> posts = postMapper.findPosts(normalizedCondition).stream()
                .map(PostListResponse::from)
                .toList();

        return PageResponse.of(
                posts,
                normalizedCondition.getPage(),
                normalizedCondition.getSize(),
                totalCount
        );
    }

    public PostDetailResponse getPostDetail(Long postId) {
        return PostDetailResponse.from(findVisiblePost(postId));
    }

    public PageResponse<PostListResponse> getNotices(int page, int size) {
        return getPosts(PostSearchCondition.builder()
                .postType(PostType.NOTICE)
                .page(page)
                .size(size)
                .build());
    }

    public PageResponse<PostListResponse> getFaqs(int page, int size) {
        return getPosts(PostSearchCondition.builder()
                .postType(PostType.FAQ)
                .page(page)
                .size(size)
                .build());
    }

    public PageResponse<PostListResponse> getEvents(int page, int size) {
        return getPosts(PostSearchCondition.builder()
                .postType(PostType.EVENT)
                .page(page)
                .size(size)
                .build());
    }

    private PostSearchCondition normalizeCondition(PostSearchCondition condition) {
        PostSearchCondition normalizedCondition = condition == null ? new PostSearchCondition() : condition;

        int page = normalizedCondition.getPage() == null || normalizedCondition.getPage() < 1
                ? DEFAULT_PAGE
                : normalizedCondition.getPage();
        int size = normalizedCondition.getSize() == null || normalizedCondition.getSize() < 1
                ? DEFAULT_SIZE
                : Math.min(normalizedCondition.getSize(), MAX_SIZE);

        normalizedCondition.setPage(page);
        normalizedCondition.setSize(size);
        normalizedCondition.setOffset((page - 1) * size);

        return normalizedCondition;
    }

    private Post findVisiblePost(Long postId) {
        Post post = postMapper.findVisiblePostById(postId);
        if (post == null) {
            throw new CustomException(ErrorCode.POST_NOT_FOUND);
        }
        return post;
    }
}
