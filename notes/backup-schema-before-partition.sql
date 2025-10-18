--
-- PostgreSQL database dump
--

\restrict 1nK1JCLzOqy4Ofdef0NeCQl95nYdh96LmfpY4UVfolTWVPWrxqJhm7Z4TZu67OB

-- Dumped from database version 16.10 (Postgres.app)
-- Dumped by pg_dump version 16.10 (Postgres.app)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: genonaut_admin
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO genonaut_admin;

--
-- Name: btree_gin; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS btree_gin WITH SCHEMA public;


--
-- Name: EXTENSION btree_gin; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION btree_gin IS 'support for indexing common datatypes in GIN';


--
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


--
-- Name: forbid_prompt_update(); Type: FUNCTION; Schema: public; Owner: genonaut_admin
--

CREATE FUNCTION public.forbid_prompt_update() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  IF NEW.prompt IS DISTINCT FROM OLD.prompt THEN
    RAISE EXCEPTION 'prompt is immutable';
  END IF;
  RETURN NEW;
END;
$$;


ALTER FUNCTION public.forbid_prompt_update() OWNER TO genonaut_admin;

--
-- Name: genonaut_apply_privs(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.genonaut_apply_privs() RETURNS event_trigger
    LANGUAGE plpgsql
    AS $$
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


ALTER FUNCTION public.genonaut_apply_privs() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: genonaut_admin
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO genonaut_admin;

--
-- Name: available_models; Type: TABLE; Schema: public; Owner: genonaut_admin
--

CREATE TABLE public.available_models (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    type character varying(20) NOT NULL,
    file_path character varying(512) NOT NULL,
    description text,
    is_active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.available_models OWNER TO genonaut_admin;

--
-- Name: available_models_id_seq; Type: SEQUENCE; Schema: public; Owner: genonaut_admin
--

CREATE SEQUENCE public.available_models_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.available_models_id_seq OWNER TO genonaut_admin;

--
-- Name: available_models_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: genonaut_admin
--

ALTER SEQUENCE public.available_models_id_seq OWNED BY public.available_models.id;


--
-- Name: content_items; Type: TABLE; Schema: public; Owner: genonaut_admin
--

CREATE TABLE public.content_items (
    id integer NOT NULL,
    title character varying(255) NOT NULL,
    content_type character varying(50) NOT NULL,
    content_data text NOT NULL,
    item_metadata jsonb,
    creator_id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    quality_score double precision,
    is_private boolean NOT NULL,
    path_thumb character varying(512),
    prompt character varying(20000) NOT NULL,
    path_thumbs_alt_res jsonb
);


ALTER TABLE public.content_items OWNER TO genonaut_admin;

--
-- Name: content_items_auto; Type: TABLE; Schema: public; Owner: genonaut_admin
--

CREATE TABLE public.content_items_auto (
    id integer NOT NULL,
    title character varying(255) NOT NULL,
    content_type character varying(50) NOT NULL,
    content_data text NOT NULL,
    item_metadata jsonb,
    creator_id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    quality_score double precision,
    is_private boolean NOT NULL,
    path_thumb character varying(512),
    prompt character varying(20000) NOT NULL,
    path_thumbs_alt_res jsonb
);


ALTER TABLE public.content_items_auto OWNER TO genonaut_admin;

--
-- Name: content_items_auto_id_seq; Type: SEQUENCE; Schema: public; Owner: genonaut_admin
--

CREATE SEQUENCE public.content_items_auto_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.content_items_auto_id_seq OWNER TO genonaut_admin;

--
-- Name: content_items_auto_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: genonaut_admin
--

ALTER SEQUENCE public.content_items_auto_id_seq OWNED BY public.content_items_auto.id;


--
-- Name: content_items_id_seq; Type: SEQUENCE; Schema: public; Owner: genonaut_admin
--

CREATE SEQUENCE public.content_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.content_items_id_seq OWNER TO genonaut_admin;

--
-- Name: content_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: genonaut_admin
--

ALTER SEQUENCE public.content_items_id_seq OWNED BY public.content_items.id;


--
-- Name: content_tags; Type: TABLE; Schema: public; Owner: genonaut_admin
--

CREATE TABLE public.content_tags (
    content_id integer NOT NULL,
    content_source character varying(10) NOT NULL,
    tag_id uuid NOT NULL
);


ALTER TABLE public.content_tags OWNER TO genonaut_admin;

--
-- Name: flagged_content; Type: TABLE; Schema: public; Owner: genonaut_admin
--

CREATE TABLE public.flagged_content (
    id integer NOT NULL,
    content_item_id integer,
    content_item_auto_id integer,
    content_source character varying(20) NOT NULL,
    flagged_text text NOT NULL,
    flagged_words jsonb NOT NULL,
    total_problem_words integer NOT NULL,
    total_words integer NOT NULL,
    problem_percentage double precision NOT NULL,
    risk_score double precision NOT NULL,
    creator_id uuid NOT NULL,
    flagged_at timestamp without time zone NOT NULL,
    reviewed boolean NOT NULL,
    reviewed_at timestamp without time zone,
    reviewed_by uuid,
    notes text
);


ALTER TABLE public.flagged_content OWNER TO genonaut_admin;

--
-- Name: flagged_content_id_seq; Type: SEQUENCE; Schema: public; Owner: genonaut_admin
--

CREATE SEQUENCE public.flagged_content_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.flagged_content_id_seq OWNER TO genonaut_admin;

--
-- Name: flagged_content_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: genonaut_admin
--

ALTER SEQUENCE public.flagged_content_id_seq OWNED BY public.flagged_content.id;


--
-- Name: generation_jobs; Type: TABLE; Schema: public; Owner: genonaut_admin
--

CREATE TABLE public.generation_jobs (
    id integer NOT NULL,
    user_id uuid NOT NULL,
    job_type character varying(50) NOT NULL,
    prompt character varying(20000) NOT NULL,
    status character varying(20) NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    error_message text,
    params jsonb,
    content_id integer,
    celery_task_id character varying(255),
    negative_prompt text,
    checkpoint_model character varying(255),
    lora_models jsonb,
    width integer,
    height integer,
    batch_size integer,
    comfyui_prompt_id character varying(255)
);


ALTER TABLE public.generation_jobs OWNER TO genonaut_admin;

--
-- Name: generation_jobs_id_seq; Type: SEQUENCE; Schema: public; Owner: genonaut_admin
--

CREATE SEQUENCE public.generation_jobs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.generation_jobs_id_seq OWNER TO genonaut_admin;

--
-- Name: generation_jobs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: genonaut_admin
--

ALTER SEQUENCE public.generation_jobs_id_seq OWNED BY public.generation_jobs.id;


--
-- Name: models_checkpoints; Type: TABLE; Schema: public; Owner: genonaut_admin
--

CREATE TABLE public.models_checkpoints (
    id uuid NOT NULL,
    path character varying(500) NOT NULL,
    filename character varying(255),
    name character varying(255),
    version character varying(50),
    architecture character varying(100),
    family character varying(100),
    description text,
    rating double precision,
    tags jsonb,
    model_metadata jsonb,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.models_checkpoints OWNER TO genonaut_admin;

--
-- Name: models_loras; Type: TABLE; Schema: public; Owner: genonaut_admin
--

CREATE TABLE public.models_loras (
    id uuid NOT NULL,
    path character varying(500) NOT NULL,
    filename character varying(255),
    name character varying(255),
    version character varying(50),
    compatible_architectures character varying(255),
    family character varying(100),
    description text,
    rating double precision,
    tags jsonb,
    trigger_words jsonb,
    optimal_checkpoints jsonb,
    model_metadata jsonb,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.models_loras OWNER TO genonaut_admin;

--
-- Name: recommendations; Type: TABLE; Schema: public; Owner: genonaut_admin
--

CREATE TABLE public.recommendations (
    id integer NOT NULL,
    user_id uuid NOT NULL,
    content_item_id integer NOT NULL,
    recommendation_score double precision NOT NULL,
    algorithm_version character varying(50) NOT NULL,
    created_at timestamp without time zone NOT NULL,
    is_served boolean NOT NULL,
    served_at timestamp without time zone,
    rec_metadata jsonb
);


ALTER TABLE public.recommendations OWNER TO genonaut_admin;

--
-- Name: recommendations_id_seq; Type: SEQUENCE; Schema: public; Owner: genonaut_admin
--

CREATE SEQUENCE public.recommendations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.recommendations_id_seq OWNER TO genonaut_admin;

--
-- Name: recommendations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: genonaut_admin
--

ALTER SEQUENCE public.recommendations_id_seq OWNED BY public.recommendations.id;


--
-- Name: tag_parents; Type: TABLE; Schema: public; Owner: genonaut_admin
--

CREATE TABLE public.tag_parents (
    tag_id uuid NOT NULL,
    parent_id uuid NOT NULL
);


ALTER TABLE public.tag_parents OWNER TO genonaut_admin;

--
-- Name: tag_ratings; Type: TABLE; Schema: public; Owner: genonaut_admin
--

CREATE TABLE public.tag_ratings (
    id integer NOT NULL,
    user_id uuid NOT NULL,
    tag_id uuid NOT NULL,
    rating double precision NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.tag_ratings OWNER TO genonaut_admin;

--
-- Name: tag_ratings_id_seq; Type: SEQUENCE; Schema: public; Owner: genonaut_admin
--

CREATE SEQUENCE public.tag_ratings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tag_ratings_id_seq OWNER TO genonaut_admin;

--
-- Name: tag_ratings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: genonaut_admin
--

ALTER SEQUENCE public.tag_ratings_id_seq OWNED BY public.tag_ratings.id;


--
-- Name: tags; Type: TABLE; Schema: public; Owner: genonaut_admin
--

CREATE TABLE public.tags (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    tag_metadata jsonb NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.tags OWNER TO genonaut_admin;

--
-- Name: user_interactions; Type: TABLE; Schema: public; Owner: genonaut_admin
--

CREATE TABLE public.user_interactions (
    id integer NOT NULL,
    user_id uuid NOT NULL,
    content_item_id integer NOT NULL,
    interaction_type character varying(50) NOT NULL,
    rating integer,
    duration integer,
    created_at timestamp without time zone NOT NULL,
    interaction_metadata jsonb
);


ALTER TABLE public.user_interactions OWNER TO genonaut_admin;

--
-- Name: user_interactions_id_seq; Type: SEQUENCE; Schema: public; Owner: genonaut_admin
--

CREATE SEQUENCE public.user_interactions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_interactions_id_seq OWNER TO genonaut_admin;

--
-- Name: user_interactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: genonaut_admin
--

ALTER SEQUENCE public.user_interactions_id_seq OWNED BY public.user_interactions.id;


--
-- Name: user_notifications; Type: TABLE; Schema: public; Owner: genonaut_admin
--

CREATE TABLE public.user_notifications (
    id integer NOT NULL,
    user_id uuid NOT NULL,
    title character varying(255) NOT NULL,
    message text NOT NULL,
    notification_type character varying(50) NOT NULL,
    read_status boolean NOT NULL,
    related_job_id integer,
    related_content_id integer,
    created_at timestamp without time zone NOT NULL,
    read_at timestamp without time zone
);


ALTER TABLE public.user_notifications OWNER TO genonaut_admin;

--
-- Name: user_notifications_id_seq; Type: SEQUENCE; Schema: public; Owner: genonaut_admin
--

CREATE SEQUENCE public.user_notifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_notifications_id_seq OWNER TO genonaut_admin;

--
-- Name: user_notifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: genonaut_admin
--

ALTER SEQUENCE public.user_notifications_id_seq OWNED BY public.user_notifications.id;


--
-- Name: user_search_history; Type: TABLE; Schema: public; Owner: genonaut_admin
--

CREATE TABLE public.user_search_history (
    id integer NOT NULL,
    user_id uuid NOT NULL,
    search_query character varying(500) NOT NULL,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.user_search_history OWNER TO genonaut_admin;

--
-- Name: user_search_history_id_seq; Type: SEQUENCE; Schema: public; Owner: genonaut_admin
--

CREATE SEQUENCE public.user_search_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_search_history_id_seq OWNER TO genonaut_admin;

--
-- Name: user_search_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: genonaut_admin
--

ALTER SEQUENCE public.user_search_history_id_seq OWNED BY public.user_search_history.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: genonaut_admin
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    username character varying(50) NOT NULL,
    email character varying(255) NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    preferences jsonb,
    is_active boolean NOT NULL,
    favorite_tag_ids jsonb
);


ALTER TABLE public.users OWNER TO genonaut_admin;

--
-- Name: available_models id; Type: DEFAULT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.available_models ALTER COLUMN id SET DEFAULT nextval('public.available_models_id_seq'::regclass);


--
-- Name: content_items id; Type: DEFAULT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.content_items ALTER COLUMN id SET DEFAULT nextval('public.content_items_id_seq'::regclass);


--
-- Name: content_items_auto id; Type: DEFAULT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.content_items_auto ALTER COLUMN id SET DEFAULT nextval('public.content_items_auto_id_seq'::regclass);


--
-- Name: flagged_content id; Type: DEFAULT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.flagged_content ALTER COLUMN id SET DEFAULT nextval('public.flagged_content_id_seq'::regclass);


--
-- Name: generation_jobs id; Type: DEFAULT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.generation_jobs ALTER COLUMN id SET DEFAULT nextval('public.generation_jobs_id_seq'::regclass);


--
-- Name: recommendations id; Type: DEFAULT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.recommendations ALTER COLUMN id SET DEFAULT nextval('public.recommendations_id_seq'::regclass);


--
-- Name: tag_ratings id; Type: DEFAULT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.tag_ratings ALTER COLUMN id SET DEFAULT nextval('public.tag_ratings_id_seq'::regclass);


--
-- Name: user_interactions id; Type: DEFAULT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.user_interactions ALTER COLUMN id SET DEFAULT nextval('public.user_interactions_id_seq'::regclass);


--
-- Name: user_notifications id; Type: DEFAULT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.user_notifications ALTER COLUMN id SET DEFAULT nextval('public.user_notifications_id_seq'::regclass);


--
-- Name: user_search_history id; Type: DEFAULT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.user_search_history ALTER COLUMN id SET DEFAULT nextval('public.user_search_history_id_seq'::regclass);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: available_models available_models_file_path_key; Type: CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.available_models
    ADD CONSTRAINT available_models_file_path_key UNIQUE (file_path);


--
-- Name: available_models available_models_pkey; Type: CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.available_models
    ADD CONSTRAINT available_models_pkey PRIMARY KEY (id);


--
-- Name: content_items_auto content_items_auto_pkey; Type: CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.content_items_auto
    ADD CONSTRAINT content_items_auto_pkey PRIMARY KEY (id);


--
-- Name: content_items content_items_pkey; Type: CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.content_items
    ADD CONSTRAINT content_items_pkey PRIMARY KEY (id);


--
-- Name: content_tags content_tags_pkey; Type: CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.content_tags
    ADD CONSTRAINT content_tags_pkey PRIMARY KEY (content_id, content_source, tag_id);


--
-- Name: flagged_content flagged_content_pkey; Type: CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.flagged_content
    ADD CONSTRAINT flagged_content_pkey PRIMARY KEY (id);


--
-- Name: generation_jobs generation_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.generation_jobs
    ADD CONSTRAINT generation_jobs_pkey PRIMARY KEY (id);


--
-- Name: models_checkpoints models_checkpoints_filename_key; Type: CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.models_checkpoints
    ADD CONSTRAINT models_checkpoints_filename_key UNIQUE (filename);


--
-- Name: models_checkpoints models_checkpoints_name_key; Type: CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.models_checkpoints
    ADD CONSTRAINT models_checkpoints_name_key UNIQUE (name);


--
-- Name: models_checkpoints models_checkpoints_pkey; Type: CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.models_checkpoints
    ADD CONSTRAINT models_checkpoints_pkey PRIMARY KEY (id);


--
-- Name: models_loras models_loras_filename_key; Type: CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.models_loras
    ADD CONSTRAINT models_loras_filename_key UNIQUE (filename);


--
-- Name: models_loras models_loras_name_key; Type: CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.models_loras
    ADD CONSTRAINT models_loras_name_key UNIQUE (name);


--
-- Name: models_loras models_loras_pkey; Type: CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.models_loras
    ADD CONSTRAINT models_loras_pkey PRIMARY KEY (id);


--
-- Name: recommendations recommendations_pkey; Type: CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.recommendations
    ADD CONSTRAINT recommendations_pkey PRIMARY KEY (id);


--
-- Name: tag_parents tag_parents_pkey; Type: CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.tag_parents
    ADD CONSTRAINT tag_parents_pkey PRIMARY KEY (tag_id, parent_id);


--
-- Name: tag_ratings tag_ratings_pkey; Type: CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.tag_ratings
    ADD CONSTRAINT tag_ratings_pkey PRIMARY KEY (id);


--
-- Name: tags tags_pkey; Type: CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.tags
    ADD CONSTRAINT tags_pkey PRIMARY KEY (id);


--
-- Name: user_interactions unique_user_content_interaction; Type: CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.user_interactions
    ADD CONSTRAINT unique_user_content_interaction UNIQUE (user_id, content_item_id, interaction_type, created_at);


--
-- Name: available_models uq_model_name_type; Type: CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.available_models
    ADD CONSTRAINT uq_model_name_type UNIQUE (name, type);


--
-- Name: tag_ratings uq_user_tag_rating; Type: CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.tag_ratings
    ADD CONSTRAINT uq_user_tag_rating UNIQUE (user_id, tag_id);


--
-- Name: user_interactions user_interactions_pkey; Type: CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.user_interactions
    ADD CONSTRAINT user_interactions_pkey PRIMARY KEY (id);


--
-- Name: user_notifications user_notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.user_notifications
    ADD CONSTRAINT user_notifications_pkey PRIMARY KEY (id);


--
-- Name: user_search_history user_search_history_pkey; Type: CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.user_search_history
    ADD CONSTRAINT user_search_history_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ci_title_fts_idx; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ci_title_fts_idx ON public.content_items USING gin (to_tsvector('english'::regconfig, (COALESCE(title, ''::character varying))::text));


--
-- Name: cia_title_fts_idx; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX cia_title_fts_idx ON public.content_items_auto USING gin (to_tsvector('english'::regconfig, (COALESCE(title, ''::character varying))::text));


--
-- Name: gj_prompt_fts_idx; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX gj_prompt_fts_idx ON public.generation_jobs USING gin (to_tsvector('english'::regconfig, (COALESCE(prompt, (''::text)::character varying))::text));


--
-- Name: idx_available_models_active_name; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_available_models_active_name ON public.available_models USING btree (is_active, name);


--
-- Name: idx_available_models_type_active; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_available_models_type_active ON public.available_models USING btree (type, is_active);


--
-- Name: idx_checkpoint_description_gist; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_checkpoint_description_gist ON public.models_checkpoints USING gist (to_tsvector('english'::regconfig, description));


--
-- Name: idx_checkpoint_model_metadata_gin; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_checkpoint_model_metadata_gin ON public.models_checkpoints USING gin (model_metadata jsonb_path_ops);


--
-- Name: idx_checkpoint_name_lower; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_checkpoint_name_lower ON public.models_checkpoints USING btree (lower((name)::text));


--
-- Name: idx_checkpoint_rating_desc; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_checkpoint_rating_desc ON public.models_checkpoints USING btree (rating DESC);


--
-- Name: idx_checkpoint_tags_gin; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_checkpoint_tags_gin ON public.models_checkpoints USING gin (tags);


--
-- Name: idx_content_items_auto_created_at_desc; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_content_items_auto_created_at_desc ON public.content_items_auto USING btree (created_at DESC);


--
-- Name: idx_content_items_auto_creator_created; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_content_items_auto_creator_created ON public.content_items_auto USING btree (creator_id, created_at DESC);


--
-- Name: idx_content_items_auto_metadata_gin; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_content_items_auto_metadata_gin ON public.content_items_auto USING gin (item_metadata);


--
-- Name: idx_content_items_auto_public_created; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_content_items_auto_public_created ON public.content_items_auto USING btree (created_at DESC) WHERE (is_private = false);


--
-- Name: idx_content_items_auto_quality_created; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_content_items_auto_quality_created ON public.content_items_auto USING btree (quality_score DESC, created_at DESC);


--
-- Name: idx_content_items_auto_title_gist; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_content_items_auto_title_gist ON public.content_items_auto USING gist (title public.gist_trgm_ops);


--
-- Name: idx_content_items_auto_type_created; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_content_items_auto_type_created ON public.content_items_auto USING btree (content_type, created_at DESC);


--
-- Name: idx_content_items_created_at_desc; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_content_items_created_at_desc ON public.content_items USING btree (created_at DESC);


--
-- Name: idx_content_items_creator_created; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_content_items_creator_created ON public.content_items USING btree (creator_id, created_at DESC);


--
-- Name: idx_content_items_metadata_gin; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_content_items_metadata_gin ON public.content_items USING gin (item_metadata);


--
-- Name: idx_content_items_public_created; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_content_items_public_created ON public.content_items USING btree (created_at DESC) WHERE (is_private = false);


--
-- Name: idx_content_items_quality_created; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_content_items_quality_created ON public.content_items USING btree (quality_score DESC, created_at DESC);


--
-- Name: idx_content_items_title_gist; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_content_items_title_gist ON public.content_items USING gist (title public.gist_trgm_ops);


--
-- Name: idx_content_items_type_created; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_content_items_type_created ON public.content_items USING btree (content_type, created_at DESC);


--
-- Name: idx_content_tags_content; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_content_tags_content ON public.content_tags USING btree (content_id, content_source);


--
-- Name: idx_content_tags_tag_content; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_content_tags_tag_content ON public.content_tags USING btree (tag_id, content_id);


--
-- Name: idx_flagged_content_creator_flagged; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_flagged_content_creator_flagged ON public.flagged_content USING btree (creator_id, flagged_at DESC);


--
-- Name: idx_flagged_content_flagged_at_desc; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_flagged_content_flagged_at_desc ON public.flagged_content USING btree (flagged_at DESC);


--
-- Name: idx_flagged_content_reviewed_flagged; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_flagged_content_reviewed_flagged ON public.flagged_content USING btree (reviewed, flagged_at DESC);


--
-- Name: idx_flagged_content_risk_flagged; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_flagged_content_risk_flagged ON public.flagged_content USING btree (risk_score DESC, flagged_at DESC);


--
-- Name: idx_flagged_content_risk_score_desc; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_flagged_content_risk_score_desc ON public.flagged_content USING btree (risk_score DESC);


--
-- Name: idx_flagged_content_source_flagged; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_flagged_content_source_flagged ON public.flagged_content USING btree (content_source, flagged_at DESC);


--
-- Name: idx_flagged_content_unreviewed_high_risk; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_flagged_content_unreviewed_high_risk ON public.flagged_content USING btree (risk_score DESC) WHERE (reviewed = false);


--
-- Name: idx_flagged_content_words_gin; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_flagged_content_words_gin ON public.flagged_content USING gin (flagged_words);


--
-- Name: idx_generation_jobs_celery_task_id; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_generation_jobs_celery_task_id ON public.generation_jobs USING btree (celery_task_id) WHERE (celery_task_id IS NOT NULL);


--
-- Name: idx_generation_jobs_comfyui_prompt_id; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_generation_jobs_comfyui_prompt_id ON public.generation_jobs USING btree (comfyui_prompt_id) WHERE (comfyui_prompt_id IS NOT NULL);


--
-- Name: idx_generation_jobs_completed_at_desc; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_generation_jobs_completed_at_desc ON public.generation_jobs USING btree (completed_at DESC) WHERE (completed_at IS NOT NULL);


--
-- Name: idx_generation_jobs_created_at_desc; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_generation_jobs_created_at_desc ON public.generation_jobs USING btree (created_at DESC);


--
-- Name: idx_generation_jobs_prompt_gist; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_generation_jobs_prompt_gist ON public.generation_jobs USING gist (prompt public.gist_trgm_ops);


--
-- Name: idx_generation_jobs_status_created; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_generation_jobs_status_created ON public.generation_jobs USING btree (status, created_at DESC);


--
-- Name: idx_generation_jobs_status_created_priority; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_generation_jobs_status_created_priority ON public.generation_jobs USING btree (status, created_at) WHERE ((status)::text = ANY ((ARRAY['pending'::character varying, 'running'::character varying])::text[]));


--
-- Name: idx_generation_jobs_type_created; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_generation_jobs_type_created ON public.generation_jobs USING btree (job_type, created_at DESC);


--
-- Name: idx_generation_jobs_user_created; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_generation_jobs_user_created ON public.generation_jobs USING btree (user_id, created_at DESC);


--
-- Name: idx_generation_jobs_user_status_created; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_generation_jobs_user_status_created ON public.generation_jobs USING btree (user_id, status, created_at DESC);


--
-- Name: idx_generation_jobs_user_type_created; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_generation_jobs_user_type_created ON public.generation_jobs USING btree (user_id, job_type, created_at DESC);


--
-- Name: idx_lora_description_gist; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_lora_description_gist ON public.models_loras USING gist (to_tsvector('english'::regconfig, description));


--
-- Name: idx_lora_model_metadata_gin; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_lora_model_metadata_gin ON public.models_loras USING gin (model_metadata jsonb_path_ops);


--
-- Name: idx_lora_name_lower; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_lora_name_lower ON public.models_loras USING btree (lower((name)::text));


--
-- Name: idx_lora_optimal_checkpoints_gin; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_lora_optimal_checkpoints_gin ON public.models_loras USING gin (optimal_checkpoints);


--
-- Name: idx_lora_rating_desc; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_lora_rating_desc ON public.models_loras USING btree (rating DESC);


--
-- Name: idx_lora_tags_gin; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_lora_tags_gin ON public.models_loras USING gin (tags);


--
-- Name: idx_lora_trigger_words_gin; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_lora_trigger_words_gin ON public.models_loras USING gin (trigger_words);


--
-- Name: idx_notifications_type; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_notifications_type ON public.user_notifications USING btree (notification_type);


--
-- Name: idx_notifications_user_created; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_notifications_user_created ON public.user_notifications USING btree (user_id, created_at DESC);


--
-- Name: idx_notifications_user_unread; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_notifications_user_unread ON public.user_notifications USING btree (user_id, read_status);


--
-- Name: idx_recommendations_algorithm_created; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_recommendations_algorithm_created ON public.recommendations USING btree (algorithm_version, created_at DESC);


--
-- Name: idx_recommendations_content_created; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_recommendations_content_created ON public.recommendations USING btree (content_item_id, created_at DESC);


--
-- Name: idx_recommendations_created_at_desc; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_recommendations_created_at_desc ON public.recommendations USING btree (created_at DESC);


--
-- Name: idx_recommendations_score_created; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_recommendations_score_created ON public.recommendations USING btree (recommendation_score DESC, created_at DESC);


--
-- Name: idx_recommendations_served_created; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_recommendations_served_created ON public.recommendations USING btree (is_served, created_at DESC);


--
-- Name: idx_recommendations_user_created; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_recommendations_user_created ON public.recommendations USING btree (user_id, created_at DESC);


--
-- Name: idx_recommendations_user_score_created; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_recommendations_user_score_created ON public.recommendations USING btree (user_id, recommendation_score DESC, created_at DESC);


--
-- Name: idx_recommendations_user_served_created; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_recommendations_user_served_created ON public.recommendations USING btree (user_id, is_served, created_at DESC);


--
-- Name: idx_tag_parents_parent; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_tag_parents_parent ON public.tag_parents USING btree (parent_id);


--
-- Name: idx_tag_parents_tag; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_tag_parents_tag ON public.tag_parents USING btree (tag_id);


--
-- Name: idx_tag_ratings_tag_rating; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_tag_ratings_tag_rating ON public.tag_ratings USING btree (tag_id, rating DESC);


--
-- Name: idx_tag_ratings_user_created; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_tag_ratings_user_created ON public.tag_ratings USING btree (user_id, created_at DESC);


--
-- Name: idx_tags_created_at_desc; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_tags_created_at_desc ON public.tags USING btree (created_at DESC);


--
-- Name: idx_tags_name; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_tags_name ON public.tags USING btree (name);


--
-- Name: idx_user_interactions_content_created; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_user_interactions_content_created ON public.user_interactions USING btree (content_item_id, created_at DESC);


--
-- Name: idx_user_interactions_created_at_desc; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_user_interactions_created_at_desc ON public.user_interactions USING btree (created_at DESC);


--
-- Name: idx_user_interactions_rating_created; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_user_interactions_rating_created ON public.user_interactions USING btree (rating DESC, created_at DESC) WHERE (rating IS NOT NULL);


--
-- Name: idx_user_interactions_type_created; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_user_interactions_type_created ON public.user_interactions USING btree (interaction_type, created_at DESC);


--
-- Name: idx_user_interactions_user_created; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_user_interactions_user_created ON public.user_interactions USING btree (user_id, created_at DESC);


--
-- Name: idx_user_interactions_user_type_created; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_user_interactions_user_type_created ON public.user_interactions USING btree (user_id, interaction_type, created_at DESC);


--
-- Name: idx_user_search_history_user_created; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_user_search_history_user_created ON public.user_search_history USING btree (user_id, created_at DESC);


--
-- Name: idx_users_active_created; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_users_active_created ON public.users USING btree (is_active, created_at DESC);


--
-- Name: idx_users_created_at_desc; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_users_created_at_desc ON public.users USING btree (created_at DESC);


--
-- Name: idx_users_email_lower; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_users_email_lower ON public.users USING btree (lower((email)::text));


--
-- Name: idx_users_favorite_tags_gin; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_users_favorite_tags_gin ON public.users USING gin (favorite_tag_ids);


--
-- Name: idx_users_username_lower; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX idx_users_username_lower ON public.users USING btree (lower((username)::text));


--
-- Name: ix_available_models_is_active; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_available_models_is_active ON public.available_models USING btree (is_active);


--
-- Name: ix_available_models_name; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_available_models_name ON public.available_models USING btree (name);


--
-- Name: ix_available_models_type; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_available_models_type ON public.available_models USING btree (type);


--
-- Name: ix_content_items_auto_content_type; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_content_items_auto_content_type ON public.content_items_auto USING btree (content_type);


--
-- Name: ix_content_items_auto_creator_id; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_content_items_auto_creator_id ON public.content_items_auto USING btree (creator_id);


--
-- Name: ix_content_items_content_type; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_content_items_content_type ON public.content_items USING btree (content_type);


--
-- Name: ix_content_items_creator_id; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_content_items_creator_id ON public.content_items USING btree (creator_id);


--
-- Name: ix_flagged_content_content_item_auto_id; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_flagged_content_content_item_auto_id ON public.flagged_content USING btree (content_item_auto_id);


--
-- Name: ix_flagged_content_content_item_id; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_flagged_content_content_item_id ON public.flagged_content USING btree (content_item_id);


--
-- Name: ix_flagged_content_content_source; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_flagged_content_content_source ON public.flagged_content USING btree (content_source);


--
-- Name: ix_flagged_content_creator_id; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_flagged_content_creator_id ON public.flagged_content USING btree (creator_id);


--
-- Name: ix_flagged_content_reviewed; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_flagged_content_reviewed ON public.flagged_content USING btree (reviewed);


--
-- Name: ix_generation_jobs_celery_task_id; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_generation_jobs_celery_task_id ON public.generation_jobs USING btree (celery_task_id);


--
-- Name: ix_generation_jobs_comfyui_prompt_id; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_generation_jobs_comfyui_prompt_id ON public.generation_jobs USING btree (comfyui_prompt_id);


--
-- Name: ix_generation_jobs_job_type; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_generation_jobs_job_type ON public.generation_jobs USING btree (job_type);


--
-- Name: ix_generation_jobs_status; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_generation_jobs_status ON public.generation_jobs USING btree (status);


--
-- Name: ix_generation_jobs_user_id; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_generation_jobs_user_id ON public.generation_jobs USING btree (user_id);


--
-- Name: ix_models_checkpoints_architecture; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_models_checkpoints_architecture ON public.models_checkpoints USING btree (architecture);


--
-- Name: ix_models_checkpoints_family; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_models_checkpoints_family ON public.models_checkpoints USING btree (family);


--
-- Name: ix_models_checkpoints_path; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE UNIQUE INDEX ix_models_checkpoints_path ON public.models_checkpoints USING btree (path);


--
-- Name: ix_models_checkpoints_rating; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_models_checkpoints_rating ON public.models_checkpoints USING btree (rating);


--
-- Name: ix_models_loras_compatible_architectures; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_models_loras_compatible_architectures ON public.models_loras USING btree (compatible_architectures);


--
-- Name: ix_models_loras_family; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_models_loras_family ON public.models_loras USING btree (family);


--
-- Name: ix_models_loras_path; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE UNIQUE INDEX ix_models_loras_path ON public.models_loras USING btree (path);


--
-- Name: ix_models_loras_rating; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_models_loras_rating ON public.models_loras USING btree (rating);


--
-- Name: ix_recommendations_content_item_id; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_recommendations_content_item_id ON public.recommendations USING btree (content_item_id);


--
-- Name: ix_recommendations_user_id; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_recommendations_user_id ON public.recommendations USING btree (user_id);


--
-- Name: ix_tag_ratings_tag_id; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_tag_ratings_tag_id ON public.tag_ratings USING btree (tag_id);


--
-- Name: ix_tag_ratings_user_id; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_tag_ratings_user_id ON public.tag_ratings USING btree (user_id);


--
-- Name: ix_tags_name; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE UNIQUE INDEX ix_tags_name ON public.tags USING btree (name);


--
-- Name: ix_user_interactions_content_item_id; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_user_interactions_content_item_id ON public.user_interactions USING btree (content_item_id);


--
-- Name: ix_user_interactions_interaction_type; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_user_interactions_interaction_type ON public.user_interactions USING btree (interaction_type);


--
-- Name: ix_user_interactions_user_id; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_user_interactions_user_id ON public.user_interactions USING btree (user_id);


--
-- Name: ix_user_notifications_notification_type; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_user_notifications_notification_type ON public.user_notifications USING btree (notification_type);


--
-- Name: ix_user_notifications_read_status; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_user_notifications_read_status ON public.user_notifications USING btree (read_status);


--
-- Name: ix_user_notifications_user_id; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_user_notifications_user_id ON public.user_notifications USING btree (user_id);


--
-- Name: ix_user_search_history_user_id; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE INDEX ix_user_search_history_user_id ON public.user_search_history USING btree (user_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: genonaut_admin
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: content_items trg_forbid_prompt_update_ci; Type: TRIGGER; Schema: public; Owner: genonaut_admin
--

CREATE TRIGGER trg_forbid_prompt_update_ci BEFORE UPDATE ON public.content_items FOR EACH ROW EXECUTE FUNCTION public.forbid_prompt_update();


--
-- Name: content_items_auto trg_forbid_prompt_update_cia; Type: TRIGGER; Schema: public; Owner: genonaut_admin
--

CREATE TRIGGER trg_forbid_prompt_update_cia BEFORE UPDATE ON public.content_items_auto FOR EACH ROW EXECUTE FUNCTION public.forbid_prompt_update();


--
-- Name: generation_jobs trg_forbid_prompt_update_gj; Type: TRIGGER; Schema: public; Owner: genonaut_admin
--

CREATE TRIGGER trg_forbid_prompt_update_gj BEFORE UPDATE ON public.generation_jobs FOR EACH ROW EXECUTE FUNCTION public.forbid_prompt_update();


--
-- Name: content_items_auto content_items_auto_creator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.content_items_auto
    ADD CONSTRAINT content_items_auto_creator_id_fkey FOREIGN KEY (creator_id) REFERENCES public.users(id);


--
-- Name: content_items content_items_creator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.content_items
    ADD CONSTRAINT content_items_creator_id_fkey FOREIGN KEY (creator_id) REFERENCES public.users(id);


--
-- Name: content_tags content_tags_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.content_tags
    ADD CONSTRAINT content_tags_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tags(id) ON DELETE CASCADE;


--
-- Name: flagged_content flagged_content_content_item_auto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.flagged_content
    ADD CONSTRAINT flagged_content_content_item_auto_id_fkey FOREIGN KEY (content_item_auto_id) REFERENCES public.content_items_auto(id) ON DELETE CASCADE;


--
-- Name: flagged_content flagged_content_content_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.flagged_content
    ADD CONSTRAINT flagged_content_content_item_id_fkey FOREIGN KEY (content_item_id) REFERENCES public.content_items(id) ON DELETE CASCADE;


--
-- Name: flagged_content flagged_content_creator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.flagged_content
    ADD CONSTRAINT flagged_content_creator_id_fkey FOREIGN KEY (creator_id) REFERENCES public.users(id);


--
-- Name: flagged_content flagged_content_reviewed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.flagged_content
    ADD CONSTRAINT flagged_content_reviewed_by_fkey FOREIGN KEY (reviewed_by) REFERENCES public.users(id);


--
-- Name: generation_jobs generation_jobs_content_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.generation_jobs
    ADD CONSTRAINT generation_jobs_content_id_fkey FOREIGN KEY (content_id) REFERENCES public.content_items(id);


--
-- Name: generation_jobs generation_jobs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.generation_jobs
    ADD CONSTRAINT generation_jobs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: recommendations recommendations_content_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.recommendations
    ADD CONSTRAINT recommendations_content_item_id_fkey FOREIGN KEY (content_item_id) REFERENCES public.content_items(id);


--
-- Name: recommendations recommendations_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.recommendations
    ADD CONSTRAINT recommendations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: tag_parents tag_parents_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.tag_parents
    ADD CONSTRAINT tag_parents_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.tags(id) ON DELETE CASCADE;


--
-- Name: tag_parents tag_parents_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.tag_parents
    ADD CONSTRAINT tag_parents_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tags(id) ON DELETE CASCADE;


--
-- Name: tag_ratings tag_ratings_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.tag_ratings
    ADD CONSTRAINT tag_ratings_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tags(id);


--
-- Name: tag_ratings tag_ratings_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.tag_ratings
    ADD CONSTRAINT tag_ratings_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: user_interactions user_interactions_content_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.user_interactions
    ADD CONSTRAINT user_interactions_content_item_id_fkey FOREIGN KEY (content_item_id) REFERENCES public.content_items(id);


--
-- Name: user_interactions user_interactions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.user_interactions
    ADD CONSTRAINT user_interactions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: user_notifications user_notifications_related_content_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.user_notifications
    ADD CONSTRAINT user_notifications_related_content_id_fkey FOREIGN KEY (related_content_id) REFERENCES public.content_items(id);


--
-- Name: user_notifications user_notifications_related_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.user_notifications
    ADD CONSTRAINT user_notifications_related_job_id_fkey FOREIGN KEY (related_job_id) REFERENCES public.generation_jobs(id);


--
-- Name: user_notifications user_notifications_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.user_notifications
    ADD CONSTRAINT user_notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: user_search_history user_search_history_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: genonaut_admin
--

ALTER TABLE ONLY public.user_search_history
    ADD CONSTRAINT user_search_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: genonaut_admin
--

GRANT USAGE ON SCHEMA public TO genonaut_ro;
GRANT USAGE ON SCHEMA public TO genonaut_rw;


--
-- Name: FUNCTION gtrgm_in(cstring); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gtrgm_in(cstring) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gtrgm_in(cstring) TO genonaut_ro;


--
-- Name: FUNCTION gtrgm_out(public.gtrgm); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gtrgm_out(public.gtrgm) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gtrgm_out(public.gtrgm) TO genonaut_ro;


--
-- Name: FUNCTION forbid_prompt_update(); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.forbid_prompt_update() TO genonaut_rw;
GRANT ALL ON FUNCTION public.forbid_prompt_update() TO genonaut_ro;


--
-- Name: FUNCTION genonaut_apply_privs(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.genonaut_apply_privs() TO genonaut_ro;
GRANT ALL ON FUNCTION public.genonaut_apply_privs() TO genonaut_rw;


--
-- Name: FUNCTION gin_btree_consistent(internal, smallint, anyelement, integer, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_btree_consistent(internal, smallint, anyelement, integer, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_btree_consistent(internal, smallint, anyelement, integer, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_compare_prefix_anyenum(anyenum, anyenum, smallint, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_compare_prefix_anyenum(anyenum, anyenum, smallint, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_compare_prefix_anyenum(anyenum, anyenum, smallint, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_compare_prefix_bit(bit, bit, smallint, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_compare_prefix_bit(bit, bit, smallint, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_compare_prefix_bit(bit, bit, smallint, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_compare_prefix_bool(boolean, boolean, smallint, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_compare_prefix_bool(boolean, boolean, smallint, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_compare_prefix_bool(boolean, boolean, smallint, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_compare_prefix_bpchar(character, character, smallint, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_compare_prefix_bpchar(character, character, smallint, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_compare_prefix_bpchar(character, character, smallint, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_compare_prefix_bytea(bytea, bytea, smallint, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_compare_prefix_bytea(bytea, bytea, smallint, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_compare_prefix_bytea(bytea, bytea, smallint, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_compare_prefix_char("char", "char", smallint, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_compare_prefix_char("char", "char", smallint, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_compare_prefix_char("char", "char", smallint, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_compare_prefix_cidr(cidr, cidr, smallint, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_compare_prefix_cidr(cidr, cidr, smallint, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_compare_prefix_cidr(cidr, cidr, smallint, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_compare_prefix_date(date, date, smallint, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_compare_prefix_date(date, date, smallint, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_compare_prefix_date(date, date, smallint, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_compare_prefix_float4(real, real, smallint, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_compare_prefix_float4(real, real, smallint, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_compare_prefix_float4(real, real, smallint, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_compare_prefix_float8(double precision, double precision, smallint, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_compare_prefix_float8(double precision, double precision, smallint, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_compare_prefix_float8(double precision, double precision, smallint, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_compare_prefix_inet(inet, inet, smallint, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_compare_prefix_inet(inet, inet, smallint, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_compare_prefix_inet(inet, inet, smallint, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_compare_prefix_int2(smallint, smallint, smallint, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_compare_prefix_int2(smallint, smallint, smallint, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_compare_prefix_int2(smallint, smallint, smallint, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_compare_prefix_int4(integer, integer, smallint, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_compare_prefix_int4(integer, integer, smallint, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_compare_prefix_int4(integer, integer, smallint, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_compare_prefix_int8(bigint, bigint, smallint, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_compare_prefix_int8(bigint, bigint, smallint, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_compare_prefix_int8(bigint, bigint, smallint, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_compare_prefix_interval(interval, interval, smallint, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_compare_prefix_interval(interval, interval, smallint, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_compare_prefix_interval(interval, interval, smallint, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_compare_prefix_macaddr(macaddr, macaddr, smallint, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_compare_prefix_macaddr(macaddr, macaddr, smallint, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_compare_prefix_macaddr(macaddr, macaddr, smallint, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_compare_prefix_macaddr8(macaddr8, macaddr8, smallint, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_compare_prefix_macaddr8(macaddr8, macaddr8, smallint, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_compare_prefix_macaddr8(macaddr8, macaddr8, smallint, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_compare_prefix_money(money, money, smallint, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_compare_prefix_money(money, money, smallint, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_compare_prefix_money(money, money, smallint, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_compare_prefix_name(name, name, smallint, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_compare_prefix_name(name, name, smallint, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_compare_prefix_name(name, name, smallint, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_compare_prefix_numeric(numeric, numeric, smallint, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_compare_prefix_numeric(numeric, numeric, smallint, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_compare_prefix_numeric(numeric, numeric, smallint, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_compare_prefix_oid(oid, oid, smallint, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_compare_prefix_oid(oid, oid, smallint, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_compare_prefix_oid(oid, oid, smallint, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_compare_prefix_text(text, text, smallint, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_compare_prefix_text(text, text, smallint, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_compare_prefix_text(text, text, smallint, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_compare_prefix_time(time without time zone, time without time zone, smallint, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_compare_prefix_time(time without time zone, time without time zone, smallint, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_compare_prefix_time(time without time zone, time without time zone, smallint, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_compare_prefix_timestamp(timestamp without time zone, timestamp without time zone, smallint, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_compare_prefix_timestamp(timestamp without time zone, timestamp without time zone, smallint, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_compare_prefix_timestamp(timestamp without time zone, timestamp without time zone, smallint, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_compare_prefix_timestamptz(timestamp with time zone, timestamp with time zone, smallint, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_compare_prefix_timestamptz(timestamp with time zone, timestamp with time zone, smallint, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_compare_prefix_timestamptz(timestamp with time zone, timestamp with time zone, smallint, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_compare_prefix_timetz(time with time zone, time with time zone, smallint, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_compare_prefix_timetz(time with time zone, time with time zone, smallint, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_compare_prefix_timetz(time with time zone, time with time zone, smallint, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_compare_prefix_uuid(uuid, uuid, smallint, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_compare_prefix_uuid(uuid, uuid, smallint, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_compare_prefix_uuid(uuid, uuid, smallint, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_compare_prefix_varbit(bit varying, bit varying, smallint, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_compare_prefix_varbit(bit varying, bit varying, smallint, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_compare_prefix_varbit(bit varying, bit varying, smallint, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_enum_cmp(anyenum, anyenum); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_enum_cmp(anyenum, anyenum) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_enum_cmp(anyenum, anyenum) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_query_anyenum(anyenum, internal, smallint, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_query_anyenum(anyenum, internal, smallint, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_query_anyenum(anyenum, internal, smallint, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_query_bit(bit, internal, smallint, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_query_bit(bit, internal, smallint, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_query_bit(bit, internal, smallint, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_query_bool(boolean, internal, smallint, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_query_bool(boolean, internal, smallint, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_query_bool(boolean, internal, smallint, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_query_bpchar(character, internal, smallint, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_query_bpchar(character, internal, smallint, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_query_bpchar(character, internal, smallint, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_query_bytea(bytea, internal, smallint, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_query_bytea(bytea, internal, smallint, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_query_bytea(bytea, internal, smallint, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_query_char("char", internal, smallint, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_query_char("char", internal, smallint, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_query_char("char", internal, smallint, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_query_cidr(cidr, internal, smallint, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_query_cidr(cidr, internal, smallint, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_query_cidr(cidr, internal, smallint, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_query_date(date, internal, smallint, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_query_date(date, internal, smallint, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_query_date(date, internal, smallint, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_query_float4(real, internal, smallint, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_query_float4(real, internal, smallint, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_query_float4(real, internal, smallint, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_query_float8(double precision, internal, smallint, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_query_float8(double precision, internal, smallint, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_query_float8(double precision, internal, smallint, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_query_inet(inet, internal, smallint, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_query_inet(inet, internal, smallint, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_query_inet(inet, internal, smallint, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_query_int2(smallint, internal, smallint, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_query_int2(smallint, internal, smallint, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_query_int2(smallint, internal, smallint, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_query_int4(integer, internal, smallint, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_query_int4(integer, internal, smallint, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_query_int4(integer, internal, smallint, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_query_int8(bigint, internal, smallint, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_query_int8(bigint, internal, smallint, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_query_int8(bigint, internal, smallint, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_query_interval(interval, internal, smallint, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_query_interval(interval, internal, smallint, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_query_interval(interval, internal, smallint, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_query_macaddr(macaddr, internal, smallint, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_query_macaddr(macaddr, internal, smallint, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_query_macaddr(macaddr, internal, smallint, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_query_macaddr8(macaddr8, internal, smallint, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_query_macaddr8(macaddr8, internal, smallint, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_query_macaddr8(macaddr8, internal, smallint, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_query_money(money, internal, smallint, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_query_money(money, internal, smallint, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_query_money(money, internal, smallint, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_query_name(name, internal, smallint, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_query_name(name, internal, smallint, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_query_name(name, internal, smallint, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_query_numeric(numeric, internal, smallint, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_query_numeric(numeric, internal, smallint, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_query_numeric(numeric, internal, smallint, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_query_oid(oid, internal, smallint, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_query_oid(oid, internal, smallint, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_query_oid(oid, internal, smallint, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_query_text(text, internal, smallint, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_query_text(text, internal, smallint, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_query_text(text, internal, smallint, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_query_time(time without time zone, internal, smallint, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_query_time(time without time zone, internal, smallint, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_query_time(time without time zone, internal, smallint, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_query_timestamp(timestamp without time zone, internal, smallint, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_query_timestamp(timestamp without time zone, internal, smallint, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_query_timestamp(timestamp without time zone, internal, smallint, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_query_timestamptz(timestamp with time zone, internal, smallint, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_query_timestamptz(timestamp with time zone, internal, smallint, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_query_timestamptz(timestamp with time zone, internal, smallint, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_query_timetz(time with time zone, internal, smallint, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_query_timetz(time with time zone, internal, smallint, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_query_timetz(time with time zone, internal, smallint, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_query_trgm(text, internal, smallint, internal, internal, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_query_trgm(text, internal, smallint, internal, internal, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_query_trgm(text, internal, smallint, internal, internal, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_query_uuid(uuid, internal, smallint, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_query_uuid(uuid, internal, smallint, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_query_uuid(uuid, internal, smallint, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_query_varbit(bit varying, internal, smallint, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_query_varbit(bit varying, internal, smallint, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_query_varbit(bit varying, internal, smallint, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_value_anyenum(anyenum, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_value_anyenum(anyenum, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_value_anyenum(anyenum, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_value_bit(bit, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_value_bit(bit, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_value_bit(bit, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_value_bool(boolean, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_value_bool(boolean, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_value_bool(boolean, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_value_bpchar(character, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_value_bpchar(character, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_value_bpchar(character, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_value_bytea(bytea, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_value_bytea(bytea, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_value_bytea(bytea, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_value_char("char", internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_value_char("char", internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_value_char("char", internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_value_cidr(cidr, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_value_cidr(cidr, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_value_cidr(cidr, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_value_date(date, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_value_date(date, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_value_date(date, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_value_float4(real, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_value_float4(real, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_value_float4(real, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_value_float8(double precision, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_value_float8(double precision, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_value_float8(double precision, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_value_inet(inet, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_value_inet(inet, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_value_inet(inet, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_value_int2(smallint, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_value_int2(smallint, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_value_int2(smallint, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_value_int4(integer, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_value_int4(integer, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_value_int4(integer, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_value_int8(bigint, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_value_int8(bigint, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_value_int8(bigint, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_value_interval(interval, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_value_interval(interval, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_value_interval(interval, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_value_macaddr(macaddr, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_value_macaddr(macaddr, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_value_macaddr(macaddr, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_value_macaddr8(macaddr8, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_value_macaddr8(macaddr8, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_value_macaddr8(macaddr8, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_value_money(money, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_value_money(money, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_value_money(money, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_value_name(name, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_value_name(name, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_value_name(name, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_value_numeric(numeric, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_value_numeric(numeric, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_value_numeric(numeric, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_value_oid(oid, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_value_oid(oid, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_value_oid(oid, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_value_text(text, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_value_text(text, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_value_text(text, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_value_time(time without time zone, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_value_time(time without time zone, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_value_time(time without time zone, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_value_timestamp(timestamp without time zone, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_value_timestamp(timestamp without time zone, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_value_timestamp(timestamp without time zone, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_value_timestamptz(timestamp with time zone, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_value_timestamptz(timestamp with time zone, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_value_timestamptz(timestamp with time zone, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_value_timetz(time with time zone, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_value_timetz(time with time zone, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_value_timetz(time with time zone, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_value_trgm(text, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_value_trgm(text, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_value_trgm(text, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_value_uuid(uuid, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_value_uuid(uuid, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_value_uuid(uuid, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_extract_value_varbit(bit varying, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_extract_value_varbit(bit varying, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_extract_value_varbit(bit varying, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_numeric_cmp(numeric, numeric); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_numeric_cmp(numeric, numeric) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_numeric_cmp(numeric, numeric) TO genonaut_ro;


--
-- Name: FUNCTION gin_trgm_consistent(internal, smallint, text, integer, internal, internal, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_trgm_consistent(internal, smallint, text, integer, internal, internal, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_trgm_consistent(internal, smallint, text, integer, internal, internal, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gin_trgm_triconsistent(internal, smallint, text, integer, internal, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gin_trgm_triconsistent(internal, smallint, text, integer, internal, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gin_trgm_triconsistent(internal, smallint, text, integer, internal, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gtrgm_compress(internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gtrgm_compress(internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gtrgm_compress(internal) TO genonaut_ro;


--
-- Name: FUNCTION gtrgm_consistent(internal, text, smallint, oid, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gtrgm_consistent(internal, text, smallint, oid, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gtrgm_consistent(internal, text, smallint, oid, internal) TO genonaut_ro;


--
-- Name: FUNCTION gtrgm_decompress(internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gtrgm_decompress(internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gtrgm_decompress(internal) TO genonaut_ro;


--
-- Name: FUNCTION gtrgm_distance(internal, text, smallint, oid, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gtrgm_distance(internal, text, smallint, oid, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gtrgm_distance(internal, text, smallint, oid, internal) TO genonaut_ro;


--
-- Name: FUNCTION gtrgm_options(internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gtrgm_options(internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gtrgm_options(internal) TO genonaut_ro;


--
-- Name: FUNCTION gtrgm_penalty(internal, internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gtrgm_penalty(internal, internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gtrgm_penalty(internal, internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gtrgm_picksplit(internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gtrgm_picksplit(internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gtrgm_picksplit(internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION gtrgm_same(public.gtrgm, public.gtrgm, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gtrgm_same(public.gtrgm, public.gtrgm, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gtrgm_same(public.gtrgm, public.gtrgm, internal) TO genonaut_ro;


--
-- Name: FUNCTION gtrgm_union(internal, internal); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.gtrgm_union(internal, internal) TO genonaut_rw;
GRANT ALL ON FUNCTION public.gtrgm_union(internal, internal) TO genonaut_ro;


--
-- Name: FUNCTION set_limit(real); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.set_limit(real) TO genonaut_rw;
GRANT ALL ON FUNCTION public.set_limit(real) TO genonaut_ro;


--
-- Name: FUNCTION show_limit(); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.show_limit() TO genonaut_rw;
GRANT ALL ON FUNCTION public.show_limit() TO genonaut_ro;


--
-- Name: FUNCTION show_trgm(text); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.show_trgm(text) TO genonaut_rw;
GRANT ALL ON FUNCTION public.show_trgm(text) TO genonaut_ro;


--
-- Name: FUNCTION similarity(text, text); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.similarity(text, text) TO genonaut_rw;
GRANT ALL ON FUNCTION public.similarity(text, text) TO genonaut_ro;


--
-- Name: FUNCTION similarity_dist(text, text); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.similarity_dist(text, text) TO genonaut_rw;
GRANT ALL ON FUNCTION public.similarity_dist(text, text) TO genonaut_ro;


--
-- Name: FUNCTION similarity_op(text, text); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.similarity_op(text, text) TO genonaut_rw;
GRANT ALL ON FUNCTION public.similarity_op(text, text) TO genonaut_ro;


--
-- Name: FUNCTION strict_word_similarity(text, text); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.strict_word_similarity(text, text) TO genonaut_rw;
GRANT ALL ON FUNCTION public.strict_word_similarity(text, text) TO genonaut_ro;


--
-- Name: FUNCTION strict_word_similarity_commutator_op(text, text); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.strict_word_similarity_commutator_op(text, text) TO genonaut_rw;
GRANT ALL ON FUNCTION public.strict_word_similarity_commutator_op(text, text) TO genonaut_ro;


--
-- Name: FUNCTION strict_word_similarity_dist_commutator_op(text, text); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.strict_word_similarity_dist_commutator_op(text, text) TO genonaut_rw;
GRANT ALL ON FUNCTION public.strict_word_similarity_dist_commutator_op(text, text) TO genonaut_ro;


--
-- Name: FUNCTION strict_word_similarity_dist_op(text, text); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.strict_word_similarity_dist_op(text, text) TO genonaut_rw;
GRANT ALL ON FUNCTION public.strict_word_similarity_dist_op(text, text) TO genonaut_ro;


--
-- Name: FUNCTION strict_word_similarity_op(text, text); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.strict_word_similarity_op(text, text) TO genonaut_rw;
GRANT ALL ON FUNCTION public.strict_word_similarity_op(text, text) TO genonaut_ro;


--
-- Name: FUNCTION word_similarity(text, text); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.word_similarity(text, text) TO genonaut_rw;
GRANT ALL ON FUNCTION public.word_similarity(text, text) TO genonaut_ro;


--
-- Name: FUNCTION word_similarity_commutator_op(text, text); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.word_similarity_commutator_op(text, text) TO genonaut_rw;
GRANT ALL ON FUNCTION public.word_similarity_commutator_op(text, text) TO genonaut_ro;


--
-- Name: FUNCTION word_similarity_dist_commutator_op(text, text); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.word_similarity_dist_commutator_op(text, text) TO genonaut_rw;
GRANT ALL ON FUNCTION public.word_similarity_dist_commutator_op(text, text) TO genonaut_ro;


--
-- Name: FUNCTION word_similarity_dist_op(text, text); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.word_similarity_dist_op(text, text) TO genonaut_rw;
GRANT ALL ON FUNCTION public.word_similarity_dist_op(text, text) TO genonaut_ro;


--
-- Name: FUNCTION word_similarity_op(text, text); Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT ALL ON FUNCTION public.word_similarity_op(text, text) TO genonaut_rw;
GRANT ALL ON FUNCTION public.word_similarity_op(text, text) TO genonaut_ro;


--
-- Name: TABLE alembic_version; Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.alembic_version TO genonaut_rw;
GRANT SELECT ON TABLE public.alembic_version TO genonaut_ro;


--
-- Name: TABLE available_models; Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.available_models TO genonaut_rw;
GRANT SELECT ON TABLE public.available_models TO genonaut_ro;


--
-- Name: SEQUENCE available_models_id_seq; Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT USAGE ON SEQUENCE public.available_models_id_seq TO genonaut_rw;
GRANT USAGE ON SEQUENCE public.available_models_id_seq TO genonaut_ro;


--
-- Name: TABLE content_items; Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.content_items TO genonaut_rw;
GRANT SELECT ON TABLE public.content_items TO genonaut_ro;


--
-- Name: TABLE content_items_auto; Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.content_items_auto TO genonaut_rw;
GRANT SELECT ON TABLE public.content_items_auto TO genonaut_ro;


--
-- Name: SEQUENCE content_items_auto_id_seq; Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT USAGE ON SEQUENCE public.content_items_auto_id_seq TO genonaut_rw;
GRANT USAGE ON SEQUENCE public.content_items_auto_id_seq TO genonaut_ro;


--
-- Name: SEQUENCE content_items_id_seq; Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT USAGE ON SEQUENCE public.content_items_id_seq TO genonaut_rw;
GRANT USAGE ON SEQUENCE public.content_items_id_seq TO genonaut_ro;


--
-- Name: TABLE content_tags; Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.content_tags TO genonaut_rw;
GRANT SELECT ON TABLE public.content_tags TO genonaut_ro;


--
-- Name: TABLE flagged_content; Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.flagged_content TO genonaut_rw;
GRANT SELECT ON TABLE public.flagged_content TO genonaut_ro;


--
-- Name: SEQUENCE flagged_content_id_seq; Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT USAGE ON SEQUENCE public.flagged_content_id_seq TO genonaut_rw;
GRANT USAGE ON SEQUENCE public.flagged_content_id_seq TO genonaut_ro;


--
-- Name: TABLE generation_jobs; Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.generation_jobs TO genonaut_rw;
GRANT SELECT ON TABLE public.generation_jobs TO genonaut_ro;


--
-- Name: SEQUENCE generation_jobs_id_seq; Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT USAGE ON SEQUENCE public.generation_jobs_id_seq TO genonaut_rw;
GRANT USAGE ON SEQUENCE public.generation_jobs_id_seq TO genonaut_ro;


--
-- Name: TABLE models_checkpoints; Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.models_checkpoints TO genonaut_rw;
GRANT SELECT ON TABLE public.models_checkpoints TO genonaut_ro;


--
-- Name: TABLE models_loras; Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.models_loras TO genonaut_rw;
GRANT SELECT ON TABLE public.models_loras TO genonaut_ro;


--
-- Name: TABLE recommendations; Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.recommendations TO genonaut_rw;
GRANT SELECT ON TABLE public.recommendations TO genonaut_ro;


--
-- Name: SEQUENCE recommendations_id_seq; Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT USAGE ON SEQUENCE public.recommendations_id_seq TO genonaut_rw;
GRANT USAGE ON SEQUENCE public.recommendations_id_seq TO genonaut_ro;


--
-- Name: TABLE tag_parents; Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.tag_parents TO genonaut_rw;
GRANT SELECT ON TABLE public.tag_parents TO genonaut_ro;


--
-- Name: TABLE tag_ratings; Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.tag_ratings TO genonaut_rw;
GRANT SELECT ON TABLE public.tag_ratings TO genonaut_ro;


--
-- Name: SEQUENCE tag_ratings_id_seq; Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT USAGE ON SEQUENCE public.tag_ratings_id_seq TO genonaut_rw;
GRANT USAGE ON SEQUENCE public.tag_ratings_id_seq TO genonaut_ro;


--
-- Name: TABLE tags; Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.tags TO genonaut_rw;
GRANT SELECT ON TABLE public.tags TO genonaut_ro;


--
-- Name: TABLE user_interactions; Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.user_interactions TO genonaut_rw;
GRANT SELECT ON TABLE public.user_interactions TO genonaut_ro;


--
-- Name: SEQUENCE user_interactions_id_seq; Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT USAGE ON SEQUENCE public.user_interactions_id_seq TO genonaut_rw;
GRANT USAGE ON SEQUENCE public.user_interactions_id_seq TO genonaut_ro;


--
-- Name: TABLE user_notifications; Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.user_notifications TO genonaut_rw;
GRANT SELECT ON TABLE public.user_notifications TO genonaut_ro;


--
-- Name: SEQUENCE user_notifications_id_seq; Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT USAGE ON SEQUENCE public.user_notifications_id_seq TO genonaut_rw;
GRANT USAGE ON SEQUENCE public.user_notifications_id_seq TO genonaut_ro;


--
-- Name: TABLE user_search_history; Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.user_search_history TO genonaut_rw;
GRANT SELECT ON TABLE public.user_search_history TO genonaut_ro;


--
-- Name: SEQUENCE user_search_history_id_seq; Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT USAGE ON SEQUENCE public.user_search_history_id_seq TO genonaut_rw;
GRANT USAGE ON SEQUENCE public.user_search_history_id_seq TO genonaut_ro;


--
-- Name: TABLE users; Type: ACL; Schema: public; Owner: genonaut_admin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.users TO genonaut_rw;
GRANT SELECT ON TABLE public.users TO genonaut_ro;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: public; Owner: genonaut_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE genonaut_admin IN SCHEMA public GRANT USAGE ON SEQUENCES TO genonaut_rw;
ALTER DEFAULT PRIVILEGES FOR ROLE genonaut_admin IN SCHEMA public GRANT USAGE ON SEQUENCES TO genonaut_ro;


--
-- Name: DEFAULT PRIVILEGES FOR FUNCTIONS; Type: DEFAULT ACL; Schema: public; Owner: genonaut_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE genonaut_admin IN SCHEMA public GRANT ALL ON FUNCTIONS TO genonaut_rw;
ALTER DEFAULT PRIVILEGES FOR ROLE genonaut_admin IN SCHEMA public GRANT ALL ON FUNCTIONS TO genonaut_ro;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: genonaut_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE genonaut_admin IN SCHEMA public GRANT SELECT,INSERT,DELETE,UPDATE ON TABLES TO genonaut_rw;
ALTER DEFAULT PRIVILEGES FOR ROLE genonaut_admin IN SCHEMA public GRANT SELECT ON TABLES TO genonaut_ro;


--
-- Name: genonaut_on_create_schema; Type: EVENT TRIGGER; Schema: -; Owner: postgres
--

CREATE EVENT TRIGGER genonaut_on_create_schema ON ddl_command_end
         WHEN TAG IN ('CREATE SCHEMA')
   EXECUTE FUNCTION public.genonaut_apply_privs();


ALTER EVENT TRIGGER genonaut_on_create_schema OWNER TO postgres;

--
-- PostgreSQL database dump complete
--

\unrestrict 1nK1JCLzOqy4Ofdef0NeCQl95nYdh96LmfpY4UVfolTWVPWrxqJhm7Z4TZu67OB

