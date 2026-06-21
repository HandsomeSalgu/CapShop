package com.syncshopper.dto.request;

import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class FindEmailRequest {
    
    @NotBlank(message = "이름을 입력해주세요.")
    private String nickname;
    
    @NotBlank(message = "전화번호를 입력해주세요.")
    private String phone;
}
