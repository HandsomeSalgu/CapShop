package com.syncshopper.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.syncshopper.common.exception.CustomException;
import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.config.NaverSearchProperties;
import com.syncshopper.domain.detection.Detection;
import com.syncshopper.domain.search.ProductCandidate;
import com.syncshopper.domain.search.SearchQuery;
import com.syncshopper.domain.search.SearchResult;
import com.syncshopper.domain.search.SearchSource;
import com.syncshopper.domain.user.UserEventType;
import com.syncshopper.dto.response.AiVerificationResponse;
import com.syncshopper.dto.response.DetectionAnalyzeResponse;
import com.syncshopper.dto.response.DetectionWebSearchResponse;
import com.syncshopper.dto.response.SearchCandidateResponse;
import com.syncshopper.dto.response.SearchQueryBundleResponse;
import com.syncshopper.dto.search.AiVerificationRequest;
import com.syncshopper.dto.search.NaverSearchApiResponse;
import com.syncshopper.dto.search.ScoredSearchCandidate;
import com.syncshopper.dto.search.SearchResultItem;
import com.syncshopper.mapper.DetectionMapper;
import com.syncshopper.mapper.DetectionSearchMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

@Slf4j
@RequiredArgsConstructor
@Service
public class DetectionWebSearchService {

    private static final int MAX_QUERIES_PER_SOURCE = 3;
    private static final int RESPONSE_CANDIDATE_LIMIT = 20;
    private static final int AI_VERIFICATION_LIMIT = 10;

    private final DetectionMapper detectionMapper;
    private final DetectionSearchMapper detectionSearchMapper;
    private final SearchQueryGenerator searchQueryGenerator;
    private final NaverSearchClient naverSearchClient;
    private final SearchResultNormalizer searchResultNormalizer;
    private final CandidateScorer candidateScorer;
    private final AiCandidateVerificationService aiCandidateVerificationService;
    private final UserEventService userEventService;
    private final NaverSearchProperties naverSearchProperties;
    private final ObjectMapper objectMapper;

    public DetectionWebSearchResponse search(Long userId, Long jobId) {
        Detection detection = detectionMapper.findByIdAndUserId(jobId, userId);
        if (detection == null) {
            throw new CustomException(ErrorCode.DETECTION_NOT_FOUND);
        }

        logUserEvent(userId, detection, UserEventType.WEB_SEARCH_STARTED, Map.of("job_id", jobId));

        try {
            SearchQueryBundleResponse queries = searchQueryGenerator.generate(detection);
            Map<String, Long> queryIds = persistGeneratedQueries(jobId, queries);
            SearchRunResult searchRunResult = executeSearches(queries, queryIds);
            List<ScoredSearchCandidate> candidates = persistAndScore(jobId, detection, searchRunResult.results());

            List<ScoredSearchCandidate> topCandidates = candidates.stream()
                    .sorted(Comparator.comparing(ScoredSearchCandidate::getFinalScore, Comparator.nullsLast(Comparator.reverseOrder())))
                    .limit(RESPONSE_CANDIDATE_LIMIT)
                    .toList();
            assignIndexes(topCandidates);

            DetectionAnalyzeResponse.DetectionSummary detectionSummary = toDetectionSummary(detection);
            AiVerificationResponse aiVerification = aiCandidateVerificationService.verify(AiVerificationRequest.builder()
                    .detection(detectionSummary)
                    .candidates(topCandidates.stream().limit(AI_VERIFICATION_LIMIT).toList())
                    .build());

            List<SearchCandidateResponse> candidateResponses = topCandidates.stream()
                    .map(candidate -> toCandidateResponse(candidate, aiCandidateVerificationService.matchLevel(candidate.getFinalScore())))
                    .toList();

            Map<String, Object> metadata = buildMetadata(queries, searchRunResult, candidateResponses, aiVerification);
            logUserEvent(userId, detection, UserEventType.WEB_SEARCH_COMPLETED, metadata);

            return DetectionWebSearchResponse.builder()
                    .jobId(jobId)
                    .detection(detectionSummary)
                    .queries(queries)
                    .candidates(candidateResponses)
                    .aiVerification(aiVerification)
                    .metadata(metadata)
                    .message(candidateResponses.isEmpty()
                            ? "검색은 완료되었지만 후보 결과가 없습니다."
                            : "Detection 기반 웹 검색이 완료되었습니다.")
                    .build();
        } catch (RuntimeException e) {
            logUserEvent(userId, detection, UserEventType.WEB_SEARCH_FAILED, Map.of(
                    "job_id", jobId,
                    "error", e.getMessage() == null ? e.getClass().getSimpleName() : e.getMessage()
            ));
            throw e;
        }
    }

