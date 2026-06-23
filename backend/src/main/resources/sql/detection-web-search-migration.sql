SET @schema_name = DATABASE();

SET @sql = IF(
    (SELECT COUNT(*)
     FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = @schema_name
       AND TABLE_NAME = 'detections'
       AND COLUMN_NAME = 'color') = 0,
    'ALTER TABLE detections ADD COLUMN color VARCHAR(100) NULL AFTER model_name',
    'SELECT ''detections.color already exists'' AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(
    (SELECT COUNT(*)
     FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = @schema_name
       AND TABLE_NAME = 'detections'
       AND COLUMN_NAME = 'shape') = 0,
    'ALTER TABLE detections ADD COLUMN shape VARCHAR(255) NULL AFTER color',
    'SELECT ''detections.shape already exists'' AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(
    (SELECT COUNT(*)
     FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = @schema_name
       AND TABLE_NAME = 'detections'
       AND COLUMN_NAME = 'logo_text') = 0,
    'ALTER TABLE detections ADD COLUMN logo_text VARCHAR(255) NULL AFTER shape',
    'SELECT ''detections.logo_text already exists'' AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(
    (SELECT COUNT(*)
     FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = @schema_name
       AND TABLE_NAME = 'detections'
       AND COLUMN_NAME = 'key_features_json') = 0,
    'ALTER TABLE detections ADD COLUMN key_features_json JSON NULL AFTER logo_text',
    'SELECT ''detections.key_features_json already exists'' AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

CREATE TABLE IF NOT EXISTS search_queries (
    query_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    job_id BIGINT NOT NULL,
    query_text VARCHAR(255) NOT NULL,
    query_type VARCHAR(30) NOT NULL,
    source_target VARCHAR(50) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_search_queries_detection
        FOREIGN KEY (job_id) REFERENCES detections(detection_id)
        ON DELETE CASCADE,

    INDEX idx_search_queries_job_id (job_id),
    INDEX idx_search_queries_type (query_type),
    INDEX idx_search_queries_source_target (source_target),
    INDEX idx_search_queries_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS search_results (
    result_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    job_id BIGINT NOT NULL,
    query_id BIGINT NULL,
    source VARCHAR(50) NOT NULL,
    title VARCHAR(500) NULL,
    url TEXT NULL,
    image_url TEXT NULL,
    snippet TEXT NULL,
    price VARCHAR(50) NULL,
    mall_name VARCHAR(100) NULL,
    raw_json JSON NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_search_results_detection
        FOREIGN KEY (job_id) REFERENCES detections(detection_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_search_results_query
        FOREIGN KEY (query_id) REFERENCES search_queries(query_id)
        ON DELETE SET NULL,

    INDEX idx_search_results_job_id (job_id),
    INDEX idx_search_results_query_id (query_id),
    INDEX idx_search_results_source (source),
    INDEX idx_search_results_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS product_candidates (
    candidate_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    job_id BIGINT NOT NULL,
    result_id BIGINT NULL,
    product_name VARCHAR(500) NULL,
    brand VARCHAR(100) NULL,
    category VARCHAR(100) NULL,
    image_url TEXT NULL,
    product_url TEXT NULL,
    price VARCHAR(50) NULL,
    visual_score DECIMAL(6,2) NULL,
    text_score DECIMAL(6,2) NULL,
    final_score DECIMAL(6,2) NULL,
    reason TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_product_candidates_detection
        FOREIGN KEY (job_id) REFERENCES detections(detection_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_product_candidates_result
        FOREIGN KEY (result_id) REFERENCES search_results(result_id)
        ON DELETE SET NULL,

    INDEX idx_product_candidates_job_id (job_id),
    INDEX idx_product_candidates_result_id (result_id),
    INDEX idx_product_candidates_final_score (final_score),
    INDEX idx_product_candidates_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
