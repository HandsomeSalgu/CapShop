-- =========================================================
-- SyncShopper Database Schema
-- MySQL 8.x 기준
-- =========================================================

CREATE DATABASE IF NOT EXISTS syncshopper
DEFAULT CHARACTER SET utf8mb4
DEFAULT COLLATE utf8mb4_unicode_ci;

USE syncshopper;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS affiliate_clicks;
DROP TABLE IF EXISTS ai_analysis_logs;
DROP TABLE IF EXISTS user_events;
DROP TABLE IF EXISTS recommendations;
DROP TABLE IF EXISTS detections;
DROP TABLE IF EXISTS posts;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS user_preferences;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS wishlist;

SET FOREIGN_KEY_CHECKS = 1;

-- =========================================================
-- 1. users
-- 회원 / 관리자 계정
-- =========================================================

CREATE TABLE users (
    user_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NULL,

    provider VARCHAR(20) NOT NULL DEFAULT 'LOCAL',
    provider_id VARCHAR(100) NULL,

    nickname VARCHAR(50) NOT NULL,
    profile_image_url TEXT NULL,

    role VARCHAR(20) NOT NULL DEFAULT 'USER',
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    last_login_at DATETIME NULL,

    INDEX idx_users_email (email),
    INDEX idx_users_role (role),
    INDEX idx_users_status (status),

    UNIQUE INDEX uk_users_provider_provider_id (provider, provider_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =========================================================
-- 2. categories
-- 상품 / 관심사 카테고리
-- =========================================================

CREATE TABLE categories (
    category_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    parent_id BIGINT NULL,
    visible_yn CHAR(1) NOT NULL DEFAULT 'Y',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_categories_parent
        FOREIGN KEY (parent_id) REFERENCES categories(category_id)
        ON DELETE SET NULL,

    INDEX idx_categories_parent_id (parent_id),
    INDEX idx_categories_visible_yn (visible_yn)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =========================================================
-- 3. user_preferences
-- 사용자 관심 카테고리 / 브랜드 / 가격대
-- =========================================================

CREATE TABLE user_preferences (
    preference_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    category_id BIGINT NULL,
    category_name VARCHAR(50) NULL,
    brand VARCHAR(100) NULL,
    price_min INT NULL,
    price_max INT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_user_preferences_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_user_preferences_category
        FOREIGN KEY (category_id) REFERENCES categories(category_id)
        ON DELETE SET NULL,

    INDEX idx_user_preferences_user_id (user_id),
    INDEX idx_user_preferences_category_id (category_id),
    INDEX idx_user_preferences_category_name (category_name),
    INDEX idx_user_preferences_brand (brand)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =========================================================
-- 4. products
-- 상품 정보
-- =========================================================

CREATE TABLE products (
    product_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    brand VARCHAR(100) NULL,
    category_id BIGINT NULL,
    category_name VARCHAR(50) NULL,
    price INT NULL,
    image_url TEXT NULL,
    affiliate_url TEXT NULL,
    source VARCHAR(50) NULL,
    review_count INT NOT NULL DEFAULT 0,
    rating DECIMAL(2,1) NULL,
    visible_yn CHAR(1) NOT NULL DEFAULT 'Y',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_products_category
        FOREIGN KEY (category_id) REFERENCES categories(category_id)
        ON DELETE SET NULL,

    INDEX idx_products_category_id (category_id),
    INDEX idx_products_category_name (category_name),
    INDEX idx_products_brand (brand),
    INDEX idx_products_source (source),
    INDEX idx_products_visible_yn (visible_yn),
    INDEX idx_products_price (price)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =========================================================
-- 5. posts
-- 관리자 게시글 / 공지사항 / FAQ / 이벤트
-- =========================================================

CREATE TABLE posts (
    post_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    post_type VARCHAR(30) NOT NULL,
    visible_yn CHAR(1) NOT NULL DEFAULT 'Y',
    created_by BIGINT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_posts_created_by
        FOREIGN KEY (created_by) REFERENCES users(user_id)
        ON DELETE RESTRICT,

    INDEX idx_posts_created_by (created_by),
    INDEX idx_posts_post_type (post_type),
    INDEX idx_posts_visible_yn (visible_yn),
    INDEX idx_posts_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =========================================================
-- 6. detections
-- 유튜브 일시정지 후 AI 탐지 결과
-- =========================================================

CREATE TABLE detections (
    detection_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    video_id VARCHAR(100) NOT NULL,
    timestamp_sec INT NOT NULL,
    image_hash VARCHAR(255) NULL,
    subtitle_summary TEXT NULL,

    target_name VARCHAR(255) NULL,
    category_name VARCHAR(50) NULL,
    brand VARCHAR(100) NULL,
    model_name VARCHAR(100) NULL,
    confidence DECIMAL(5,4) NULL,

    status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_detections_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE,

    INDEX idx_detections_user_id (user_id),
    INDEX idx_detections_video_id (video_id),
    INDEX idx_detections_image_hash (image_hash),
    INDEX idx_detections_status (status),
    INDEX idx_detections_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =========================================================
-- 7. recommendations
-- 사용자에게 추천된 상품 기록
-- =========================================================

CREATE TABLE recommendations (
    recommendation_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    detection_id BIGINT NULL,

    rank_no INT NOT NULL,
    score DECIMAL(8,4) NULL,
    reason TEXT NULL,
    recommendation_type VARCHAR(30) NOT NULL DEFAULT 'GENERAL',

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_recommendations_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_recommendations_product
        FOREIGN KEY (product_id) REFERENCES products(product_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_recommendations_detection
        FOREIGN KEY (detection_id) REFERENCES detections(detection_id)
        ON DELETE SET NULL,

    INDEX idx_recommendations_user_id (user_id),
    INDEX idx_recommendations_product_id (product_id),
    INDEX idx_recommendations_detection_id (detection_id),
    INDEX idx_recommendations_type (recommendation_type),
    INDEX idx_recommendations_created_at (created_at),
    INDEX idx_recommendations_score (score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =========================================================
-- 8. user_events
-- 사용자 행동 로그
-- =========================================================

CREATE TABLE user_events (
    event_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    product_id BIGINT NULL,
    recommendation_id BIGINT NULL,

    event_type VARCHAR(30) NOT NULL,
    video_id VARCHAR(100) NULL,
    category_name VARCHAR(50) NULL,
    brand VARCHAR(100) NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_user_events_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_user_events_product
        FOREIGN KEY (product_id) REFERENCES products(product_id)
        ON DELETE SET NULL,

    CONSTRAINT fk_user_events_recommendation
        FOREIGN KEY (recommendation_id) REFERENCES recommendations(recommendation_id)
        ON DELETE SET NULL,

    INDEX idx_user_events_user_id (user_id),
    INDEX idx_user_events_product_id (product_id),
    INDEX idx_user_events_recommendation_id (recommendation_id),
    INDEX idx_user_events_event_type (event_type),
    INDEX idx_user_events_video_id (video_id),
    INDEX idx_user_events_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =========================================================
-- 9. ai_analysis_logs
-- FastAPI AI 서버 요청 / 응답 로그
-- =========================================================

CREATE TABLE ai_analysis_logs (
    log_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    detection_id BIGINT NULL,

    api_provider VARCHAR(50) NULL,
    request_payload JSON NULL,
    response_payload JSON NULL,

    success_yn CHAR(1) NOT NULL DEFAULT 'N',
    error_message TEXT NULL,
    latency_ms INT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_ai_logs_detection
        FOREIGN KEY (detection_id) REFERENCES detections(detection_id)
        ON DELETE SET NULL,

    INDEX idx_ai_logs_detection_id (detection_id),
    INDEX idx_ai_logs_api_provider (api_provider),
    INDEX idx_ai_logs_success_yn (success_yn),
    INDEX idx_ai_logs_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =========================================================
-- 10. affiliate_clicks
-- 구매하러 가기 버튼 클릭 로그
-- =========================================================

CREATE TABLE affiliate_clicks (
    click_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    recommendation_id BIGINT NULL,
    source VARCHAR(50) NULL,
    clicked_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_affiliate_clicks_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_affiliate_clicks_product
        FOREIGN KEY (product_id) REFERENCES products(product_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_affiliate_clicks_recommendation
        FOREIGN KEY (recommendation_id) REFERENCES recommendations(recommendation_id)
        ON DELETE SET NULL,

    INDEX idx_affiliate_clicks_user_id (user_id),
    INDEX idx_affiliate_clicks_product_id (product_id),
    INDEX idx_affiliate_clicks_recommendation_id (recommendation_id),
    INDEX idx_affiliate_clicks_source (source),
    INDEX idx_affiliate_clicks_clicked_at (clicked_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =========================================================
-- 11. products.description and wishlists 추가
-- 구매하러 가기 버튼 클릭 로그
-- =========================================================


ALTER TABLE products
ADD COLUMN description TEXT NULL AFTER affiliate_url;

CREATE TABLE wishlists (
    wishlist_id BIGINT AUTO_INCREMENT PRIMARY KEY,

    user_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uk_wishlists_user_product (user_id, product_id),

    INDEX idx_wishlists_user_id (user_id),
    INDEX idx_wishlists_product_id (product_id),

    CONSTRAINT fk_wishlists_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_wishlists_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



-- =========================================================
-- Initial Category Data
-- =========================================================

INSERT INTO categories (name, parent_id, visible_yn)
VALUES
('패션', NULL, 'Y'),
('뷰티', NULL, 'Y'),
('전자기기', NULL, 'Y'),
('가구/인테리어', NULL, 'Y'),
('스포츠/아웃도어', NULL, 'Y'),
('식품', NULL, 'Y'),
('취미/키덜트', NULL, 'Y'),
('자동차용품', NULL, 'Y');


INSERT INTO products
(product_id, title, brand, category_id, category_name, price, image_url, affiliate_url, description, source, review_count, rating, visible_yn, created_at, updated_at)
VALUES
(1, 'Nike Air Force 1', 'Nike', 1, '패션', 129000,
 'https://example.com/nike-air-force.jpg',
 'https://example.com/buy/nike-air-force',
 '클래식한 디자인의 Nike Air Force 1 스니커즈입니다.',
 'MOCK', 120, 4.8, 'Y', NOW(), NOW()),

(2, 'Adidas Samba OG', 'Adidas', 1, '패션', 139000,
 'https://example.com/adidas-samba.jpg',
 'https://example.com/buy/adidas-samba',
 '데일리 코디에 어울리는 Adidas Samba OG 스니커즈입니다.',
 'MOCK', 95, 4.6, 'Y', NOW(), NOW()),

(3, 'Apple AirPods Pro 2', 'Apple', 3, '전자기기', 329000,
 'https://example.com/airpods-pro.jpg',
 'https://example.com/buy/airpods-pro',
 '노이즈 캔슬링을 지원하는 Apple AirPods Pro 2입니다.',
 'MOCK', 310, 4.9, 'Y', NOW(), NOW()),

(4, 'Dyson Supersonic Hair Dryer', 'Dyson', 2, '뷰티', 499000,
 'https://example.com/dyson-hair-dryer.jpg',
 'https://example.com/buy/dyson-hair-dryer',
 '빠른 건조와 스타일링을 지원하는 Dyson 헤어드라이어입니다.',
 'MOCK', 180, 4.7, 'Y', NOW(), NOW()),

(5, 'Sony WH-1000XM5', 'Sony', 3, '전자기기', 459000,
 'https://example.com/sony-wh1000xm5.jpg',
 'https://example.com/buy/sony-wh1000xm5',
 '고성능 노이즈 캔슬링 무선 헤드폰입니다.',
 'MOCK', 260, 4.8, 'Y', NOW(), NOW()),

(6, 'New Balance 530', 'New Balance', 1, '패션', 119000,
 'https://example.com/new-balance-530.jpg',
 'https://example.com/buy/new-balance-530',
 '편안한 착화감의 New Balance 530 운동화입니다.',
 'MOCK', 140, 4.5, 'Y', NOW(), NOW());


-- =========================================================
-- 확인용 조회
-- =========================================================

SHOW TABLES;