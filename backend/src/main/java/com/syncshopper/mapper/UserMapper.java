package com.syncshopper.mapper;

import com.syncshopper.domain.user.User;

import java.util.List;

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

    List<User> findAllUsers(@Param("offset") int offset, @Param("limit") int limit, @Param("keyword") String keyword);

    long countAllUsers(@Param("keyword") String keyword);

    int updateUserStatus(@Param("userId") Long userId, @Param("status") String status);

    int updateUserRole(@Param("userId") Long userId, @Param("role") String role);

    User findByNicknameAndPhone(@Param("nickname") String nickname, @Param("phone") String phone);

    User findByEmailAndNicknameAndPhone(@Param("email") String email, @Param("nickname") String nickname, @Param("phone") String phone);

    List<User> findAllActiveUsers();
}
