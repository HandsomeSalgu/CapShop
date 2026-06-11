package com.syncshopper.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "Page response")
public class PageResponse<T> {

    private List<T> content;
    private int page;
    private int size;
    private long totalCount;
    private int totalPages;
    private boolean first;
    private boolean last;

    public static <T> PageResponse<T> of(List<T> content, int page, int size, long totalCount) {
        int totalPages = size <= 0 ? 0 : (int) Math.ceil((double) totalCount / size);

        return PageResponse.<T>builder()
                .content(content)
                .page(page)
                .size(size)
                .totalCount(totalCount)
                .totalPages(totalPages)
                .first(page <= 1)
                .last(totalPages == 0 || page >= totalPages)
                .build();
    }
}
