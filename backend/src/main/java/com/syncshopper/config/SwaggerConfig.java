package com.syncshopper.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class SwaggerConfig {

    @Bean
    public OpenAPI syncShopperOpenAPI() {
        return new OpenAPI()
                .info(new Info()
                        .title("SyncShopper API")
                        .description("SyncShopper 백엔드 API 문서")
                        .version("v1.0.0")
                        .contact(new Contact()
                                .name("SyncShopper Team")));
    }
}
