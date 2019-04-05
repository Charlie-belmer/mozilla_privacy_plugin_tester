---
--- Primary Key Sequences
---

CREATE SEQUENCE messages_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE plugin_repository_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE test_results_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE urls_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

---
--- Table Creation
---

CREATE TABLE plugin_repository (
    id integer DEFAULT nextval('plugin_repository_id_seq'::regclass) NOT NULL,
    name character varying(512),
    url character varying(512),
    icon_url character varying(512),
    users integer,
    author character varying(512),
    version character varying(64),
    last_plugin_update date,
    xpi_url character varying(512)
);

CREATE TABLE test_messages (
    id integer DEFAULT nextval('messages_seq'::regclass) NOT NULL,
    header text,
    url_id integer NOT NULL,
    body bytea
);

CREATE TABLE test_results (
    plugin integer NOT NULL,
    last_test_date date,
    icon_path character varying(1024),
    id integer DEFAULT nextval('test_results_id_seq'::regclass) NOT NULL
);

CREATE TABLE test_results_urls (
    id integer DEFAULT nextval('urls_seq'::regclass) NOT NULL,
    url character varying(1024) NOT NULL,
    test_id integer NOT NULL
);


---
--- FK and PK constraints
---

ALTER TABLE ONLY plugin_repository
    ADD CONSTRAINT plugin_repository_pkey PRIMARY KEY (id);

ALTER TABLE ONLY test_messages
    ADD CONSTRAINT test_messages_pkey PRIMARY KEY (id);

ALTER TABLE ONLY test_results
    ADD CONSTRAINT test_results_pkey PRIMARY KEY (id);

ALTER TABLE ONLY test_results_urls
    ADD CONSTRAINT test_results_urls_pkey PRIMARY KEY (id);

ALTER TABLE ONLY test_results_urls
    ADD CONSTRAINT test_fk FOREIGN KEY (test_id) REFERENCES test_results(id) ON DELETE CASCADE;

ALTER TABLE ONLY test_messages
    ADD CONSTRAINT url_fk FOREIGN KEY (url_id) REFERENCES test_results_urls(id) ON DELETE CASCADE;
