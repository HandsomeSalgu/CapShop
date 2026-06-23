package com.syncshopper.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.syncshopper.domain.detection.Detection;
import com.syncshopper.dto.response.SearchQueryBundleResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

@RequiredArgsConstructor
@Component
public class SearchQueryGenerator {

    private static final int TYPE_LIMIT = 3;

    private final ObjectMapper objectMapper;

    public SearchQueryBundleResponse generate(Detection detection) {
        QueryContext context = QueryContext.from(detection, keyFeatures(detection));

        List<String> primary = limit(Arrays.asList(
                join(context.brand(), context.modelName()),
                join(context.brand(), context.targetName()),
                join(context.logoText(), context.productKo()),
                context.targetName()
        ));

        List<String> shopping = limit(Arrays.asList(
                join(context.logoText(), context.productKo()),
                join(context.colorKo(), context.styleKo(), context.productKo()),
                join(context.colorKo(), context.letteringKo(), context.productKo()),
                join(context.secondaryColorKo(), "그래픽", context.productKo())
        ));

        List<String> image = limit(Arrays.asList(
                join(context.logoText(), context.englishTarget()),
                join(context.englishTarget(), context.englishFeature()),
                join(context.colorKo(), context.styleKo(), context.productKo()),
                join(context.logoText(), context.productKo())
        ));

        List<String> blog = limit(Arrays.asList(
                quotedJoin(context.logoText(), context.productKo()),
                quotedJoin(context.logoText(), "티셔츠"),
                join(context.colorKo(), context.styleKo(), context.productKo())
        ));

        List<String> cafe = limit(Arrays.asList(
                quotedJoin(context.logoText(), context.productKo()),
                quotedJoin(context.logoText(), "티셔츠"),
                join(context.colorKo(), context.styleKo(), context.productKo())
        ));

        List<String> web = limit(Arrays.asList(
                quotedJoin(context.logoText(), context.englishProduct()),
                quotedJoin(context.logoText(), context.productKo()),
                quotedJoin(context.logoText(), "티셔츠"),
                join(context.colorKo(), context.styleKo(), context.productKo())
        ));

        List<String> fallback = limit(Arrays.asList(
                join(context.colorKo(), "영문", context.letteringKo(), context.productKo()),
                join(context.secondaryColorKo(), "그래픽", context.productKo()),
                context.englishFallback(),
                context.targetName()
        ));

        return SearchQueryBundleResponse.builder()
                .primaryQueries(primary)
                .shoppingQueries(shopping)
                .imageQueries(image)
                .blogQueries(blog)
                .cafeQueries(cafe)
                .webQueries(web)
                .fallbackQueries(fallback)
                .build();
    }

    private List<String> keyFeatures(Detection detection) {
        if (detection == null || detection.getKeyFeaturesJson() == null || detection.getKeyFeaturesJson().isBlank()) {
            return List.of();
        }

        try {
            return objectMapper.readerForListOf(String.class).readValue(detection.getKeyFeaturesJson());
        } catch (Exception e) {
            return List.of();
        }
    }

    private static List<String> limit(List<String> queries) {
        Set<String> distinct = new LinkedHashSet<>();
        for (String query : queries) {
            String normalized = normalizeQuery(query);
            if (normalized != null) {
                distinct.add(normalized);
            }
            if (distinct.size() >= TYPE_LIMIT) {
                break;
            }
        }
        return new ArrayList<>(distinct);
    }

    private static String join(String... parts) {
        StringBuilder builder = new StringBuilder();
        for (String part : parts) {
            if (part == null || part.isBlank()) {
                continue;
            }
            if (!builder.isEmpty()) {
                builder.append(' ');
            }
            builder.append(part.trim());
        }
        return normalizeQuery(builder.toString());
    }

    private static String quotedJoin(String... parts) {
        List<String> values = new ArrayList<>();
        for (String part : parts) {
            if (part != null && !part.isBlank()) {
                values.add("\"" + part.trim() + "\"");
            }
        }
        return normalizeQuery(String.join(" ", values));
    }

    private static String normalizeQuery(String query) {
        if (query == null) {
            return null;
        }

        String normalized = query.replaceAll("\\s+", " ").trim();
        if (normalized.isBlank() || normalized.length() < 2) {
            return null;
        }
        return normalized;
    }

