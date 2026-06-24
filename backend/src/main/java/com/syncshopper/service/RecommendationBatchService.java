package com.syncshopper.service;

import com.syncshopper.domain.recommendation.UserKeywordScore;
import com.syncshopper.domain.user.User;
import com.syncshopper.mapper.RecommendationMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

@Slf4j
@Service
public class RecommendationBatchService {

    private final UserService userService;
    private final RecommendationMapper recommendationMapper;
    private final RedisTemplate<String, Object> redisTemplate;

    public RecommendationBatchService(UserService userService, RecommendationMapper recommendationMapper, RedisTemplate<String, Object> redisTemplate) {
        this.userService = userService;
        this.recommendationMapper = recommendationMapper;
        this.redisTemplate = redisTemplate;
    }

    // 매시간 정각에 실행
    @Scheduled(cron = "0 0 * * * *")
    public void aggregateRecommendationKeywords() {
        log.info("Starting RecommendationBatchService keyword aggregation...");

        List<User> activeUsers = userService.findAllActiveUsers();
        
        for (User user : activeUsers) {
            Long userId = user.getUserId();
            List<UserKeywordScore> topKeywords = recommendationMapper.findTopKeywordsByUserId(userId, 3);
            
            if (topKeywords != null && !topKeywords.isEmpty()) {
                List<String> keywordsToCache = topKeywords.stream()
                        .map(UserKeywordScore::getKeyword)
                        .collect(Collectors.toList());
                
                String redisKey = "user:" + userId + ":recommend_keywords";
                
                // Redis에 캐싱 (TTL: 2시간) - Jackson 제네릭 에러 방지를 위해 콤마로 연결한 String으로 저장
                String joinedKeywords = String.join(",", keywordsToCache);
                redisTemplate.opsForValue().set(redisKey, joinedKeywords, 2, TimeUnit.HOURS);
                
                log.debug("User {} top keywords cached: {}", userId, keywordsToCache);
            }
        }
        
        log.info("Finished RecommendationBatchService keyword aggregation.");
    }
}
