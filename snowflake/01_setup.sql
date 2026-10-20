-- Compute: extra-small, auto-suspend fast so the trial credits last.
CREATE WAREHOUSE IF NOT EXISTS GOLD_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND   = 60
  AUTO_RESUME    = TRUE
  INITIALLY_SUSPENDED = TRUE;

-- 1. Create the Database and Schema
CREATE DATABASE IF NOT EXISTS GOLD_DB;



USE DATABASE _GOLD;
