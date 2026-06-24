package com.syncshopper.service;

import com.syncshopper.dto.response.PageResponse;
import com.syncshopper.dto.response.ViewHistoryResponse;
import com.syncshopper.mapper.UserEventMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@RequiredArgsConstructor
@Service
public class ViewHistoryService {

    private static final int DEFAULT_PAGE = 1;
    private static final int DEFAULT_SIZE = 12;
    private static final int MAX_SIZE = 50;

    private final UserEventMapper userEventMapper;

    public PageResponse<ViewHistoryResponse> getMyViewHistory(Long userId, String keyword, String category, int page, int size) {
        PageRequest pageRequest = normalizePage(page, size);

        long totalCount = userEventMapper.countViewHistory(userId, keyword, category);
        List<ViewHistoryResponse> products = userEventMapper.findViewHistory(
                userId,
                keyword,
                category,
                pageRequest.offset(),
                pageRequest.size()
        );

        return PageResponse.of(products, pageRequest.page(), pageRequest.size(), totalCount);
    }

    private PageRequest normalizePage(int page, int size) {
        int normalizedPage = page < 1 ? DEFAULT_PAGE : page;
        int normalizedSize = size < 1 ? DEFAULT_SIZE : Math.min(size, MAX_SIZE);
        return new PageRequest(normalizedPage, normalizedSize, (normalizedPage - 1) * normalizedSize);
    }

    private record PageRequest(int page, int size, int offset) {
    }
}
