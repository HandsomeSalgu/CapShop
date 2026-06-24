package com.syncshopper.mapper;

import com.syncshopper.domain.user.UserEvent;
import com.syncshopper.dto.response.ViewHistoryResponse;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface UserEventMapper {

    int insertUserEvent(UserEvent userEvent);

    UserEvent findById(@Param("eventId") Long eventId);

    List<ViewHistoryResponse> findViewHistory(
            @Param("userId") Long userId,
            @Param("keyword") String keyword,
            @Param("category") String category,
            @Param("offset") int offset,
            @Param("size") int size
    );

    long countViewHistory(
            @Param("userId") Long userId,
            @Param("keyword") String keyword,
            @Param("category") String category
    );
}
