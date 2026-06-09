package com.syncshopper.controller;

import com.syncshopper.common.response.ApiResponse;
import com.syncshopper.mapper.HealthMapper;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@Tag(name = "Health", description = "서버 및 DB 상태 확인 API")
@RestController
public class HealthController {

    private final HealthMapper healthMapper;

    public HealthController(HealthMapper healthMapper) {
        this.healthMapper = healthMapper;
    }

    @Operation(summary = "서버 상태 확인", description = "Spring Boot 서버가 정상적으로 실행 중인지 확인합니다.")
    @GetMapping("/api/health")
    public ApiResponse<Map<String, String>> health() {
        return ApiResponse.success(
                "서버가 정상적으로 실행 중입니다.",
                Map.of("status", "UP")
        );
    }

    @Operation(summary = "DB 연결 상태 확인", description = "MyBatis를 통해 DB 연결 상태를 확인합니다.")
    @GetMapping("/api/health/db")
    public ApiResponse<Map<String, Object>> dbHealth() {
        Integer result = healthMapper.selectOne();

        return ApiResponse.success(
                "DB 연결이 정상입니다.",
                Map.of("db", "UP", "result", result)
        );
    }
}
