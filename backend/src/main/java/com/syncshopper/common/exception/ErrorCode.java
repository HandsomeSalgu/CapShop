package com.syncshopper.common.exception;

import org.springframework.http.HttpStatus;

public enum ErrorCode {

    INVALID_INPUT_VALUE(HttpStatus.BAD_REQUEST, "Invalid input value."),
    METHOD_NOT_ALLOWED(HttpStatus.METHOD_NOT_ALLOWED, "HTTP method is not allowed."),
    INTERNAL_SERVER_ERROR(HttpStatus.INTERNAL_SERVER_ERROR, "Internal server error."),

    UNAUTHORIZED(HttpStatus.UNAUTHORIZED, "Authentication is required."),
    FORBIDDEN(HttpStatus.FORBIDDEN, "Access is denied."),

    DUPLICATE_EMAIL(HttpStatus.CONFLICT, "Email is already in use."),
    INVALID_LOGIN(HttpStatus.UNAUTHORIZED, "Email or password is invalid."),
    INVALID_PASSWORD(HttpStatus.UNAUTHORIZED, "Password is invalid."),
    INACTIVE_USER(HttpStatus.FORBIDDEN, "User is not active."),
    OAUTH_EMAIL_CONFLICT(HttpStatus.CONFLICT, "Email is already registered with another login method."),
    TOKEN_INVALID(HttpStatus.UNAUTHORIZED, "Token is invalid."),
    TOKEN_EXPIRED(HttpStatus.UNAUTHORIZED, "Token is expired."),
    USER_NOT_FOUND(HttpStatus.NOT_FOUND, "User not found."),
    CURRENT_PASSWORD_NOT_MATCHED(HttpStatus.BAD_REQUEST, "Current password does not match."),
    PASSWORD_CONFIRM_NOT_MATCHED(HttpStatus.BAD_REQUEST, "New password and confirmation do not match."),
    OAUTH_USER_PASSWORD_CHANGE_NOT_ALLOWED(HttpStatus.BAD_REQUEST, "OAuth users cannot change password."),

    PRODUCT_NOT_FOUND(HttpStatus.NOT_FOUND, "Product not found."),
    INVALID_SORT_TYPE(HttpStatus.BAD_REQUEST, "Invalid sort type."),
    POST_NOT_FOUND(HttpStatus.NOT_FOUND, "Post not found."),
    DETECTION_NOT_FOUND(HttpStatus.NOT_FOUND, "Detection result not found."),
    AI_ANALYSIS_FAILED(HttpStatus.INTERNAL_SERVER_ERROR, "AI analysis failed."),

    INVALID_COMMERCE_QUERY(HttpStatus.BAD_REQUEST, "Search query is required."),
    NAVER_SHOPPING_API_FAILED(HttpStatus.BAD_GATEWAY, "Naver Shopping API request failed."),
    AI_SERVER_ERROR(HttpStatus.BAD_GATEWAY, "AI server request failed."),
    COMMERCE_API_ERROR(HttpStatus.BAD_GATEWAY, "Commerce API request failed.");

    private final HttpStatus status;
    private final String message;

    ErrorCode(HttpStatus status, String message) {
        this.status = status;
        this.message = message;
    }

    public HttpStatus getStatus() {
        return status;
    }

    public String getMessage() {
        return message;
    }
}