    private SearchRunResult executeSearches(SearchQueryBundleResponse queries, Map<String, Long> queryIds) {
        List<NormalizedSearchResult> results = new ArrayList<>();
        List<Map<String, Object>> failures = new ArrayList<>();
        int cacheHits = 0;

        cacheHits += executeSource(SearchSource.NAVER_SHOPPING, shoppingPlan(queries), queryIds, results, failures);
        cacheHits += executeSource(SearchSource.NAVER_IMAGE, sourcePlan("IMAGE", SearchSource.NAVER_IMAGE, queries.getPrimaryQueries(), queries.getImageQueries()), queryIds, results, failures);
        cacheHits += executeSource(SearchSource.NAVER_BLOG, sourcePlan("BLOG", SearchSource.NAVER_BLOG, queries.getPrimaryQueries(), queries.getBlogQueries()), queryIds, results, failures);
        cacheHits += executeSource(SearchSource.NAVER_CAFE, sourcePlan("CAFE", SearchSource.NAVER_CAFE, queries.getPrimaryQueries(), queries.getCafeQueries()), queryIds, results, failures);
        cacheHits += executeSource(SearchSource.NAVER_WEB, sourcePlan("WEB", SearchSource.NAVER_WEB, queries.getPrimaryQueries(), queries.getWebQueries()), queryIds, results, failures);

        boolean fallbackUsed = false;
        if (results.isEmpty() && queries.getFallbackQueries() != null && !queries.getFallbackQueries().isEmpty()) {
            fallbackUsed = true;
            List<PlannedQuery> fallbackPlan = fallbackPlan(queries);
            cacheHits += executeSource(SearchSource.NAVER_SHOPPING, fallbackPlan, queryIds, results, failures);
            cacheHits += executeSource(SearchSource.NAVER_WEB, fallbackPlan, queryIds, results, failures);
        }

        return new SearchRunResult(results, failures, cacheHits, fallbackUsed);
    }

    private int executeSource(
            SearchSource source,
            List<PlannedQuery> plannedQueries,
            Map<String, Long> queryIds,
            List<NormalizedSearchResult> results,
            List<Map<String, Object>> failures
    ) {
        int cacheHits = 0;
        for (PlannedQuery plannedQuery : plannedQueries) {
            NaverSearchApiResponse response = switch (source) {
                case NAVER_SHOPPING -> naverSearchClient.searchShopping(plannedQuery.queryText(), display());
                case NAVER_IMAGE -> naverSearchClient.searchImage(plannedQuery.queryText(), display());
                case NAVER_BLOG -> naverSearchClient.searchBlog(plannedQuery.queryText(), display());
                case NAVER_CAFE -> naverSearchClient.searchCafe(plannedQuery.queryText(), display());
                case NAVER_WEB -> naverSearchClient.searchWeb(plannedQuery.queryText(), display());
            };

            if (!response.isSuccess()) {
                Map<String, Object> failure = new LinkedHashMap<>();
                failure.put("source", source.name());
                failure.put("query_text", plannedQuery.queryText());
                failure.put("status", response.getStatusCode());
                failure.put("error_message", response.getErrorMessage());
                failures.add(failure);
                continue;
            }

            if (response.isCached()) {
                cacheHits++;
            }

            Long queryId = queryIds.get(queryKey(plannedQuery.queryType(), plannedQuery.sourceTarget(), plannedQuery.queryText()));
            searchResultNormalizer.normalize(response, plannedQuery.queryType()).forEach(item ->
                    results.add(new NormalizedSearchResult(queryId, item))
            );
        }
        return cacheHits;
    }

