package com.syncshopper.mapper;

import com.syncshopper.domain.detection.AiAnalysisLog;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface AiAnalysisLogMapper {

    int insertAiAnalysisLog(AiAnalysisLog aiAnalysisLog);
}
