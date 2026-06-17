package com.syncshopper.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.syncshopper.common.exception.ErrorCode;
import com.syncshopper.common.response.ApiResponse;
import com.syncshopper.security.JwtAuthenticationFilter;
import com.syncshopper.security.OAuth2FailureHandler;
import com.syncshopper.security.OAuth2SuccessHandler;
import com.syncshopper.service.CustomOAuth2UserService;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

        private final JwtAuthenticationFilter jwtAuthenticationFilter;
        private final CustomOAuth2UserService customOAuth2UserService;
        private final OAuth2SuccessHandler oauth2SuccessHandler;
        private final OAuth2FailureHandler oauth2FailureHandler;
        private final ObjectMapper objectMapper = new ObjectMapper();

        public SecurityConfig(
                        JwtAuthenticationFilter jwtAuthenticationFilter,
                        CustomOAuth2UserService customOAuth2UserService,
                        OAuth2SuccessHandler oauth2SuccessHandler,
                        OAuth2FailureHandler oauth2FailureHandler) {
                this.jwtAuthenticationFilter = jwtAuthenticationFilter;
                this.customOAuth2UserService = customOAuth2UserService;
                this.oauth2SuccessHandler = oauth2SuccessHandler;
                this.oauth2FailureHandler = oauth2FailureHandler;
        }

        @Bean
        public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
                http
                                .csrf(csrf -> csrf.disable())
                                .cors(cors -> {
                                })
                                .sessionManagement(session -> session
                                                .sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                                .formLogin(form -> form.disable())
                                .httpBasic(httpBasic -> httpBasic.disable())
                                .exceptionHandling(exception -> exception
                                                .authenticationEntryPoint(
                                                                (request, response, authException) -> writeError(
                                                                                response, ErrorCode.UNAUTHORIZED))
                                                .accessDeniedHandler((request, response,
                                                                accessDeniedException) -> writeError(response,
                                                                                ErrorCode.FORBIDDEN)))
                                .authorizeHttpRequests(auth -> auth
                                                .requestMatchers(HttpMethod.GET, "/api/products/**").permitAll()
                                                .requestMatchers(HttpMethod.GET, "/api/categories/**").permitAll()
                                                .requestMatchers(HttpMethod.GET, "/api/posts/**").permitAll()
                                                .requestMatchers(HttpMethod.GET, "/api/commerce/**").permitAll()
                                                .requestMatchers(
                                                                "/api/auth/signup",
                                                                "/api/auth/login",
                                                                "/api/auth/logout",
                                                                "/api/auth/check-email",
                                                                "/api/health",
                                                                "/api/health/db",
                                                                "/swagger-ui/**",
                                                                "/v3/api-docs/**",
                                                                "/swagger-ui.html",
                                                                "/oauth2/**",
                                                                "/login/oauth2/**")
                                                .permitAll()
                                                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                                                .requestMatchers(
                                                                "/api/auth/me",
                                                                "/api/users/me/**",
                                                                "/api/recommendations/**",
                                                                "/api/detections/**")
                                                .authenticated()
                                                .requestMatchers("/api/**").authenticated()
                                                .anyRequest().permitAll())
                                .oauth2Login(oauth2 -> oauth2
                                                .userInfoEndpoint(userInfo -> userInfo
                                                                .userService(customOAuth2UserService))
                                                .successHandler(oauth2SuccessHandler)
                                                .failureHandler(oauth2FailureHandler))
                                .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);

                return http.build();
        }

        @Bean
        public PasswordEncoder passwordEncoder() {
                return new BCryptPasswordEncoder();
        }

        private void writeError(HttpServletResponse response, ErrorCode errorCode) throws java.io.IOException {
                response.setStatus(errorCode.getStatus().value());
                response.setContentType(MediaType.APPLICATION_JSON_VALUE);
                response.setCharacterEncoding("UTF-8");
                objectMapper.writeValue(response.getWriter(), ApiResponse.fail(errorCode.getMessage()));
        }
}