    private List<ScoredSearchCandidate> persistAndScore(
            Long jobId,
            Detection detection,
            List<NormalizedSearchResult> results
    ) {
        Set<String> seen = new LinkedHashSet<>();
        List<ScoredSearchCandidate> candidates = new ArrayList<>();

        for (NormalizedSearchResult normalized : results) {
            SearchResultItem item = normalized.item();
            if (!seen.add(deduplicateKey(item))) {
                continue;
            }

            SearchResult searchResult = SearchResult.builder()
                    .jobId(jobId)
                    .queryId(normalized.queryId())
                    .source(item.getSource().name())
                    .title(item.getTitle())
                    .url(item.getLink())
                    .imageUrl(firstNonBlank(item.getImageUrl(), item.getThumbnailUrl()))
                    .snippet(item.getSnippet())
                    .price(item.getPrice())
                    .mallName(item.getMallName())
                    .rawJson(toJson(item.getRaw()))
                    .build();
            detectionSearchMapper.insertSearchResult(searchResult);

            ScoredSearchCandidate scored = candidateScorer.score(detection, item);
            scored.setResultId(searchResult.getResultId());

            ProductCandidate productCandidate = ProductCandidate.builder()
                    .jobId(jobId)
                    .resultId(searchResult.getResultId())
                    .productName(item.getTitle())
                    .brand(firstNonBlank(item.getBrand(), detection.getBrand()))
                    .category(firstNonBlank(item.getCategory(), detection.getCategoryName()))
                    .imageUrl(firstNonBlank(item.getImageUrl(), item.getThumbnailUrl()))
                    .productUrl(item.getLink())
                    .price(item.getPrice())
                    .visualScore(scored.getVisualScore())
                    .textScore(scored.getTextScore())
                    .finalScore(scored.getFinalScore())
                    .reason(scored.getReason())
                    .build();
            detectionSearchMapper.insertProductCandidate(productCandidate);
            candidates.add(scored);
        }

        return candidates;
    }

    private Map<String, Long> persistGeneratedQueries(Long jobId, SearchQueryBundleResponse queries) {
        Map<String, Long> queryIds = new LinkedHashMap<>();
        persistQueryGroup(jobId, "PRIMARY", "ALL", queries.getPrimaryQueries(), queryIds);
        persistQueryGroup(jobId, "SHOPPING", SearchSource.NAVER_SHOPPING.name(), queries.getShoppingQueries(), queryIds);
        persistQueryGroup(jobId, "IMAGE", SearchSource.NAVER_IMAGE.name(), queries.getImageQueries(), queryIds);
        persistQueryGroup(jobId, "BLOG", SearchSource.NAVER_BLOG.name(), queries.getBlogQueries(), queryIds);
        persistQueryGroup(jobId, "CAFE", SearchSource.NAVER_CAFE.name(), queries.getCafeQueries(), queryIds);
        persistQueryGroup(jobId, "WEB", SearchSource.NAVER_WEB.name(), queries.getWebQueries(), queryIds);
        persistQueryGroup(jobId, "FALLBACK", "ALL", queries.getFallbackQueries(), queryIds);
        return queryIds;
    }

