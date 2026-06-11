package com.syncshopper.mapper;

import com.syncshopper.domain.user.UserEvent;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface UserEventMapper {

    int insertUserEvent(UserEvent userEvent);

    UserEvent findById(@Param("eventId") Long eventId);
}
