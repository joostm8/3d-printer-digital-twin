-- Runs on first container initialization (empty PGDATA only).
-- POSTGRES_DB already creates octoPrint; add moonraker as an extra DB.
SELECT 'CREATE DATABASE "moonraker"'
WHERE NOT EXISTS (
  SELECT FROM pg_database WHERE datname = 'moonraker'
)\gexec
