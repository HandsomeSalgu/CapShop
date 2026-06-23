package com.syncshopper.service;

import com.syncshopper.domain.detection.Detection;
import com.syncshopper.domain.search.SearchSource;
import com.syncshopper.dto.search.ScoredSearchCandidate;
import com.syncshopper.dto.search.SearchResultItem;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

@Component
public class CandidateScorer {

    public ScoredSearchCandidate score(Detection detection, SearchResultItem result) {
        String searchableText = normalize(String.join(" ",
                nullToEmpty(result.getTitle()),
                nullToEmpty(result.getSnippet()),
                nullToEmpty(result.getCategory()),
                nullToEmpty(result.getMallName())
        ));

        List<String> reasons = new ArrayList<>();
        double textScore = 0;
        double visualScore = 0;

        if (contains(searchableText, detection.getLogoText())) {
            textScore += 28;
            reasons.add("logoText matched");
        }
        if (contains(searchableText, detection.getBrand())) {
            textScore += 18;
            reasons.add("brand matched");
        }
        if (contains(searchableText, detection.getModelName())) {
            textScore += 22;
            reasons.add("model matched");
        }
        if (containsAny(searchableText, colorTerms(detection.getColor()))) {
            textScore += 10;
            reasons.add("color matched");
        }
        if (containsAny(searchableText, productTerms(detection))) {
            textScore += 12;
            reasons.add("product/category matched");
        }

        int targetMatches = targetTokenMatches(searchableText, detection.getTargetName());
        if (targetMatches > 0) {
            textScore += Math.min(20, targetMatches * 5.0);
            reasons.add("target terms matched");
        }

        double sourceScore = sourceBonus(result.getSource());
        if (sourceScore > 0) {
            reasons.add(result.getSource().name() + " source bonus");
        }

        if (hasText(result.getImageUrl()) || hasText(result.getThumbnailUrl())) {
            visualScore += 8;
            reasons.add("image present");
        }

        double penalty = 0;
        if (!hasText(result.getLink())) {
            penalty += 15;
            reasons.add("missing link penalty");
        }
        if (!hasText(result.getSnippet()) && result.getSource() != SearchSource.NAVER_IMAGE) {
            penalty += 5;
            reasons.add("weak snippet penalty");
        }

        double finalScore = clamp(textScore + visualScore + sourceScore - penalty);
        if (reasons.isEmpty()) {
            reasons.add("kept as broad fallback candidate");
        }

        return ScoredSearchCandidate.builder()
                .result(result)
                .visualScore(round(visualScore))
                .textScore(round(textScore))
                .finalScore(round(finalScore))
                .reason(String.join(", ", reasons))
                .build();
    }

    private double sourceBonus(SearchSource source) {
        if (source == null) {
            return 0;
        }

        return switch (source) {
            case NAVER_SHOPPING -> 18;
            case NAVER_IMAGE -> 10;
            case NAVER_BLOG, NAVER_CAFE -> 6;
            case NAVER_WEB -> 5;
        };
    }

    private int targetTokenMatches(String searchableText, String targetName) {
        if (!hasText(targetName)) {
            return 0;
        }

        int matches = 0;
        for (String token : targetName.toLowerCase(Locale.ROOT).split("[^a-z0-9가-힣]+")) {
            if (token.length() < 3) {
                continue;
            }
            if (searchableText.contains(token)) {
                matches++;
            }
        }
        return matches;
    }

    private List<String> productTerms(Detection detection) {
        String source = normalize(String.join(" ",
                nullToEmpty(detection.getTargetName()),
                nullToEmpty(detection.getCategoryName()),
                nullToEmpty(detection.getShape())
        ));

        List<String> terms = new ArrayList<>();
        if (containsAny(source, List.of("t-shirt", "shirt", "tee", "반팔", "티셔츠"))) {
            terms.addAll(List.of("t-shirt", "shirt", "tee", "반팔", "티셔츠", "반팔티"));
        }
        if (containsAny(source, List.of("sneaker", "shoe", "스니커즈", "신발"))) {
            terms.addAll(List.of("sneaker", "shoe", "스니커즈", "신발", "운동화"));
        }
        if (containsAny(source, List.of("earbud", "headphone", "이어폰", "헤드폰"))) {
            terms.addAll(List.of("earbud", "headphone", "이어폰", "헤드폰"));
        }
        return terms;
    }

    private List<String> colorTerms(String color) {
        String normalized = normalize(color);
        List<String> terms = new ArrayList<>();
        if (hasText(normalized)) {
            terms.add(normalized);
        }
        if (contains(normalized, "red")) {
            terms.addAll(List.of("빨간", "빨강", "레드", "red"));
        }
        if (contains(normalized, "orange")) {
            terms.addAll(List.of("주황", "오렌지", "orange"));
        }
        if (contains(normalized, "black")) {
            terms.addAll(List.of("검정", "블랙", "black"));
        }
        if (contains(normalized, "white")) {
            terms.addAll(List.of("흰색", "화이트", "white"));
        }
        return terms;
    }

    private boolean contains(String searchableText, String value) {
        return hasText(value) && searchableText.contains(normalize(value));
    }

    private boolean containsAny(String searchableText, List<String> values) {
        return values.stream().anyMatch(value -> contains(searchableText, value));
    }

    private String normalize(String value) {
        return value == null ? "" : value.toLowerCase(Locale.ROOT).replaceAll("\\s+", " ").trim();
    }

    private String nullToEmpty(String value) {
        return value == null ? "" : value;
    }

    private boolean hasText(String value) {
        return value != null && !value.isBlank();
    }

    private double clamp(double value) {
        return Math.max(0, Math.min(100, value));
    }

    private double round(double value) {
        return Math.round(value * 10.0) / 10.0;
    }
}
