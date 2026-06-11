package com.syncshopper.service;

import com.syncshopper.dto.response.CategoryResponse;
import com.syncshopper.mapper.CategoryMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@RequiredArgsConstructor
@Service
public class CategoryService {

    private final CategoryMapper categoryMapper;

    public List<CategoryResponse> getCategories() {
        return categoryMapper.findVisibleCategories().stream()
                .map(CategoryResponse::from)
                .toList();
    }
}
