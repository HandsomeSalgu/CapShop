package com.syncshopper.service;

import com.syncshopper.domain.search.SearchSource;
import com.syncshopper.dto.search.NaverSearchApiResponse;
import com.syncshopper.dto.search.SearchResultItem;
import org.springframework.stereotype.Component;
import org.springframework.web.util.HtmlUtils;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Component
public class SearchResultNormalizer {

    public List<SearchResultItem> normalize(NaverSearchApiResponse response, String queryType) {
        if (response == null || !response.isSuccess() || response.getItems() == null) {
            return List.of();
        }

        return response.getItems().stream()
                .map(item -> normalizeItem(response.getSource(), queryType, response.getQueryText(), item))
                .filter(item -> item.getTitle() != null && !item.getTitle().isBlank())
                .toList();
    }

    private SearchResultItem normalizeItem(
            SearchSource source,
            String queryType,
            String queryText,
            Map<String, Object> raw
    ) {
        return switch (source) {
            case NAVER_SHOPPING -> normalizeShopping(queryType, queryText, raw);
            case NAVER_IMAGE -> normalizeImage(queryType, queryText, raw);
            case NAVER_BLOG -> normalizeTextSource(source, queryType, queryText, raw);
            case NAVER_CAFE -> normalizeTextSource(source, queryType, queryText, raw);
            case NAVER_WEB -> normalizeTextSource(source, queryType, queryText, raw);
        };
    }

    private SearchResultItem normalizeShopping(String queryType, String queryText, Map<String, Object> raw) {
        return SearchResultItem.builder()
                .source(SearchSource.NAVER_SHOPPING)
                .queryType(queryType)
                .queryText(queryText)
                .title(clean(value(raw, "title")))
                .link(value(raw, "link"))
                .imageUrl(value(raw, "image"))
                .thumbnailUrl(value(raw, "image"))
                .snippet(clean(value(raw, "description")))
                .price(value(raw, "lprice"))
                .mallName(clean(value(raw, "mallName")))
                .brand(clean(firstNonBlank(value(raw, "brand"), value(raw, "maker"))))
                .category(resolveCategory(raw))
                .searchedAt(LocalDateTime.now())
                .raw(raw)
                .build();
    }

    private SearchResultItem normalizeImage(String queryType, String queryText, Map<String, Object> raw) {
        return SearchResultItem.builder()
                .source(SearchSource.NAVER_IMAGE)
                .queryType(queryType)
                .queryText(queryText)
                .title(clean(value(raw, "title")))
                .link(value(raw, "link"))
                .imageUrl(value(raw, "link"))
                .thumbnailUrl(value(raw, "thumbnail"))
                .snippet(clean(value(raw, "description")))
                .searchedAt(LocalDateTime.now())
                .raw(raw)
                .build();
    }

    private SearchResultItem normalizeTextSource(
            SearchSource source,
            String queryType,
            String queryText,
            Map<String, Object> raw
    ) {
        return SearchResultItem.builder()
                .source(source)
                .queryType(queryType)
                .queryText(queryText)
                .title(clean(value(raw, "title")))
                .link(value(raw, "link"))
                .snippet(clean(value(raw, "description")))
                .mallName(clean(firstNonBlank(value(raw, "bloggername"), value(raw, "cafename"))))
                .searchedAt(LocalDateTime.now())
                .raw(raw)
                .build();
    }

    private String resolveCategory(Map<String, Object> raw) {
        String category4 = clean(value(raw, "category4"));
        if (hasText(category4)) {
            return category4;
        }

        String category3 = clean(value(raw, "category3"));
        if (hasText(category3)) {
            return category3;
        }

        String category2 = clean(value(raw, "category2"));
        if (hasText(category2)) {
            return category2;
        }

        return clean(value(raw, "category1"));
    }

    private String value(Map<String, Object> raw, String key) {
        Object value = raw == null ? null : raw.get(key);
        return value == null ? null : String.valueOf(value);
    }

    private String clean(String value) {
        if (value == null) {
            return null;
        }

        String withoutTags = value.replaceAll("<[^>]*>", "");
        String decoded = HtmlUtils.htmlUnescape(withoutTags);
        return decoded.replaceAll("\\s+", " ").trim();
    }

    private String firstNonBlank(String first, String second) {
        return hasText(first) ? first : second;
    }

    private boolean hasText(String value) {
        return value != null && !value.isBlank();
    }
}
