ALTER TABLE users
ADD COLUMN phone VARCHAR(20) NULL AFTER profile_image_url;

ALTER TABLE users
ADD COLUMN birth_date DATE NULL AFTER phone;
