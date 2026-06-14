package com.syncshopper.mapper;

import com.syncshopper.domain.detection.Detection;
import com.syncshopper.domain.detection.DetectionStatus;
import com.syncshopper.dto.response.DetectionHistoryResponse;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface DetectionMapper {

    int insertDetection(Detection detection);

    int updateDetectionResult(Detection detection);

    int updateDetectionFailed(
            @Param("detectionId") Long detectionId,
            @Param("status") DetectionStatus status
    );

    Detection findByIdAndUserId(
            @Param("detectionId") Long detectionId,
            @Param("userId") Long userId
    );

    List<DetectionHistoryResponse> findMyDetections(
            @Param("userId") Long userId,
            @Param("offset") int offset,
            @Param("size") int size
    );

    long countMyDetections(@Param("userId") Long userId);
}