    private void persistQueryGroup(
            Long jobId,
            String queryType,
            String sourceTarget,
            List<String> queryTexts,
            Map<String, Long> queryIds
    ) {
        if (queryTexts == null) {
            return;
        }

        for (String queryText : queryTexts) {
            if (queryText == null || queryText.isBlank()) {
                continue;
            }

            String key = queryKey(queryType, sourceTarget, queryText);
            if (queryIds.containsKey(key)) {
                continue;
            }

            SearchQuery searchQuery = SearchQuery.builder()
                    .jobId(jobId)
                    .queryText(queryText)
                    .queryType(queryType)
                    .sourceTarget(sourceTarget)
                    .build();
            detectionSearchMapper.insertSearchQuery(searchQuery);
            queryIds.put(key, searchQuery.getQueryId());
        }
    }

    private List<PlannedQuery> shoppingPlan(SearchQueryBundleResponse queries) {
        return sourcePlan("SHOPPING", SearchSource.NAVER_SHOPPING, queries.getPrimaryQueries(), queries.getShoppingQueries());
    }

    private List<PlannedQuery> sourcePlan(
            String queryType,
            SearchSource source,
            List<String> primaryQueries,
            List<String> sourceQueries
    ) {
        List<PlannedQuery> plannedQueries = new ArrayList<>();
        appendPlannedQueries(plannedQueries, "PRIMARY", "ALL", primaryQueries);
        appendPlannedQueries(plannedQueries, queryType, source.name(), sourceQueries);
        return plannedQueries.stream()
                .filter(plannedQuery -> plannedQuery.queryText() != null && !plannedQuery.queryText().isBlank())
                .collect(LinkedHashMap<String, PlannedQuery>::new,
                        (map, query) -> map.putIfAbsent(query.queryText().toLowerCase(), query),
                        Map::putAll)
                .values()
                .stream()
                .limit(MAX_QUERIES_PER_SOURCE)
                .toList();
    }

    private List<PlannedQuery> fallbackPlan(SearchQueryBundleResponse queries) {
        List<PlannedQuery> plannedQueries = new ArrayList<>();
        appendPlannedQueries(plannedQueries, "FALLBACK", "ALL", queries.getFallbackQueries());
        return plannedQueries.stream().limit(MAX_QUERIES_PER_SOURCE).toList();
    }

    private void appendPlannedQueries(
            List<PlannedQuery> target,
            String queryType,
            String sourceTarget,
            List<String> queries
    ) {
        if (queries == null) {
            return;
        }
        queries.forEach(query -> target.add(new PlannedQuery(queryType, sourceTarget, query)));
    }

    private DetectionAnalyzeResponse.DetectionSummary toDetectionSummary(Detection detection) {
        return DetectionAnalyzeResponse.DetectionSummary.builder()
                .targetName(detection.getTargetName())
                .categoryName(detection.getCategoryName())
                .brand(detection.getBrand())
                .modelName(detection.getModelName())
                .color(detection.getColor())
                .shape(detection.getShape())
                .logoText(detection.getLogoText())
                .keyFeatures(keyFeaturesFromJson(detection.getKeyFeaturesJson()))
                .confidence(detection.getConfidence())
                .build();
    }

    private SearchCandidateResponse toCandidateResponse(ScoredSearchCandidate candidate, String matchLevel) {
        SearchResultItem result = candidate.getResult();
        return SearchCandidateResponse.builder()
                .index(candidate.getIndex())
                .source(result.getSource().name())
                .sourceLabel(result.getSource().getLabel())
                .queryType(result.getQueryType())
                .queryText(result.getQueryText())
                .title(result.getTitle())
                .url(result.getLink())
                .imageUrl(firstNonBlank(result.getImageUrl(), result.getThumbnailUrl()))
                .thumbnailUrl(result.getThumbnailUrl())
                .snippet(result.getSnippet())
                .price(result.getPrice())
                .mallName(result.getMallName())
                .score(candidate.getFinalScore())
                .matchLevel(matchLevel)
                .reason(candidate.getReason())
                .build();
    }

