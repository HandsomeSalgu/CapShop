ALTER TABLE users
MODIFY password VARCHAR(255) NULL;

ALTER TABLE users
ADD COLUMN provider VARCHAR(20) NOT NULL DEFAULT 'LOCAL' AFTER password;

ALTER TABLE users
ADD COLUMN provider_id VARCHAR(100) NULL AFTER provider;

ALTER TABLE users
ADD COLUMN profile_image_url TEXT NULL AFTER nickname;

CREATE UNIQUE INDEX uk_users_provider_provider_id
ON users(provider, provider_id);
