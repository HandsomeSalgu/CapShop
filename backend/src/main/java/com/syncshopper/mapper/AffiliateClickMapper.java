package com.syncshopper.mapper;

import com.syncshopper.domain.user.AffiliateClick;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface AffiliateClickMapper {

    int insertAffiliateClick(AffiliateClick affiliateClick);
}
