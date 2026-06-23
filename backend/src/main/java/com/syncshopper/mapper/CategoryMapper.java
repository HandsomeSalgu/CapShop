package com.syncshopper.mapper;

import com.syncshopper.domain.product.Category;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
public interface CategoryMapper {

    List<Category> findVisibleCategories();
    Category findByName(String name);
}
