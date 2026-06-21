package com.syncshopper.mapper;

import com.syncshopper.domain.post.Post;
import com.syncshopper.dto.request.PostSearchCondition;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface PostMapper {

    List<Post> findPosts(PostSearchCondition condition);

    long countPosts(PostSearchCondition condition);

    Post findVisiblePostById(@Param("postId") Long postId);

    Post findById(@Param("postId") Long postId);

    void insertPost(Post post);

    void updatePost(Post post);
}
