-- Learnzo MySQL setup
-- Run as MySQL root (or admin): mysql -u root -p < scripts/init_mysql.sql

-- Database
CREATE DATABASE IF NOT EXISTS learnzo
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE learnzo;

-- User matching app/config.py defaults (when no env vars set)
-- User: learnzo_user, Password: learnzo_pass
CREATE USER IF NOT EXISTS 'learnzo_user'@'localhost' IDENTIFIED BY 'learnzo_pass';
GRANT ALL PRIVILEGES ON learnzo.* TO 'learnzo_user'@'localhost';
FLUSH PRIVILEGES;

-- Optional: user matching root config.py (user / aryaanilkumar)
-- Uncomment if you want to use config.py credentials instead of env/app config:
-- CREATE USER IF NOT EXISTS 'user'@'localhost' IDENTIFIED BY 'aryaanilkumar';
-- GRANT ALL PRIVILEGES ON learnzo.* TO 'user'@'localhost';
-- FLUSH PRIVILEGES;

-- Tables are created by the FastAPI app on startup (SQLAlchemy Base.metadata.create_all).
-- No need to create tables here unless you prefer to manage schema manually.