    private record QueryContext(
            String targetName,
            String categoryName,
            String brand,
            String modelName,
            String color,
            String colorKo,
            String secondaryColorKo,
            String shape,
            String logoText,
            String productKo,
            String styleKo,
            String letteringKo,
            String englishTarget,
            String englishProduct,
            String englishFeature,
            String englishFallback
    ) {

        static QueryContext from(Detection detection, List<String> keyFeatures) {
            String targetName = clean(detection == null ? null : detection.getTargetName());
            String categoryName = clean(detection == null ? null : detection.getCategoryName());
            String brand = clean(detection == null ? null : detection.getBrand());
            String modelName = clean(detection == null ? null : detection.getModelName());
            String color = clean(detection == null ? null : detection.getColor());
            String shape = clean(detection == null ? null : detection.getShape());
            String logoText = clean(detection == null ? null : detection.getLogoText());
            String haystack = String.join(" ", List.of(
                    nullToEmpty(targetName),
                    nullToEmpty(categoryName),
                    nullToEmpty(color),
                    nullToEmpty(shape),
                    String.join(" ", keyFeatures)
            )).toLowerCase(Locale.ROOT);

            String productKo = resolveProductKo(haystack);
            String styleKo = resolveStyleKo(haystack);
            String colorKo = resolveColorKo(haystack, color);
            String secondaryColorKo = resolveSecondaryColorKo(haystack, colorKo);
            String letteringKo = haystack.contains("letter") || haystack.contains("text") || hasText(logoText)
                    ? "레터링"
                    : null;
            String englishTarget = hasText(targetName) ? targetName : joinEnglish(brand, modelName, shape);
            String englishProduct = resolveEnglishProduct(haystack, targetName);
            String englishFeature = resolveEnglishFeature(haystack);
            String englishFallback = resolveEnglishFallback(haystack, color);

            return new QueryContext(
                    targetName,
                    categoryName,
                    brand,
                    modelName,
                    color,
                    colorKo,
                    secondaryColorKo,
                    shape,
                    logoText,
                    productKo,
                    styleKo,
                    letteringKo,
                    englishTarget,
                    englishProduct,
                    englishFeature,
                    englishFallback
            );
        }

        private static String resolveProductKo(String haystack) {
            if (containsAny(haystack, "t-shirt", "tee", "short-sleeve", "short sleeve", "shirt")) {
                return "반팔티";
            }
            if (containsAny(haystack, "sneaker", "shoe", "shoes")) {
                return "스니커즈";
            }
            if (containsAny(haystack, "earbud", "headphone", "airpods")) {
                return "이어폰";
            }
            if (containsAny(haystack, "bag", "backpack", "tote")) {
                return "가방";
            }
            return null;
        }

        private static String resolveStyleKo(String haystack) {
            if (containsAny(haystack, "graphic", "print", "printed")) {
                return "그래픽";
            }
            if (containsAny(haystack, "letter", "text", "logo")) {
                return "레터링";
            }
            if (containsAny(haystack, "crewneck", "crew neck")) {
                return "크루넥";
            }
            return null;
        }

        private static String resolveColorKo(String haystack, String color) {
            String source = (nullToEmpty(color) + " " + haystack).toLowerCase(Locale.ROOT);
            if (containsAny(source, "red", "crimson")) {
                return "빨간색";
            }
            if (containsAny(source, "orange")) {
                return "주황색";
            }
            if (containsAny(source, "black")) {
                return "검정색";
            }
            if (containsAny(source, "white")) {
                return "흰색";
            }
            if (containsAny(source, "blue")) {
                return "파란색";
            }
            if (containsAny(source, "green")) {
                return "초록색";
            }
            if (containsAny(source, "yellow")) {
                return "노란색";
            }
            return null;
        }

        private static String resolveSecondaryColorKo(String haystack, String primaryColorKo) {
            if (!"주황색".equals(primaryColorKo) && haystack.contains("orange")) {
                return "주황색";
            }
            if (!"빨간색".equals(primaryColorKo) && haystack.contains("red")) {
                return "빨간색";
            }
            return null;
        }

        private static String resolveEnglishProduct(String haystack, String targetName) {
            if (containsAny(haystack, "t-shirt", "tee", "short-sleeve", "short sleeve")) {
                return "t-shirt";
            }
            if (containsAny(haystack, "sneaker", "shoe")) {
                return "sneakers";
            }
            return hasText(targetName) ? targetName : "product";
        }

        private static String resolveEnglishFeature(String haystack) {
            if (haystack.contains("black") && containsAny(haystack, "letter", "text")) {
                return "black lettering";
            }
            if (containsAny(haystack, "graphic", "print")) {
                return "graphic";
            }
            return null;
        }

        private static String resolveEnglishFallback(String haystack, String color) {
            if (containsAny(haystack, "t-shirt", "tee", "short-sleeve", "short sleeve")) {
                if (haystack.contains("red") && haystack.contains("orange")) {
                    return "red orange graphic tee";
                }
                if (hasText(color)) {
                    return color + " graphic tee";
                }
                return "graphic tee";
            }
            return null;
        }

        private static boolean containsAny(String value, String... needles) {
            for (String needle : needles) {
                if (value != null && value.contains(needle)) {
                    return true;
                }
            }
            return false;
        }

        private static String joinEnglish(String... parts) {
            return SearchQueryGenerator.join(parts);
        }

        private static String clean(String value) {
            if (value == null) {
                return null;
            }
            String cleaned = value.replaceAll("\\s+", " ").trim();
            return cleaned.isBlank() ? null : cleaned;
        }

        private static String nullToEmpty(String value) {
            return value == null ? "" : value;
        }

        private static boolean hasText(String value) {
            return value != null && !value.isBlank();
        }
    }
}
