package com.syncshopper.mapper;

import com.syncshopper.domain.user.UserPreference;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface UserPreferenceMapper {
    void insertUserPreference(UserPreference userPreference);
}
