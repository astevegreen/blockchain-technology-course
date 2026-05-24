#!/usr/bin/env bash
set -euo pipefail

(
# Wait until ready
for i in {1..60}; do
  if mysqladmin ping --silent; then break; fi
  sleep 1
done

# Initialize DB + user if needed
mysql -uroot <<SQL
CREATE DATABASE IF NOT EXISTS \`${DB_NAME:-mempool}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${DB_USER:-mempool}'@'localhost' IDENTIFIED BY '${DB_PASS:-mempool}';
GRANT ALL PRIVILEGES ON \`${DB_NAME:-mempool}\`.* TO '${DB_USER:-mempool}'@'localhost';
FLUSH PRIVILEGES;
SQL
) &

exec mysqld_safe

# Replace the shell with mysqld_safe in foreground so supervisord tracks it
