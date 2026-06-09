package com.syncshopper.config;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.context.annotation.Configuration;

@Configuration
@MapperScan("com.syncshopper.mapper")
public class MyBatisConfig {
}
