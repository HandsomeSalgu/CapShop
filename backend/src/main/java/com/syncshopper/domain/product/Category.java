package com.syncshopper.domain.product;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Category {

    private Long categoryId;
    private String name;
    private Long parentId;
    private String visibleYn;
    private LocalDateTime createdAt;
}
