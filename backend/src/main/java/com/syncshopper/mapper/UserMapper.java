package com.syncshopper.mapper;

import com.syncshopper.domain.user.User;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface UserMapper {

    int insertUser(User user);

    User findById(Long userId);

    User findByEmail(String email);

    User findByProviderAndProviderId(@Param("provider") String provider, @Param("providerId") String providerId);

    int existsByEmail(String email);

    int updateLastLoginAt(Long userId);

    int updateOAuthUser(User user);

    int updateProfile(User user);

    int updatePassword(@Param("userId") Long userId, @Param("password") String password);
}