    private Map<String, Object> buildMetadata(
            SearchQueryBundleResponse queries,
            SearchRunResult searchRunResult,
            List<SearchCandidateResponse> candidates,
            AiVerificationResponse aiVerification
    ) {
        Map<String, Object> metadata = new LinkedHashMap<>();
        metadata.put("query_count", queryCount(queries));
        metadata.put("result_count", searchRunResult.results().size());
        metadata.put("candidate_count", candidates.size());
        metadata.put("cache_hit_count", searchRunResult.cacheHits());
        metadata.put("fallback_used", searchRunResult.fallbackUsed());
        metadata.put("partial", !searchRunResult.failures().isEmpty());
        metadata.put("failures", searchRunResult.failures());
        if (!candidates.isEmpty()) {
            metadata.put("top_source", candidates.getFirst().getSource());
            metadata.put("best_candidate_url", candidates.getFirst().getUrl());
        }
        if (aiVerification != null) {
            metadata.put("match_level", aiVerification.getMatchLevel());
            metadata.put("confidence", aiVerification.getConfidence());
        }
        return metadata;
    }

    private int queryCount(SearchQueryBundleResponse queries) {
        return size(queries.getPrimaryQueries())
                + size(queries.getShoppingQueries())
                + size(queries.getImageQueries())
                + size(queries.getBlogQueries())
                + size(queries.getCafeQueries())
                + size(queries.getWebQueries())
                + size(queries.getFallbackQueries());
    }

    private int size(List<?> values) {
        return values == null ? 0 : values.size();
    }

    private void assignIndexes(List<ScoredSearchCandidate> candidates) {
        for (int index = 0; index < candidates.size(); index++) {
            candidates.get(index).setIndex(index);
        }
    }

    private void logUserEvent(
            Long userId,
            Detection detection,
            UserEventType eventType,
            Map<String, Object> metadata
    ) {
        try {
            userEventService.createInternalEvent(
                    userId,
                    null,
                    null,
                    eventType,
                    "DETECTION_WEB_SEARCH",
                    detection.getVideoId(),
                    detection.getCategoryName(),
                    detection.getBrand(),
                    null,
                    metadata
            );
        } catch (RuntimeException e) {
            log.warn("Failed to save web-search user event. eventType={} detectionId={}", eventType, detection.getDetectionId(), e);
        }
    }

    private List<String> keyFeaturesFromJson(String value) {
        if (value == null || value.isBlank()) {
            return List.of();
        }

        try {
            return objectMapper.readerForListOf(String.class).readValue(value);
        } catch (Exception e) {
            return List.of();
        }
    }

    private String toJson(Object value) {
        try {
            return objectMapper.writeValueAsString(value == null ? Map.of() : value);
        } catch (JsonProcessingException e) {
            return "{}";
        }
    }

    private String deduplicateKey(SearchResultItem item) {
        if (item.getLink() != null && !item.getLink().isBlank()) {
            return item.getSource().name() + ":link:" + item.getLink();
        }
        return item.getSource().name() + ":title:" + item.getTitle();
    }

    private String queryKey(String queryType, String sourceTarget, String queryText) {
        return queryType + "|" + sourceTarget + "|" + queryText.trim().toLowerCase();
    }

    private int display() {
        Integer display = naverSearchProperties.getSearch() == null ? null : naverSearchProperties.getSearch().getDisplay();
        if (display == null || display < 1) {
            return 5;
        }
        return Math.min(display, 100);
    }

    private String firstNonBlank(String first, String second) {
        return first != null && !first.isBlank() ? first : second;
    }

    private record PlannedQuery(String queryType, String sourceTarget, String queryText) {
    }

    private record NormalizedSearchResult(Long queryId, SearchResultItem item) {
    }

    private record SearchRunResult(
            List<NormalizedSearchResult> results,
            List<Map<String, Object>> failures,
            int cacheHits,
            boolean fallbackUsed
    ) {
    }
}
