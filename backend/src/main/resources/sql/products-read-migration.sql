SET @schema_name = DATABASE();

SET @sql = IF(
    (SELECT COUNT(*)
     FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = @schema_name
       AND TABLE_NAME = 'products'
       AND COLUMN_NAME = 'description') = 0,
    'ALTER TABLE products ADD COLUMN description TEXT NULL AFTER affiliate_url',
    'SELECT ''products.description already exists'' AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(
    (SELECT COUNT(*)
     FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = @schema_name
       AND TABLE_NAME = 'products'
       AND COLUMN_NAME = 'mall_name') = 0,
    'ALTER TABLE products ADD COLUMN mall_name VARCHAR(100) NULL AFTER affiliate_url',
    'SELECT ''products.mall_name already exists'' AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(
    (SELECT COUNT(*)
     FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = @schema_name
       AND TABLE_NAME = 'products'
       AND COLUMN_NAME = 'external_product_id') = 0,
    'ALTER TABLE products ADD COLUMN external_product_id VARCHAR(100) NULL AFTER source',
    'SELECT ''products.external_product_id already exists'' AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(
    (SELECT COUNT(*)
     FROM INFORMATION_SCHEMA.STATISTICS
     WHERE TABLE_SCHEMA = @schema_name
       AND TABLE_NAME = 'products'
       AND INDEX_NAME = 'idx_products_external_product_id') = 0,
    'CREATE INDEX idx_products_external_product_id ON products (external_product_id)',
    'SELECT ''idx_products_external_product_id already exists'' AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
