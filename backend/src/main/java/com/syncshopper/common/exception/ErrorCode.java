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

    PRODUCT_NOT_FOUND(HttpStatus.NOT_FOUND, "Product not found."),
    POST_NOT_FOUND(HttpStatus.NOT_FOUND, "Post not found."),

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
