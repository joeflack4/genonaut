-- Jinja2 template: uses {{ }} for passwords. Run via init.py
-- setup_genonaut.sql
-- Run connected to the 'postgres' database as a superuser.

-----------------------
-- 0) Safety helpers
-----------------------
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'genonaut_admin') THEN
    CREATE ROLE genonaut_admin LOGIN PASSWORD '{{ DB_PASSWORD_ADMIN }}' SUPERUSER CREATEDB CREATEROLE REPLICATION BYPASSRLS;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'genonaut_rw') THEN
    CREATE ROLE genonaut_rw LOGIN PASSWORD '{{ DB_PASSWORD_RW }}' NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'genonaut_ro') THEN
    CREATE ROLE genonaut_ro LOGIN PASSWORD '{{ DB_PASSWORD_RO }}' NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
  END IF;
END$$;

-----------------------
-- 1) Database
-----------------------
-- Drop/create optional (uncomment drop if you really want a fresh DB)
-- DROP DATABASE IF EXISTS {{ DB_NAME }};

-- Create database (will fail if exists, that's ok)
CREATE DATABASE {{ DB_NAME }} OWNER genonaut_admin;

-----------------------
-- 2) Wire up privileges in the DB
-----------------------
\connect {{ DB_NAME }}

-- Tighten DB entry points
REVOKE CONNECT ON DATABASE {{ DB_NAME }} FROM PUBLIC;
GRANT  CONNECT ON DATABASE {{ DB_NAME }} TO genonaut_ro, genonaut_rw, genonaut_admin;

-- Public schema lockdown
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
ALTER SCHEMA public OWNER TO genonaut_admin;
GRANT USAGE ON SCHEMA public TO genonaut_ro, genonaut_rw;

-- Existing objects in public (if any)
GRANT SELECT ON ALL TABLES    IN SCHEMA public TO genonaut_ro;
GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA public TO genonaut_rw;
GRANT USAGE ON ALL SEQUENCES  IN SCHEMA public TO genonaut_ro, genonaut_rw;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO genonaut_ro, genonaut_rw;

-- Default privileges for FUTURE objects created by genonaut_admin in public
ALTER DEFAULT PRIVILEGES FOR ROLE genonaut_admin IN SCHEMA public
  GRANT SELECT ON TABLES TO genonaut_ro;
ALTER DEFAULT PRIVILEGES FOR ROLE genonaut_admin IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO genonaut_rw;
ALTER DEFAULT PRIVILEGES FOR ROLE genonaut_admin IN SCHEMA public
  GRANT USAGE ON SEQUENCES TO genonaut_ro, genonaut_rw;
ALTER DEFAULT PRIVILEGES FOR ROLE genonaut_admin IN SCHEMA public
  GRANT EXECUTE ON FUNCTIONS TO genonaut_ro, genonaut_rw;

-- Ensure rw cannot do DDL in public
REVOKE CREATE ON SCHEMA public FROM genonaut_rw;

-----------------------
-- 3) Auto-apply to any NEW schema in this DB
-----------------------
CREATE OR REPLACE FUNCTION genonaut_apply_privs()
RETURNS event_trigger
LANGUAGE plpgsql AS $$
DECLARE r record; sch text;
BEGIN
  FOR r IN SELECT * FROM pg_event_trigger_ddl_commands() LOOP
    IF r.command_tag = 'CREATE SCHEMA' THEN
      sch := r.object_identity; -- schema name (possibly quoted)

      EXECUTE format('REVOKE CREATE ON SCHEMA %s FROM PUBLIC;', sch);
      EXECUTE format('GRANT  USAGE ON SCHEMA %s TO genonaut_ro, genonaut_rw;', sch);

      -- Future objects created by genonaut_admin in that schema
      EXECUTE format(
        'ALTER DEFAULT PRIVILEGES FOR ROLE genonaut_admin IN SCHEMA %s
           GRANT SELECT ON TABLES TO genonaut_ro;', sch);
      EXECUTE format(
        'ALTER DEFAULT PRIVILEGES FOR ROLE genonaut_admin IN SCHEMA %s
           GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO genonaut_rw;', sch);
      EXECUTE format(
        'ALTER DEFAULT PRIVILEGES FOR ROLE genonaut_admin IN SCHEMA %s
           GRANT USAGE ON SEQUENCES TO genonaut_ro, genonaut_rw;', sch);
      EXECUTE format(
        'ALTER DEFAULT PRIVILEGES FOR ROLE genonaut_admin IN SCHEMA %s
           GRANT EXECUTE ON FUNCTIONS TO genonaut_ro, genonaut_rw;', sch);
    END IF;
  END LOOP;
END $$;

DROP EVENT TRIGGER IF EXISTS genonaut_on_create_schema;
CREATE EVENT TRIGGER genonaut_on_create_schema
  ON ddl_command_end
  WHEN TAG IN ('CREATE SCHEMA')
  EXECUTE PROCEDURE genonaut_apply_privs();
