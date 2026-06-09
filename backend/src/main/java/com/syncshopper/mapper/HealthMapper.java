package com.syncshopper.mapper;

import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface HealthMapper {
    Integer selectOne();
}
