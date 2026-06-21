ALTER TABLE products
ADD COLUMN description TEXT NULL AFTER affiliate_url;

ALTER TABLE products
ADD COLUMN mall_name VARCHAR(100) NULL AFTER affiliate_url,
ADD COLUMN external_product_id VARCHAR(100) NULL AFTER source;

CREATE INDEX idx_products_external_product_id ON products (external_product_id);
