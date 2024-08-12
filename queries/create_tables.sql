CREATE TABLE IF NOT EXISTS pdl.titles
(
    id          smallint               NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 100 MINVALUE 100 MAXVALUE 1000 CACHE 1 ),
    name        character varying(100) NOT NULL,
    description text,
    CONSTRAINT pk_titles PRIMARY KEY (id),
    CONSTRAINT uc_title_name UNIQUE (name)
)
    WITH (
        OIDS = FALSE
    );


CREATE TABLE IF NOT EXISTS pdl.programs
(
    id          smallint NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 100 MINVALUE 100 MAXVALUE 1000 CACHE 1 ),
    title_id    smallint,
    subtitle_id smallint,
    name        character varying(100),
    CONSTRAINT pk_programs PRIMARY KEY (id)
)
    WITH (
        OIDS = FALSE
    );

CREATE TABLE IF NOT EXISTS pdl.sub_programs
(
    id         smallint NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 100 MINVALUE 100 MAXVALUE 10000 CACHE 1 ),
    program_id smallint NOT NULL,
    name       character varying(100),
    CONSTRAINT pk_sub_programs PRIMARY KEY (id)
)
    WITH (
        OIDS = FALSE
    );

CREATE TABLE IF NOT EXISTS pdl.payments
(
    id                    bigint               NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 100 MINVALUE 100 MAXVALUE 1000000 CACHE 1 ),
    title_id              smallint,
    subtitle_id           smallint,
    program_id            smallint,
    sub_program_id        smallint,
    practice_category_id  smallint,
    state_code            character varying(2) NOT NULL,
    year                  smallint             NOT NULL,
    payment               numeric(14, 2),
    recipient_count       bigint,
    base_acres            numeric(10, 2),
    farm_count            bigint,
    practice_code         character varying(100),
    practice_code_variant character varying(100),
    CONSTRAINT pk_payments PRIMARY KEY (id),
    CONSTRAINT uc_payments UNIQUE (title_id, subtitle_id, program_id, sub_program_id, state_code, year)
)
    WITH (
        OIDS = FALSE
    );

COMMENT ON COLUMN pdl.payments.recipient_count
    IS 'Stores recipient count for programs. Stores count of contracts for CRP.';

-- CREATE UNIQUE INDEX IF NOT EXISTS idx_payments_unique
--     ON pdl.payments (title_id, subtitle_id, program_id, sub_program_id, state_code, year);

CREATE TABLE IF NOT EXISTS pdl.states
(
    code character varying(2)   NOT NULL,
    name character varying(100) NOT NULL,
    CONSTRAINT pk_states PRIMARY KEY (code)
)
    WITH (
        OIDS = FALSE
    );

CREATE TABLE IF NOT EXISTS pdl.subtitles
(
    id       smallint               NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 100 MINVALUE 100 MAXVALUE 1000 ),
    title_id smallint               NOT NULL,
    name     character varying(100) NOT NULL,
    CONSTRAINT pk_subtitles PRIMARY KEY (id)
)
    WITH (
        OIDS = FALSE
    );

CREATE TABLE IF NOT EXISTS pdl.practice_categories
(
    id                    smallint          NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 100 MINVALUE 100 MAXVALUE 1000 ),
    name                  character varying NOT NULL,
    display_name          character varying,
    category_grouping     character varying,
    program_id            smallint          NOT NULL,
    is_statutory_category boolean           NOT NULL,
    PRIMARY KEY (id)
)
    WITH (
        OIDS = FALSE
    );

CREATE TABLE IF NOT EXISTS pdl.practices
(
    code         character varying(100) NOT NULL,
    name         character varying(200) NOT NULL,
    display_name character varying(200),
    source       character varying,
    CONSTRAINT pk_practices PRIMARY KEY (code)
)
    WITH (
        OIDS = FALSE
    );

COMMENT ON TABLE pdl.practices
    IS 'Conservation Practice Standards';

ALTER TABLE IF EXISTS pdl.programs
    ADD CONSTRAINT "fk_ titles_id" FOREIGN KEY (title_id)
        REFERENCES pdl.titles (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
        NOT VALID;


ALTER TABLE IF EXISTS pdl.programs
    ADD CONSTRAINT "fk_ subtitles_id" FOREIGN KEY (subtitle_id)
        REFERENCES pdl.subtitles (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
        NOT VALID;


ALTER TABLE IF EXISTS pdl.sub_programs
    ADD CONSTRAINT fk_programs_id FOREIGN KEY (program_id)
        REFERENCES pdl.programs (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
        NOT VALID;


ALTER TABLE IF EXISTS pdl.payments
    ADD CONSTRAINT fk_programs_id FOREIGN KEY (program_id)
        REFERENCES pdl.programs (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
        NOT VALID;


ALTER TABLE IF EXISTS pdl.payments
    ADD CONSTRAINT fk_sub_programs_id FOREIGN KEY (sub_program_id)
        REFERENCES pdl.sub_programs (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
        NOT VALID;


ALTER TABLE IF EXISTS pdl.payments
    ADD CONSTRAINT fk_states_id FOREIGN KEY (state_code)
        REFERENCES pdl.states (code) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
        NOT VALID;


ALTER TABLE IF EXISTS pdl.payments
    ADD CONSTRAINT fk_titles_id FOREIGN KEY (title_id)
        REFERENCES pdl.titles (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID;


ALTER TABLE IF EXISTS pdl.payments
    ADD CONSTRAINT fk_subtitles_id FOREIGN KEY (subtitle_id)
        REFERENCES pdl.subtitles (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID;


ALTER TABLE IF EXISTS pdl.payments
    ADD CONSTRAINT fk_practice_categories_id FOREIGN KEY (practice_category_id)
        REFERENCES pdl.practice_categories (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID;

ALTER TABLE IF EXISTS pdl.payments
    ADD CONSTRAINT fk_practice_code FOREIGN KEY (practice_code)
        REFERENCES pdl.practices (code) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID;

ALTER TABLE IF EXISTS pdl.subtitles
    ADD CONSTRAINT fk_titles_id FOREIGN KEY (title_id)
        REFERENCES pdl.titles (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
        NOT VALID;


ALTER TABLE IF EXISTS pdl.practice_categories
    ADD CONSTRAINT fk_program_id FOREIGN KEY (program_id)
        REFERENCES pdl.programs (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID;

END;
